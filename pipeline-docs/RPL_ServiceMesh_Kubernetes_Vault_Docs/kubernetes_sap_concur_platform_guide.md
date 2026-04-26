Kubernetes @ SAP Concur 

3/14/26, 9:54 PM 


![](pipeline-docs/markdown_converted/images/kubernetes_sap_concur_platform_guide.pdf-0001-02.png)


## Container Ecosystem 

Welcome to the Container Ecosystem's team documentation portal! 

The Container Ecosystem is an assembly of tools and services to assist with the deployment and operations of your container-based workloads. 

Central to the ecosystem is the Kubernetes control plane which provides a robust API to which you can submit declarative manifests describing your application stack and dependent infrastructure primitives. Kubernetes controllers then jump into action to orchestrate the provisioning of your components, ensuring that the desired state matches the current state. 

Additionally, our team provides: 

- The Platform (Kubernetes Addons and configuration, Sysdig monitoring) 

- The Lifecycle (KATE, Image Promotion, Kube-S3-Applier) 

- The Compliance (Sysdig Secure, Anchore) 

## Are you new to Kubernetes? 

Kubernetes is a portable, extensible, open source platform for managing containerized workloads and services. It enables declarative configuration and automation, and has a large, rapidly growing 

https://pages.github.concur.com/kraken/documentation/external/docs/ 

1/4 

Kubernetes @ SAP Concur 

3/14/26, 9:54 PM 

ecosystem. Kubernetes services, support, and tools are widely available. The adoption of Kubernetes accelerated with the shift from monolithic architectures to microservices. 

## What are the advantages of Kubernetes? 

- Service discovery & load balancing: Exposes containers via DNS or IP, and distributes traffic for stability. 

- Storage orchestration: Automatically mounts storage from local or cloud providers. 

- Automated rollouts & rollbacks: Manages container updates and state changes safely. 

- Automatic bin packing: Efficiently schedules containers based on resource requirements. 

- Self-healing: Restarts, replaces, or kills containers based on health checks. 

- Secret & config management: Securely stores and manages sensitive data and app configs. 

- Batch execution: Handles batch and CI workloads, replacing failed containers as needed. 

- Horizontal scaling: Easily scale apps up or down manually or automatically. 

- IPv4/IPv6 dual-stack: Supports both IPv4 and IPv6 addresses for Pods and Services. 

- Extensibility: Add features to clusters without modifying upstream code. 

Read more about Kubernetes here: https://kubernetes.io/docs/concepts/overview/what-iskubernetes/ 

## Goal 

The main goal of the Container Ecosystem is to simplify and reduce the burden of end-to-end (E2E) teams working to meet their service maturity goals. 

## What can tenants do to maximize the performance & reduce the risk of incindents (i.e. P1s) 

- Follow the best practices: some of the pratices we recommend are required especially considering the fact that if not in place they will cause incidents during certain maintenance (i.e. node rotation). 

- Read the documentation: This is among the most complete docs you can find and provides solutions to most issues you can find and detailed guides on how to deploy and troubleshoot. 

- When asking something in #ask-k8s don't forget to: 

Tell us which cluster you are talking about. 

https://pages.github.concur.com/kraken/documentation/external/docs/ 

2/4 

Kubernetes @ SAP Concur 

3/14/26, 9:54 PM 

What's your namespace? 

   - What's your service's name? 

   - Do you have any logs? post them! 

   - is there something you changed recently that you reckon might have caused the issue? Let us know! 

   - Search the channel history! There's nothing new under the sun, chances are that other people had the same issue you had and finding the ways they have been supported in the past could support you now. 

- After experiencing an incident like a P1, you should make sure you align the changes that resolve the issue in all other environments where you have the same exact configuration, especially if that configuration is identified as the culprit for the incident. 

## How would a good request in #ask-k8s look like? 


![](pipeline-docs/markdown_converted/images/kubernetes_sap_concur_platform_guide.pdf-0003-09.png)


In this example you can see that the user provided all the above mentioned information and also read the documentation and searched the channel history, and we have a clear snapshot of the error from the logs. 

## Useful Links 

The main Developer Documentation 

Notification Slack Channel 

https://pages.github.concur.com/kraken/documentation/external/docs/ 

3/4 

Kubernetes @ SAP Concur 

3/14/26, 9:54 PM 

- The Main Kubernetes Support Slack Channel 

- Accessing EKS Clusters 

- Accessing Colo Clusters 

- How to Deploy to Kubernetes @SAP Concur 

- Kubernetes Best Practices 

- Tuning Requests and Limits 

- GitHub Checks Troubleshooting 

- Sysdig Access 

Source: https://github.concur.com/kraken/documentation 

https://pages.github.concur.com/kraken/documentation/external/docs/ 

4/4 

