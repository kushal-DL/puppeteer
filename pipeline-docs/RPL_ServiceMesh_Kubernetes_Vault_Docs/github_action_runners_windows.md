## **Github Action Runners - Windows** 

Release Pipeline team provides _**self-hosted**_ windows github action runners for teams on request. This enables users of Release Pipeline to perform windows based builds. 

Prerequisites Executing Workflows On RPL Runners rpl-managed-windows-runner rpl-windows-scanner 

FAQs 

How do I request a windows runner for my GitHub organization? How Do I Run Sonarqube and Mend Scans on Windows? How many runners does RPL team create per GitHub Organization? Is RPL's Supply Chain Tool supported on windows runner? 

## Prerequisites 

If you do not already have windows runners, you must request them. 

## Executing Workflows On RPL Runners 

Labels Example **rpl-managed-windows-runner workflow.yaml** Main Label to Use `name: Windows Build on: [push] jobs: windows-build: runs-on: [self-hosted, Windows, X64, rplmanaged-windows-runner] name: Test steps: - uses: actions/checkout@v4` **rpl-windows-scanner workflow.yaml** Label to use if you want automatic Mend and SonarQube scans to execute before the workflow `name: Start a Scan with Sonarqube and Mend on: [push] jobs: windows-build: runs-on: [self-hosted, Windows, X64, rplwindows-scanner] name: Test steps: - uses: actions/checkout@v4` 

<org>-rpl-windows-runner 

Legacy, was previously the only label available and was used for both running scans and executing workflows 

Deprecated: 07 Oct 2024 

**workflow.yaml** `name: Windows Build on: [push] jobs: windows-build: runs-on: [self-hosted, Windows, X64, <org>rpl-windows-runner] name: Test steps: - uses: actions/checkout@v4` 

## FAQs 

## **How do I request a windows runner for my GitHub organization?** 

1.  Create a Github Technical User 

a. Follow github team's guide to create a Github Technical User, if you do not have one already. 


![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0002-08.png)


## **Pro Tip** 

Although github team's documentation mentions using a DL, but use personal email address (SAP email) when creating the technical user. DL seem to work as of now. 


![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0002-11.png)


## **Unique email** 

Use unique email address: If your email has already been used to create a technical user and you want to create another user, then add emai `xt>` ` to your email address to make it unique. For example: If pankaj.sharma@sap.com does not work then use pankaj.sharma+Token@sap.com (add `+Token` )would work if you get an err using your email address 

2. Add the Github Technical User to your github organization as Owner 

Go to `People` section of your github organization and add the above created technical user as `Owner` to your org. 


![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0002-16.png)


## **Permissions** 

If the technical user is not added to your github org as owner then Release Pipeline team's automation to create windows runners will fail. 

Example: https://github.concur.com/orgs/<ORG-NAME>/people 

3. Login to Github using the technical user 

Once you create the technical user successfully, you will receive an email to create a password for that user. 

Login to https://github.concur.com using the technical user and above created password. 

Generate PAT for the technical user 


![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0003-00.png)


## **PAT** 

Please create personal access token (PAT) for the technical user and not github actions runner token. 

Once you are logged in using the technical user, go to your github **Settings** page. Navigate to **Developer Settings Personal Access Token** . Click on **new token** . 


![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0003-04.png)


1.  Provide a text for **Note** field for the new personal access token a.  Set the expiration to " **No expiration** " b.  Check **admin:org** settings and click **Generate Token** . 


![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0003-06.png)



![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0003-07.png)


**Configuration** Please make sure that you make the above two config selections 

- Store the PAT in a secrets storing too 1.  Follow the steps listed here to store the PAT in AWS Secret Manager, AWS Parameter Store or Thycotic 

Submit an onboarding request with RPL team via slack 

From #ask-release-pipeline slack channel, use the lightning bolt ad select **Request GH Window Runner** 


![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0004-01.png)


1. Fill the form. Provide your github org name and the name of the token generated in the previous step (please do not provide the PAT itself) and th 


![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0005-01.png)


1. Release Pipeline team will create self hosted windows runners for your org and notify you. 

Once the runner is configured, you can find it under **Runners Group** >> **Default** RPL Managed machines have the following name `rpl-windows-<hostname>-<org>-#` 

## **How Do I Run Sonarqube and Mend Scans on Windows?** 

Utilize this label: rpl-windows-scanner 

## **How many runners does RPL team create per GitHub Organization?** 


![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0006-00.png)


**----- Start of picture text -----**<br>
Release Pipeline Provides Per GitHub Organization<br>Count Label<br>10 rpl-managed-windows-runner<br>10 rpl-windows-scanner<br>**----- End of picture text -----**<br>


## **Is RPL's Supply Chain Tool supported on windows runner?** 

**Yes** , supply-chain tool come pre installed on RPL provisioned self-hosted runner. 

**Example** : https://github.concur.com/ktg/windows-github-actions-example/blob/main/.github/workflows/windows_build.yml 

1.  Yes, RPL provisioned Windows action runners comes with docker per-configured. 

## **Docker** 

1.  RPL provisioned self-hosted windows runners come pre-installed with Supply Chain tool. 2.  You can build your docker image, as part of your build 3.  Use Supply Chain CLI's docker promote to deploy your docker images 

## **K8's** 

1.  RPL provisioned self-hosted windows runners come pre-installed with Supply Chain tool. 2.  Use Kate app to deploy to your cluster 

https://pages.github.concur.com/kraken/documentation/external/docs/application-developer/Release-Pipeline/ 

## Cloudformation 

1.  Onboard your code repository with Release Pipeline APR. This will provision a deployer-codebuild project in production environments. 2.  RPL provisioned self-hosted windows runners come pre-installed with Supply Chain tool. 3.  Use Supply Chain CLI's promote zipfile feature to trigger your deployments in deployer code build project. 

## **Storing Secrets** 

1.  AWS secrets manager is the FedRamp approved secret storage 2.  Access RPL build AWS account (AWS GIF account) using https://codebuild.cnqr.delivery/ (select your org from the dropdown) 3.  You will have access to store secrets in AWS secret manager at a defined path only: /<yout-org>/secret 


![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0006-14.png)


## **VPN** 

You need to be on non-prod vpn to access the above URL 

## **Retrieving Secrets** 

1.  You can retrieve the secrets (/<your-org>/secret) in your action workflow yaml 


![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0006-19.png)


You can only access your org level secrets 


![](pipeline-docs/markdown_converted/images/github_action_runners_windows.pdf-0006-21.png)


Users are not granted privileges to RDP into the runner instance. 

