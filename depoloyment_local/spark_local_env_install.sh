helm repo add spark-operator https://kubeflow.github.io/spark-operator

helm install spark spark-operator/spark-operator --namespace airflow  --set sparkJobNamespace=airflow  --set webhook.enable=true;
kubectl create serviceaccount spark --namespace=airflow;
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=airflow:spark --namespace=airflow;
kubectl apply -f access_airflow_to_spark.yaml;
kubectl apply -f access_event_wath_airflow.yaml;
kubectl apply -f spark_role.yaml;
