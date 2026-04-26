## **Deployments using K8s via Secure Promotion** 


![](pipeline-docs/markdown_converted/images/k8s_deployments_via_secure_channel.pdf-0001-01.png)


## **DEPRECATION NOTICE!!!** 

Notice:  The information provided in this document has been deprecated.  The correct way to access K8s with secure promotion is via the 'Kate' application created by the k8s team.  You can find information on the kate app here : https://pages.github.concur.com /kraken/documentation/external/docs/application-developer/ReleasePipeline/1-kate/ 


![](pipeline-docs/markdown_converted/images/k8s_deployments_via_secure_channel.pdf-0001-04.png)


For Onboarding to Secure Promotion from Delivery Pipeline (Buildhub) please refer to the wiki. 

Notice: The information provided in this document has been deprecated. The correct way to access K8s with secure promotion is via the 'Kate' application created by the k8s team. You can find information on the kate app here : https://pages.github.concur.com/kraken/documentation /external/docs/application-developer/Release-Pipeline/1-kate/ 

Architecture Differences Buildhub Model Secure Promotion Model Building Container Images Control Logic Workflows Uploading Container Image Promoting Container images to Production Registry Scan and Promote Deploying Using K8s Control Logic Cluster Name and Kubeconf Context Configuration Namespace Deployment Examples 

Users of Deploy Pipeline (Buildhub) can use Secure Promotion (Release Pipeline + Supply-chain CLI) to deploy their applications to Kraken AWS Clusters and Kraken Colo Clusters. 

## Architecture Differences 

## **Buildhub Model** 

**Buildhub** uses workflow created by container hosting team to deploy applications using Kubernetes. 

## **Secure Promotion Model** 

**Secure Promotion** uses Release Pipeline to build the docker image. It uses Supply-chain CLI to scan and promote the docker image to production registry. This is the docker registry, which the Kubernetes cluster pull container images from. 

## Building Container Images 

## **Control Logic** 

Build logic is still driven from a config file, but instead of a pipelines.yml file (a Concur-specific invention), Release Pipeline relies on a Buildspec.yml file (an AWS invention). Because the buildspec is an AWS offering, most questions about the buildspec.yml can be answered with an internet search. 

## **Workflows** 

The Release Pipeline does not have workflows. Workflows were developed as an abstraction layer between common build-tool commands and the Jenkins domain-specific language. This was done in order to reduce overhead and ramp-up time with new users. 

With the buildspec.yml, users can use the same commands that they would execute on their command line to build and test. Because of this, there is no need for workflows. User's can refer to AWS's documentation for using docker commands in buildspec files for building their containers. 

## **Uploading Container Image** 

User's are required to upload the container image build in the previous step to Quay. Service credentials for quay repository can be stored in AWS's Param eter Store, and retrieved at build-time to login to quay. User can use docker push command to upload the registry to quay. 

## Promoting Container images to Production Registry 

## **Scan and Promote** 

Container images which are deployed to production environments are required to be scanned before promotion to production registry. Users can use Secure Promotion/Supply-chain CLI dockerimages endpoint to scan and promote container images to production registry. 

The Supply-chain CLI tool to make authenticating and calling the endpoints easier. 

## Deploying Using K8s 

## **Control Logic** 

Just as control logic for the Build account is configured in the Buildspec.yml, control logic for the Deploy accounts is stored in a Deployspec.yml. The Deployspec.yml works just like a buildspec would, but is named differently for convenience. 

The Buildspec.yml file is only used by the Build account, and the Deploy accounts only look at the Deployspec.yml. 

## **Cluster Name and Kubeconf** 

Container hosting team deploys Kraken clusters to AWS environments. Clusters are deployed to various accounts in a production environment. Users can use their Kraken AWS Cluster Names document to find the name of the cluster in the target account where the service is needed to be deployed to. 

Once user knows the name of the cluster, the next step is to retrieve the kubeconfig file for that cluster. kubeconfig files are stored in an s3 bucket in the target account the  service is needed to deploy to. The name of the s3 bucket is kraken-<target-account-number>-<aws-region>. 

## **Context Configuration** 

Users can use their own custom docker container in the deployspec, which has helm installed already to run the helm commands or Helm can be installed from the installers available in the artifactory. Once helm is installed, then next step is to retrieve the kubeconfig file from the s3 bucket and store it in the . kube folder. Please refer to the example below to see these steps in deployspec file. 

Set the contect to current: kubectl config set-context --current --namespace <your-namespace> 

## **Namespace** 

Container Hosting team provisions namespaces. Users are required to create a JIRA item for getting a namespace provisioned for their service. Please refer to Container Hosting Team's documentation for more details on Namespace creation and quota limits. 

## **Deployment** 

Once the above steps are completed, users can use their choice of helm/kubectl commands to deploy their service to the target Kraken Cluster. 

## Examples 

For an example of building, promoting and deploying k8s applications through the Secure Promotion, please see our Examples Repository 

