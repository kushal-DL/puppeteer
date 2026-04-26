## **Github Action Runners - Linux** 

Prerequisites Executing Workflows On RPL Runners rpl-linux-runners rpl-ghas-linux-runners RPL Self hosted Runner Onboarding Access to AWS resources in central AWS account role-to-assume Actions Runner Controller (ARC) Architecture How it works Autoscaling Advantages of using RPL runners 

RPL Old Runners vs New General Purpose Runners vs GHAS Runners RPL Windows Runners 

GHAS scans on Windows runners How to migrate to New general purpose/GHAS Runners from from Old Runners Limitations 

Troubleshooting FAQs 

Does RPL provide new auto scalable runners for Windows? Do CodeQL scans done on Windows runners send scan results to the Attestation Database? What will happen if I do not migrate to new runners if I am performing CodeQL scans? Why is my build stuck waiting for RPL provisioned self-hosted runners to pickup a job? 

## Prerequisites 

If you do not already have linux runners, you must onboard your GitHub Enterprise organization 

. 

## Executing Workflows On RPL Runners 


![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0001-10.png)


**----- Start of picture text -----**<br>
Labels Example<br>rpl-linux-runners<br>build.yaml<br>Main Label to execute<br>your workflow on RPL  name: Build<br>managed linux runners<br>on: [push]<br>jobs:<br>  build:<br>         name: Build<br>        runs-on: rpl-linux-runners<br>    steps:<br>      - uses: actions/checkout@v4<br>        ...<br>Actions available to GitHub Enterprise can be found here.<br>Do not use General Purpose runners for GHAS scans. The General Purpose runners are only set up for CI/CD.<br>PROMOTIONS WILL BE BLOCKED IF GENERAL PURPOSE RUNNERS ARE USED FOR GHAS SCANS.<br>THE SCAN RESULTS WILL NOT BE REPORTED TO THE ATTESTATION DATABASE.<br>**----- End of picture text -----**<br>


**rpl-ghas-linuxcodeql.yaml runners** Label to use if you are `name: "CodeQL Workflow"` running GitHub Advanced Security (GHAS) CodeQL `on: [push]` scans `# This block is mandatory concurrency: group: ${{ github.workflow }}-${{ github.ref }} cancel-in-progress: true jobs: ghas-scan: runs-on: rpl-ghas-linux-runners steps: - name: Checkout repository uses: actions/checkout@v4 - name: Add more steps to set up and run CodeQL ...` 


![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0002-01.png)


See the official GitHub starter workflow here for more configuration examples: https://github.com/actions/starterworkflows/blob/main/code-scanning/codeql.yml 


![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0002-03.png)


## **Mandatory Concurrency Setting** 

Please note: The default behavior of GitHub Actions is to allow multiple jobs or workflow runs to run concurrently. With CodeQL scans, this behavior can cause collisions that result in inaccurate scan findings getting reported to the attestation database. This makes the concurrency block mandatory for proper reporting of CodeQL scans. `concurrency: group: ${{ github.workflow }}-${{ github.ref }} cancel-in-progress: true` Note that this means that when multiple commits to the same branch trigger concurrent CodeQL scans, **only the most recent commit** on the branch will have a completed scan with attestations written for it. 

## RPL Self hosted Runner Onboarding 

The process for setting up Release Pipeline self hosted runners is a one-step, self-serve process: users need to **install Release Pipeline GitHub app** 

. 


![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0002-09.png)


## **Install for only select repositories** 

When installing the app, you will see "All repositories" and "Only select repositories" as options. **You must select repositories individually from the "Only select repositories" option** in order for the rpl-runner role for your repository to be created. Usability of general purpose runners is limited without this role. 


![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0002-12.png)


## **Initial setup when the app is already installed** 

If the Release Pipeline GitHub app is already installed on a repo that you want to onboard with these runners, you need to reinstall the app once to perform an initial setup. Do this by removing the repo from the selection, hitting save, selecting the repo again, and saving. 

## **Update Release Pipeline GitHub app Permissions:** 

If Release Pipeline GitHub app is already installed, users will see "Release Pipeline is requesting an update to its permissions" when they reinstall the app. The owners of the GitHub org need to accept new permissions. 


![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0003-00.png)



![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0003-01.png)



![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0004-00.png)


Release Pipeline provides three sets of runners when RPL GitHub app is installed. 

- **GHAS Runners** : These are specialized runners which should only be used to perform CodeQL scans. These runners are specially configured to send CodeQL scan findings to RPL's Attestation Database. 

- **General Purpose Runners** : These runners are CI/CD runners. They can be used for general purpose tasks such as linting, building artifacts and initiating deployments (using RPL's Supply Chain tool). 

- **ARM64 Runners** : These runners are just like the General Purpose Runners, except that they use hardware with the ARM64 architecture, instead of x86_64 

On initial setup, Release Pipeline provisions two warmed up runners each for GHAS and general purpose builds respectively. After that, the runners autoscale based on GitHub workflow executions. 

Once the RPL GitHub app is installed, users can verify creation of RPL runners by going to https://github.concur.com/organizations/{user's-org-name} /settings/actions/runners?qr=level:Organization 

**Example:** Below example shows RPL runners attached to a GitHub organization 


![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0005-00.png)


**Actions Runner Controller (ARC) for Runners** is responsible for autoscaling the runners when new workflow execution requests come in. 

In order to use RPL runners in a GitHub workflow, users need to specify the **Actions Runner Controller name** as the value for the `runs-on` key in their workflow file. 

## **Labels do not work with ARC based self hosted runners** 

## Access to AWS resources in central AWS account 

In order to access AWS resources in GIF (central build) account, users will need to use configure-aws-credentials GitHub action. 

Example: 

```
- name: Configure aws credentials
  uses: actions/configure-aws-credentials@v4
  with:
         role-to-assume: arn:aws:iam::966799970081:role/rpl-runner-{GitHub-Org}-{GitHub-Repo}-role
    aws-region: us-west-2
```

## **role-to-assume** 

When RPL GitHub app is installed on a repo, in order to onboard to RPL self-hosted runners, RPL automation creates an IAM role for the repo. The name of the role is **rpl-runner-{GitHub-Org}-{GitHub-Repo}-role** . This role has scoped down permission for AWS secret manager and AWS parameter store, in addition to other IAM permissions. Users should use this role if their workflow needs to access AWS resources in the central build account (GIF account). 

## Actions Runner Controller (ARC) 

ARC is a Kubernetes operator that orchestrates and scales self-hosted runners for GitHub Actions. ARC creates runner scale sets that automatically scale based on the number of workflows running in your repository or organization. These runners are **ephemeral** and based on containers, meaning new runner containers can scale up or down rapidly and cleanly. 

## Architecture 

A simple ARC runner setup consist of: 

- **Controller-manager pod** : This is the master pod which contains resources (created out of the box when this pod is deployed) that control all aspects of ARC operations. **Runner ScaleSet Listener pod** : This pod is responsible for scaling up and down runners. **Secret** : A kubernetes secret is an object that contains a small amount of sensitive data such as a password, a token, or a key. In ARC setup  it contains the authentication token. **Runner Pod(s)** : These are ephemeral pods that execute the workflow. Each pod gets destroyed at the end of execution. Every workflow execution gets a fresh runner pod. 


![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0006-02.png)


## How it works 

The following diagram illustrates the architecture of ARC's autoscaling runner scaleset mode. For a detailed step by step API call sequence and order of operation, please refer to official GitHub documentation. 


![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0007-00.png)


## Autoscaling 

Release Pipeline provides two warmed up runners (each for GHAS and general purpose builds respectively) per GitHub organization when a user installs the RPL GitHub app. As jobs are triggered for the repos under a given org, RPL runners provision a new runner for every job automatically. Once a job is finished, the runner is destroyed. 

## Advantages of using RPL runners 

RPL runners provide autoscaling out of the box. No additional setup is needed Users do not have to create and provide a Personal Access Token (PAT) to the RPL team anymore. Onboarding is simplified and self serve. 

Runners are ephemeral. Every execution gets their own container. Containers are destroyed after the execution is done. 

## RPL Old Runners vs New General Purpose Runners vs GHAS Runners 


![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0007-07.png)


**----- Start of picture text -----**<br>
Old Runners New GP Runners GHAS Runners<br>Auto-scalable No Yes Yes<br>Number of Runners per GitHub Org 10 No upper limit No upper limit<br>PAT creation required by the users Yes No No<br>Ephemeral Containers No Yes Yes<br>Send data to Attestation Database No No Yes<br>Manual steps needed from RPL team to onboard Yes No No<br>Docker in Docker (DinD) supported No Yes Yes<br>**----- End of picture text -----**<br>


## RPL Windows Runners 

Unfortunately, Windows runners are currently not supported with the Actions Runner Controller. Users will need to keep using the old Windows runners for CI/CD and GHAS scans on Windows projects. 

## **GHAS scans on Windows runners** 

Users can perform GHAS scans for Windows on the existing RPL-provided Windows runners. They will need to uninstall and reinstall the RPL GitHub app once to enable sending their scan results to the Attestation Database. After that, they can use a standard CodeQL workflow file with the runs-on key referencing the old <org>-rpl-windows-runner label. 


![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0008-00.png)


Make sure to uninstall and reinstall the RPL GitHub app on your repos in order to enable Windows runners to send scan results to the Attestation Database. This is a one-time setup operation. 

Windows GHAS scans use the same workflow configuration as for Linux, with the exception of the runs-on value as noted. See the GHAS Runners section of this document for an example workflow, including the mandatory `concurrency` block that must be present. 

## How to migrate to New general purpose/GHAS Runners from from Old Runners 

Migrating to the new autoscaling runners from the old RPL-managed runners is a two-step process: 

1.  Onboard through the Release Pipeline GitHub app 

2.  Set up a workflow file to use the runners with the appropriate `runs-on` key for your use case 


![](pipeline-docs/markdown_converted/images/github_action_runners_linux.pdf-0008-07.png)


The new Kubernetes autoscalable runners are not one to one replacement of the old runners. The new runners are ephemeral docker containers, who share underlying hardware of Kubernetes cluster nodes, so these runner containers **do not run in privileged mode** . This means that your workflows, which worked with old runners, might not work with the new runners without modification(s). 

## Limitations 

Kubernetes-based autoscalable runners are provided for Linux OS only. This model does not support Windows runners for now. Limitations imposed by GitHub can be found in GitHub documentation 

## Troubleshooting 

Please reach out to the #ask-release-pipeline slack channel for any issues with RPL self hosted runners 

## FAQs 

## **Does RPL provide new auto scalable runners for Windows?** 

Unfortunately no. ARC based auto scalable runners are not supported for Windows OS. Users should keep using the old Windows runners until further notice. 

## **Do CodeQL scans done on Windows runners send scan results to the Attestation Database?** 

Yes, but in order to enable the scan results to be sent to attestation database, users need to uninstall and reinstall RPL GitHub app once. 

## **What will happen if I do not migrate to new runners if I am performing CodeQL scans?** 

Your scan results will not shipped to the Attestation Database. In the future we will enable blocking based on CodeQL scan results. Your deployments will be blocked at that time. 

## **Why is my build stuck waiting for RPL provisioned self-hosted runners to pickup a job?** 

Resolution: https://wiki.one.int.sap/wiki/x/kWXlww 

