Overview - Kubernetes @ SAP Concur 

3/14/26, 9:53 PM 

## Overview 

Vault Kubernetes auth backend allows developers to use Kubernetes namespace service accounts to authenticate to Vault and retrieve a Vault token. This is done by enabling the Kubernetes auth backend on the Vault cluster, then configuring the new backend with the Kubernetes cluster data that will allow communication between Vault and that specific Kubernetes cluster. Then on startup of a Kubernetes pod, it can make a curl  request to the authentication endpoint provided using the namespace service account's token, which is located in 

/var/run/secrets/kubernetes.io/serviceaccount/token . Vault will receive this request with the service account token and ask the Kubernetes cluster if it is a valid token for the role. If it's valid, Vault will return the Pod a response that contains a Vault token. 


![](pipeline-docs/markdown_converted/images/kubernetes_sap_concur_overview.pdf-0001-05.png)


Each team will need to add a vault.yaml  file to their namespace repo before being able to use this auth backend. More details on the requirements can be found here: https://github.concur.com/namespaces/demo 

Source: https://github.concur.com/kraken/kraken2vault 

https://pages.github.concur.com/kraken/documentation/external/docs/application-developer/Vault/overview/ 

1/2 

