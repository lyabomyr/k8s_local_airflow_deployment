
# Airflow Kubernetes local deployment 

_for local airflow deploy to k8s need to:_

> * start docker engine `for execute docker engine on mac: brew install docker docker-compose colima; colima start --cpu 8 --memory 10 --disk 100;`

> * start script `bash start_local_env.sh`

> * after comleted k8s helm deploy for open airflow need to made port-forwarding

> * execute `kubectl -n airflow get pods` - get webserver pod name;

> port forward webserver: 
`kubectl -n airflow port-forward airflow-webserver-{pod name from previous step}  8083:8080` or use Lens for port forwarding

> For open webserver `localhost:8083` ```login: admin | password: admin```

> For stop airflow need to execute `bash stop_local_env.sh`

Note:

    - we need logs directory here for claiming logs in airflow
    - In kind-cluster.yaml file we determinate patch to root directory: hostPath: ../ with objects as "dags, plugins, requirements.txt" this folders will be mouned to dags folder inside airflow images
    - In dags_volume.yaml and logs_volume.yaml located volumns for logs and dags directory
    - In value.yaml located airflow deployment confifurations: execution type/ dags_folder/plugins_folder/ logs and dags clime configurations/  airflow version...
    - Also for insert variables you can add variables and apply variables.yaml or upload json with variables to UI
