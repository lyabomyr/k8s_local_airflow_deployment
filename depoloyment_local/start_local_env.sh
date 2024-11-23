brew install helm  kubectl yq ;
#set airflow dag folder
export LOCAL_DAGS_FOLDER=../
 check location  ls -a $LOCAL_DAGS_FOLDER

yq -i "
.nodes[1].extraMounts[1].hostPath = \"$LOCAL_DAGS_FOLDER\" |
.nodes[1].extraMounts[1].containerPath = \"/tmp/dags\"  |
.nodes[2].extraMounts[1].hostPath = \"$LOCAL_DAGS_FOLDER\" |
.nodes[2].extraMounts[1].containerPath = \"/tmp/dags\"  |
.nodes[3].extraMounts[1].hostPath = \"$LOCAL_DAGS_FOLDER\" |
.nodes[3].extraMounts[1].containerPath = \"/tmp/dags\"
" kind-cluster.yaml
## CREATE KUBE CLUSTER
#brew install docker docker-compose colima;
colima start --cpu 10 --memory 16 --disk 100;
#colima start --arch x86_64 --cpu 4 --memory 8 --disk 100

#Create the kind cluster
kind create cluster --name airflow-cluster --config kind-cluster.yaml

# create airflow namespace
kubectl create namespace airflow;

# creates a Kubernetes secret webserver-secret-key and generate used python code
kubectl -n airflow create secret generic my-webserver-secret --from-literal="webserver-secret-key=$(python3 -c 'import secrets; print(secrets.token_hex(16))')";

# Create the PersistentVolume and PersistentVolumeClaim for setup the Kubernetes resources which allow such a connection
kubectl apply -f dags_volume.yaml;
kubectl apply -f logs_volume.yaml;

## FETCH LATEST HELM CHART VERSION AND INSTALL AIRFLOW
helm repo add apache-airflow https://airflow.apache.org
helm repo update
helm search repo airflow
helm install airflow apache-airflow/airflow --namespace airflow --debug -f values.yaml --version 1.12.0

# Important config located in values.yaml





