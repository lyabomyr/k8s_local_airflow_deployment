from airflow import DAG
from datetime import timedelta, datetime
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import (
    SparkKubernetesOperator,
)
from airflow.providers.cncf.kubernetes.sensors.spark_kubernetes import (
    SparkKubernetesSensor,
)

default_args = {
    "owner": "clover",
    "retries": 3,
    "start_date": datetime(2024, 1, 13),
}

# Define your main application file and image
SPARK_APPLICATION_FILE = "local:///opt/spark/work-dir/test_job2.py"
SPARK_IMAGE = "lyabomyr/spark-image:latest"
K8S_NAMESPACE = "airflow"

with DAG(
    "spark-example_2",
    default_args=default_args,
    description="simple dag",
    start_date=datetime(2022, 11, 17),
    catchup=False,
    tags=["example"],
) as dag:
    # template_spec we can put to json if will use this approach
    submit = SparkKubernetesOperator(
        task_id="spark-job-template",
        in_cluster=True,
        image=SPARK_IMAGE,
        code_path=SPARK_APPLICATION_FILE,
        template_spec={
            "spark": {
                "apiVersion": "sparkoperator.k8s.io/v1beta2",
                "version": "v1beta2",
                "kind": "SparkApplication",
                "apiGroup": "sparkoperator.k8s.io",
                "metadata": {"namespace": K8S_NAMESPACE},
                "spec": {
                    "type": "Python",
                    "pythonVersion": "3",
                    "mode": "cluster",
                    "sparkVersion": "3.1.1",
                    "successfulRunHistoryLimit": 1,
                    "restartPolicy": {"type": "Never"},
                    "imagePullPolicy": "Always",
                    "hadoopConf": {},
                    "imagePullSecrets": [],
                    "dynamicAllocation": {
                        "enabled": False,
                        "initialExecutors": 1,
                        "minExecutors": 1,
                        "maxExecutors": 4,
                    },
                    "labels": {"version": "3.1.1"},
                    "driver": {
                        "serviceAccount": "spark",
                        "cores": 1,
                        "coreLimit": "1200m",
                        "instances": 1,
                        "container_resources": {
                            "gpu": {"name": None, "quantity": 2},
                            "cpu": {"request": 1, "limit": 2},
                            "memory": {"request": "2Gi", "limit": "10Gi"},
                        },
                    },
                    "executor": {
                        "cores": 1,
                        "instances": 1,
                        "container_resources": {
                            "gpu": {"name": None, "quantity": 1},
                            "cpu": {"request": 2, "limit": 5},
                            "memory": {"request": "2Gi", "limit": "10Gi"},
                        },
                    },
                },
            },
            "kubernetes": {
                "env_vars": [],
                "env_from": [],
                "image_pull_secrets": [],
                "node_selector": {},
                "affinity": {
                    "nodeAffinity": {},
                    "podAffinity": {},
                    "podAntiAffinity": {},
                },
                "tolerations": [
                    {
                        "key": "node-role.kubernetes.io/control-plane",
                        "operator": "Exists",
                        "effect": "NoSchedule",
                    }
                ],
                "config_map_mounts": {},
                "volume_mounts": [{"name": "config", "mountPath": "/tmp/logs/"}],
                "volumes": [
                    {
                        "name": "config",
                        "persistentVolumeClaim": {"claimName": "airflow-logs"},
                    }
                ],
                "from_env_config_map": [],
                "from_env_secret": [],
                "in_cluster": True,
                "conn_id": "kubernetes_default",
                "kube_config_file": None,
                "cluster_context": None,
            },
        },
        namespace=K8S_NAMESPACE,
        get_logs=True,
        dag=dag,
    )

    submit
