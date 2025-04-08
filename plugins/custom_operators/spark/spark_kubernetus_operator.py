from __future__ import annotations
import datetime
from functools import cached_property
from typing import TYPE_CHECKING, Sequence
from kubernetes.client import ApiException
from kubernetes.watch import Watch
from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.providers.cncf.kubernetes.hooks.kubernetes import (
    KubernetesHook,
    _load_body_to_dict,
)
import json

if TYPE_CHECKING:
    from kubernetes.client.models import CoreV1EventList

    from airflow.utils.context import Context

import uuid


class SparkKubernetesOperator(BaseOperator):
    def __init__(
        self,
        *,
        spec_job_template_file: str,
        namespace: str,
        kubernetes_conn_id: str = "kubernetes_default",
        api_group: str = "sparkoperator.k8s.io",
        api_version: str = "v1beta2",
        in_cluster: bool | None = None,
        cluster_context: str | None = None,
        watch: bool = True,
        image: str,
        main_application_path: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        try:
            path_to_templates = (
                "/opt/airflow/dags/repo/plugins/custom_operators/spark/templates/"
            )
            json_file_path = path_to_templates + spec_job_template_file
            with open(json_file_path, "r") as json_file:
                self.application_file = json.load(json_file)
                self.application_file["metadata"]["namespace"] = namespace
                self.application_file["metadata"][
                    "name"
                ] = f"{self.task_id[:13]}-{str(uuid.uuid4())}-task".lower().replace(
                    "_", "-"
                )
                self.application_file["spec"][
                    "mainApplicationFile"
                ] = main_application_path
                self.application_file["spec"]["image"] = image
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Config file '{spec_job_template_file}' not found."
            )
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in '{spec_job_template_file}'.")

        self.namespace = namespace
        self.kubernetes_conn_id = kubernetes_conn_id
        self.api_group = api_group
        self.api_version = api_version
        self.plural = "sparkapplications"
        self.in_cluster = in_cluster
        self.cluster_context = cluster_context
        self.watch = watch

    @cached_property
    def hook(self) -> KubernetesHook:
        return KubernetesHook(
            conn_id=self.kubernetes_conn_id,
            in_cluster=self.in_cluster,
            config_file=None,
            cluster_context=self.cluster_context,
        )

    def _get_namespace_event_stream(self, namespace, query_kwargs=None):
        try:
            return Watch().stream(
                self.hook.core_v1_client.list_namespaced_event,
                namespace=namespace,
                watch=True,
                **(query_kwargs or {}),
            )
        except ApiException as e:
            if e.status == 410:  # Resource version is too old
                events: CoreV1EventList = (
                    self.hook.core_v1_client.list_namespaced_event(
                        namespace=namespace, watch=False
                    )
                )
                resource_version = events.metadata.resource_version
                query_kwargs["resource_version"] = resource_version
                return self._get_namespace_event_stream(namespace, query_kwargs)
            else:
                raise

    def execute(self, context: Context):
        if isinstance(self.application_file, str):
            body = _load_body_to_dict(self.application_file)
        else:
            body = self.application_file
        name = body["metadata"]["name"]
        namespace = self.namespace or self.hook.get_namespace()

        response = None
        is_job_created = False
        if self.watch:
            try:
                namespace_event_stream = self._get_namespace_event_stream(
                    namespace=namespace,
                    query_kwargs={
                        "field_selector": f"involvedObject.kind=SparkApplication,involvedObject.name={name}"
                    },
                )

                response = self.hook.create_custom_object(
                    group=self.api_group,
                    version=self.api_version,
                    plural=self.plural,
                    body=body,
                    namespace=namespace,
                )
                is_job_created = True
                for event in namespace_event_stream:
                    obj = event["object"]
                    if event["object"].last_timestamp >= datetime.datetime.strptime(
                        response["metadata"]["creationTimestamp"], "%Y-%m-%dT%H:%M:%S%z"
                    ):
                        self.log.info(obj.message)
                        if obj.reason == "SparkDriverRunning":
                            pod_log_stream = Watch().stream(
                                self.hook.core_v1_client.read_namespaced_pod_log,
                                name=f"{name}-driver",
                                namespace=namespace,
                                timestamps=True,
                            )
                            for line in pod_log_stream:
                                self.log.info(line)
                        elif obj.reason in [
                            "SparkApplicationSubmissionFailed",
                            "SparkApplicationFailed",
                            "SparkApplicationDeleted",
                        ]:
                            is_job_created = False
                            raise AirflowException(obj.message)
                        elif obj.reason == "SparkApplicationCompleted":
                            break
                        else:
                            continue
            except Exception:
                if is_job_created:
                    self.on_kill()
                raise

        else:
            response = self.hook.create_custom_object(
                group=self.api_group,
                version=self.api_version,
                plural=self.plural,
                body=body,
                namespace=namespace,
            )

        return response

    def on_kill(self) -> None:
        if isinstance(self.application_file, str):
            body = _load_body_to_dict(self.application_file)
        else:
            body = self.application_file
        name = body["metadata"]["name"]
        namespace = self.namespace or self.hook.get_namespace()
        self.hook.delete_custom_object(
            group=self.api_group,
            version=self.api_version,
            plural=self.plural,
            namespace=namespace,
            name=name,
        )
