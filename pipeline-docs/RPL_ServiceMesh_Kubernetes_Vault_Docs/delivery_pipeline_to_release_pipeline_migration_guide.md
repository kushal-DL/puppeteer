## **Delivery Pipeline (Buildhub) to Release Pipeline Onboarding and Migration Guide** 


![](pipeline-docs/markdown_converted/images/3286591291_8acecb0839cf474b8d3f11f798c89382-140326-1616-586.pdf-0001-01.png)


## **TLDR** 

Too many words and you just want to onboard your repo?  Getting Started with Release Pipeline (RPL) 

Architecture Differences Buildhub Model Release Pipeline Model Building Control Logic Workflows Uploading Build Artifacts Securely Promoting Build Artifacts Deploying Control Logic Synching Files Examples 

RPL + Secure Promotion and Delivery Pipeline serve similar functions, but operate very differently. This guide was written to help new users translate their Delivery Pipeline jobs to the new service. 

For steps on how to onboard your repo to Release Pipeline, please view the Getting Started page. 

## Architecture Differences 

Release Pipeline is built off of AWS-native services. Code is compiled and deployed with AWS Codebuild, rather than Jenkins. 

In the Delivery Pipeline, build logic and deploy logic take place on separate _hubs_ . There is a Deploy Hub in each supported environment that is responsible for deploying infrastructure in that domain. These environments are open, meaning that any team can have access to them. 

In Release Pipeline, build logic and deploy logic execute in separate AWS _accounts_ , known as the Build account and the Deploy accounts, respectively. Just like how a Deploy Hub runs commands to update infrastructure in a _target environment_ , Release Pipeline's deploy account will update infrastructure in a **user's target account** . This target account is owned and administered by the user's team, and access to that account is limited to that team. The Secure Promotion is a special case, and its access is limited to creating/updating infrastructure. The pipeline team does not have access to the user's target accounts. 

Secure Promotion Release Pipeline's method of ensuring build artifacts meet security compliance policies before being allowed into production environments. If the requirements are not met, then the artifact will not be promoted to production. 

## **Buildhub Model** 

**Buildhub** creates artifacts and uploads to cloud storage **Deploy Hub** pulls down artifacts, and then creates/updates infrastructure in target environment (AWSQA, Colo, etc) 

## **Release Pipeline Model** 

**Build Account** Codebuild creates artifacts and uploads to cloud storage **Secure Promotion** runs compliance checks and promotes the artifacts to the Deploy accounts if they meet requirements **Deploy Account** Codebuild pulls down artifacts and then creates/updates infrastructure in **user's target account** (team-owned account in Fabian , team-owned account in US2, etc) 

## Building 

## **Control Logic** 

Build/deploy logic is still driven from a config file, but instead of a pipelines.yml file (a Concur-specific invention), Release Pipeline relies on a Buildspec.yml file (an AWS invention). Because the buildspec is an AWS offering, most questions about the buildspec.yml can be answered with an internet search. 

## **Workflows** 

The Release Pipeline does not have workflows. Workflows were developed as an abstraction layer between common build-tool commands and the Jenkins domain-specific language. This was done in order to reduce overhead and ramp-up time with new users. 

With the buildspec.yml, users can use the same commands that they would execute on their command line to build and test. Because of this, there is no need for workflows. 

## **Uploading Build Artifacts** 

With Secure Promotion, methods of uploading to Quay, Artifactory, etc. are determined by the user. Service credentials can be stored in AWS's Parameter Store, and retrieved at build-time to construct an HTTP request against the desired service. 

## **Securely Promoting Build Artifacts** 

Once artifacts are in place, they need to be shared with the Deploy Account. This can be accomplished with the Supply-Chain CLI. The Supply-Chain CLI is part of what makes Secure Promotion so secure. In addition to promoting files and docker images to where they need to be, the Supply-Chain CLI also runs compliance checks, documents the results, and tracks these artifacts for auditing and security compliance. 

## Deploying 

## **Control Logic** 

Just as control logic for the Build account is configured in the Buildspec.yml, control logic for the Deploy accounts is stored in a Deployspec.yml. The Deployspec.yml works just like a buildspec would, but is named differently for convenience. 

The Buildspec.yml file is only used by the Build account, and the Deploy accounts only look at the Deployspec.yml. 

## **Synching Files** 

The Delivery Pipeline's workflows ensured that all of the necessary files made it to the deploy hub in order for the deployment to take place. The Secure Promotion takes a similar approach using the Supply-chain CLI's zip endpoint. 

In the Buildspec.yml, users can archive all of the files necessary for deployment, and then call the zip endpoint to send that archive to the relevant Deploy accounts. In the Deploy accounts, all of the files that have been zipped and sent over will be available in the deployer Codebuild's workspace. This means that the files can be referenced in the Deployspec.yml just as they would be referenced in the Buildspec. 

## Examples 

For an example of building and deploying through the Secure Promotion, please see our Examples Repository 

