Vault in Kubernetes - Kubernetes @ SAP Concur 

3/14/26, 9:53 PM 

## Vault in Kubernetes 

## Working with Vault in Kubernetes 

This step-by-step guide will walk you trough the whole process of how to: 

Add your vault.yaml to the Namespaces repo 

Get a Vault Token From Inside a Container 

Work with Vault secrets 

## DISCLAIMER 

Container Ecosystem team doesn't own Vault, it is used in sidecar containers specifically to manage authentication. For issues such as 'invalid role name,' 'service account name not authorized,' 'permission denied,' etc., please review your Vault configuration and reach out to #ask-consulvault for support. 

## Getting a Vault Token From Inside a Container 

In order for these next steps to work, your container must have curl  available. At runtime of the container, execute the steps within a script to initialize your container. 

For each cluster, you'll need to know the name of the cluster in order to authenticate against the correct Vault Kubernetes auth backend. The cluster name is not available by default so you'll need to take action to obtain the name. 

PodPresets  vs ConfigMaps 

The PodPresets  feature has been removed in Kubernetes v1.20 so you will not find it in EKS and Colo clusters. 

Get cluster name by using PodPreset (Kubernetes <v1.20) 

https://pages.github.concur.com/kraken/documentation/external/docs/application-developer/Vault/vault_k8_auth/ 

1/5 

Vault in Kubernetes - Kubernetes @ SAP Concur 

3/14/26, 9:53 PM 

Each namespace will have a PodPreset resource available so that the required Vault data can be populated in your pod environment. To utilize the PodPreset, add the label vault-init: "true"  to your Deployment definition. 

vault-init  PodPreset example --apiVersion: extensions/v1beta1 kind: Deployment metadata: name: myapp namespace: foobar spec: replicas: 3 selector: matchLabels: app: myapp template: metadata: labels: app: myapp vault-init: "true" spec: containers: - name: myapp image: quay.cnqr.delivery/foobar/myapp:1.0.0 ports: - containerPort: 3000 

Once your pod is deployed, you should see environmental variables CLUSTER_NAME  and VAULT_SERVER  populated in your container. 

## Get cluster name by using kraken-env  configmap (EKS clusters and Kubernetes >v1.20) 

In the newest versions of kubernetes Vault auth works the same as in older generation of Kraken. There is one exception where newest versions don't support PodPresets. 

A ConfigMap kraken-env  is available for every namespace for developers to reference in their containers. In order for Vault login to work properly you must load environment variables from kraken-env  ConfigMap. 

You can either use the example below or add global.eks = true  to your helm chart values, more information is on Service Mesh Wiki 

https://pages.github.concur.com/kraken/documentation/external/docs/application-developer/Vault/vault_k8_auth/ 

2/5 

Vault in Kubernetes - Kubernetes @ SAP Concur 

3/14/26, 9:53 PM 

kraken-env  ConfigMap Example apiVersion: apps/v1 kind: Deployment metadata: name: myapp namespace: foobar spec: replicas: 3 selector: matchLabels: app: myapp template: metadata: labels: app: myapp spec: containers: - name: myapp image: quay.cnqr.delivery/foobar/myapp:1.0.0 ports: - containerPort: 3000 envFrom: - configMapRef: name: kraken-env 

Your container will start with environmental variables CLUSTER_NAME  and VAULT_SERVER . 

## Get Vault token 

This curl  call will return a response that will contain the Vault token (client_token). 

The command returning the namespace  value below, returns your Kubernetes namespace. However, the parameter in the call to Vault requires the Vault role name  of the role you are trying to login as. The following example will only work if your K8s namespace matches the Vault role name. If they do not match, then replace the namespace function below with your vault role name . 

curl -k -X POST -d "{\"role\": \"$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)\",\"jwt\": \"$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)\"}" https://$VAULT_SERVER/v1/{full-namespace-path}/auth/kraken/{kraken-clustername}/login 

Next set this token value in your environment as VAULT_TOKEN . 

https://pages.github.concur.com/kraken/documentation/external/docs/application-developer/Vault/vault_k8_auth/ 

3/5 

Vault in Kubernetes - Kubernetes @ SAP Concur 

3/14/26, 9:53 PM 

export VAULT_TOKEN=<client_token> 

## Working with Vault secrets 

Vault secrets are available accross all AWS accounts and Kubernetes clusters within that jurisdiction. For example if you write a secret from within a travel  account, it would also be available in spend  account. 

Kubernetes method of Vault authentication has it's own secrets backend located at 

https://$VAULT_SERVER/v1/secret/kraken/private/... 

https://$VAULT_SERVER/v1/secret/kraken/public/... 

## POST 

In the following example, we will write secret foo  with value bar . 

## POST Example 

curl -k -X POST --header "X-Vault-Token: $VAULT_TOKEN" https://$VAULT_SERVER/v1/secret/kraken/private/$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)/foo -d '{"value": "bar"}' 

For example, if we run this from foobar  Kubernetes namespace, we will create a secret foo  in 

https://$VAULT_SERVER/v1/secret/kraken/private/foobar/foo . 

## GET 

In the following example, we will read secret foo . 

## GET Example 

curl -k -X GET --header "X-Vault-Token: $VAULT_TOKEN" https://$VAULT_SERVER/v1/secret/kraken/private/$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)/foo` 

For example, if we run this from foobar  Kubernetes namespace, we will read a secret foo  from 

https://$VAULT_SERVER/v1/secret/kraken/private/foobar/foo . 

https://pages.github.concur.com/kraken/documentation/external/docs/application-developer/Vault/vault_k8_auth/ 

4/5 

Vault in Kubernetes - Kubernetes @ SAP Concur 

3/14/26, 9:53 PM 

## Debugging 

Check if Vault is working locally: 

curl -k -d "{\"role\": \"$NAMESPACE\", \"jwt\": \"$(kubectl describe secret $(kubectl describe serviceaccount default -n $NAMESPACE | grep Tokens: | awk '{print $2}') -n $NAMESPACE | grep token: | awk '{print $2}')\"}" https://$VAULT_SERVER/v1/auth/kraken-$CLUSTER_NAME/login 

Source: https://github.concur.com/kraken/kraken2vault 

https://pages.github.concur.com/kraken/documentation/external/docs/application-developer/Vault/vault_k8_auth/ 

5/5 

