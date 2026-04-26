## **Getting Started with Release Pipeline (RPL)** 

## Introduction 

This document shows the steps needed to onboard and get started using Release Pipeline 

1. Identify your Application Permissions Repository (APR) What is an Application Permissions Repository? Where is my Application Permission Repository? 

2. Register your Code Repository to your Application Permissions Repository 3. Install Release Pipeline GitHub App in your GitHub repository 

4. Add Build and Deploy Spec Files to your Code Repository Continuous Integration - buildspec.yml Continuous Deployment - deployspec.yml 

5. Onboarding Private Repositories 

6. Next Steps SAST Scans Logs 

Troubleshooting and Support 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0001-08.png)


## **Use GitHub Action Runners For Building Artifacts/Continuous Integration(CI) instead of buildspec.yml** 

We recommend using GitHub Actions(GHA) Runners for new projects, and recommend users migrate to GHA for Building artifacts at their convenience. Still continue to use deployspec.yml and Deployer CodeBuilds for deploying into environments. 

Linux Runners Onboarding 

Windows Runners Onboarding 

## 1. Identify your Application Permissions Repository (APR) 

Your organization's APR is a critical component that manages your projects' permissions and infrastructure. 

## What is an Application Permissions Repository? 

An Application Permissions Repository creates CI/CD infrastructure for every code repository registered to it. 

It creates: 

Build and deploy CodeBuild projects IAM policies and roles for deploy accounts 

The IAM resources created are defined per project by users when the code repository is registered to the APR. 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0002-00.png)


## **How APRs get Updated** 

By default, APRs run a build on **every commit** to any branch. This means that every commit will update the build infrastructure and certain deployment infrastructure according to the branch committed to: 

Commits made to the APR's **master branch** will update deploy infrastructure in **every environment defined in the APR's .plz folder** Commits made to **any other branch** will update deploy infrastructure in **only the Integration** environment 

See also: What is an Application Permissions Repository(APR)? 

## Where is my Application Permission Repository? 

Application Permissions repos can be found at https://github.concur.com/plz/<account name>, where <account name> refers to APR account name like spend, travel, tools etc. 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0002-07.png)


## **BEFORE REQUESTING NEW APR** 

We recommend searching throughout the PLZ Github Org to see if there are existing APRs that make use of the same ATM environments. 

You will need to be added as a member to get write access to your respective APR. Please request APR membership: 

1.  In the #ask-release-pipeline Slack channel, click the _attachments & shortcuts_ plus sign blocked URL under the message box 2.  Choose the "Request APR Membership" action 

3.  Select your APR from the drop down menus "Which Application Permissions Repo (APR)?" and list the GitHub usernames to be added 4.  Submit your request 

If your organization does not have an APR, please create a new APR request: 

1.  In the #ask-release-pipeline Slack channel, click the _attachments & shortcuts_ plus sign under the message box 2.  Choose the "Ask a Question" action 3.  In the summary box, write "New APR Request - <NAME-OF-APR>" 4.  Submit your request 

This list should look familiar because there is a 1-1 correlation between your Application Permissions Repository and your AWS account. 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0002-16.png)


**----- Start of picture text -----**<br>
Name APR Link<br>bi https://github.concur.com/plz/bi<br>central-architecture https://github.concur.com/plz/central-architecture<br>compleat https://github.concur.com/plz/compleat<br>data https://github.concur.com/plz/data<br>deploy https://github.concur.com/plz/atm-deploy<br>dmz https://github.concur.com/plz/dmz<br>front https://github.concur.com/plz/atm-frontend<br>host https://github.concur.com/plz/host<br>imaging https://github.concur.com/plz/imaging<br>mobile https://github.concur.com/plz/mobile<br>observe https://github.concur.com/plz/observe<br>pci https://github.concur.com/plz/pci<br>pubsub https://github.concur.com/plz/pubsub<br>qe https://github.concur.com/plz/qe/<br>receipt https://github.concur.com/plz/receipt<br>report https://github.concur.com/plz/report<br>sec https://github.concur.com/plz/sec<br>**----- End of picture text -----**<br>


spend https://github.concur.com/plz/spend t2 https://github.concur.com/plz/t2 tools https://github.concur.com/plz/tools travel https://github.concur.com/plz/travel tripit https://github.concur.com/plz/tripit usersvcs https://github.concur.com/plz/usersvcs 

## 2. Register your Code Repository to your Application Permissions Repository 

For every GitHub repository that you want to use with RPL, there must be a corresponding configuration file in your APR's approved-repos folder. 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0003-03.png)


## **Important Security Note** 

Due to RPL's blocking strategy, APR owners will have to ensure that the .checkmarx/cxone.config file is present at the root of the org. You can use the following example as a template for your file - here 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0003-06.png)


## **Case Sensitive** 

Github Org and Repo name are case sensitive. Please make sure the casing in the APR matches with the actual casing of your org repo name. 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0003-09.png)


## **Reminder** 

The approved-repos under an APR are not limited to a single GitHub Organization. For example: https://github.concur.com/plz/tools can have approved repository definitions from https://github.concur.com/my-org 

1.  Create a new branch off of the desired Application Permissions Repository. 2.  On your branch, under the approved-repos folder, add or update your approved-repos.yaml configuration file. a.  example: plz/application-permissions-template/approved-repos/[github repo name].yaml 

3.  Open a pull request for your team lead to review. a.  note: The RPL team does not own your APR. Code reviews and pull requests are the responsibility of your team lead. 

4.  Once merged, your APR's CodeBuild project will update your pipeline and permissions, enabling capabilities granted by the APR owner as specified in the pull request. 

5.  Remove your branch after it has been merged for good hygiene. 

If you would like to view the status of your APR change, login to the build account: https://codebuild.cnqr.delivery/ and go to the Codebuild > Build Projects. 

You are now able to search for your APR build using your plz repo name: 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0004-00.png)


Example pull request 

Example Application Permissions Repo 

## 3. Install Release Pipeline GitHub App in your GitHub repository 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0004-04.png)


## **Does RPL app already exist at org. level?** 

**Before** installing the app, please check your org level settings to see if the RPL app already exists. If it does, skip this step (3) and work with an org admin to activate it for your repository. 

Install the RPL Github App to the repo that you want to onboard. Installing this app establishes the hooks between your code repo. and AWS CodeBuild. 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0004-08.png)


In order to install the GitHub app, you must be an Owner, Admin or GitHub App Manager in the organization that you want to onboard. 

If you are **not** an admin/owner and request the installation of RPL Github app to you repo., an email will be received by the admin of your org. who will need to <Accept> the app installation request. 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0004-11.png)


- Due to an existing issue being investigated with webhooks, we highly recommend completing the previous step to register your repository with your APR before continuing with this step. 

Doing these steps out of order is possible, but you will likely need to uninstall and reinstall the RPL GitHub app after registering to update your CodeBuild webhooks. 

1.  Go to the RPL Github App page. 2.  Click the _Configure_ button on the right. 3.  Select the organization that your code repo is in. 

4.  Under _repository access_ , select your repository from the _select repositories_ dropdown menu. There may be other repositories already listed, indicating that the app is installed for those repositories already. 

- a.  Note: We recommend installing the GitHub app on an individual repository basis rather than for all repositories in the organization. This is because installation must happen after the APR registration step, and org-level installation would install the app prematurely. 

- 5.  Click _save_ to confirm installation of the app. 

## 4. Add Build and Deploy Spec Files to your Code Repository 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0005-00.png)


## **New Method to Building with RPL - Github Actions** 

We would strongly suggest new repositories use GitHub Action runners for building their projects Github Action Runners - Linux 

There are two config files that define the commands that your project executes: buildspec and deployspec. These are yaml configuration files that are specific to AWS CodeBuild projects. They follow a standard defined and documented by AWS. 

## Continuous Integration - buildspec.yml 

The buildspec runs in the Release Pipeline Build account. The purpose of the buildspec is to define **what** and **how** you are building. It is responsible for testing code, building artifacts, and sending artifacts to be deployed. 

Steps in the buildspec include (but are not limited to): 

Compiling code Running tests Pushing artifacts to external locations (Artifactory, Quay, Amazon ECR, etc.) Pulling and executing artifacts from external sources 

Promoting artifacts to deployment environments using the supply-chain cli 

## **Configuring buildspec** 

You can find a basic buildspec example here. 

## Continuous Deployment - deployspec.yml 

The deployspec runs in the Deploy account in all target environments specified during promotion. It is responsible for deploying build artifacts and infrastructure into a users Target account. 

Steps in the deployspec may include: 

Assuming the deployer IAM Role associated with the Target account ( **required** ) Pulling down Docker images and deploying them to a kraken namespace in the Target account Running CloudFormation templates to create infrastructure in the Target account 

## **Configuring deployspec.yml** 

The deployspec file follows the same yaml syntax as of buildspec.yml. The steps followed in deployspec are highly dependent on what you want to do with your build artifact. In some cases, (e.g., building and uploading to Artifactory), all your logic can be taken care of in your buildspec. In this case, you may not need a deployspec at all. 

You will need to use the supply-chain CLI in your buildspec.yml. You can find the supply-chain CLI here 

You can view more examples of how a deployment is triggered in our  knowledge base article. 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0005-19.png)


You can find the supported Deployment Environments here 

Every AWS command that needs to be executed in a target account MUST assume the deploy role from the target account 

The Deploy Role name follows the pattern **deployer-<GitOrg>-<GitRepo>-role** in every target account. 

## **Example deployspec command** 

```
            aws cloudformation describe-stack --role arn:aws:iam::556718446970:role/service-role/deployer-
notification-kube-tools-role
```


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0005-25.png)


## **Examples** 

For more examples, navigate to our examples repository. 


![](pipeline-docs/markdown_converted/images/3286591277_174f5d4b28df4237957890f9e24e9a46-140326-1616-584.pdf-0006-00.png)


## **File location** 

The default location of buildspec and deployspec is at the root of your code repo. 

Optionally, you can configure your repository to look for buildspec and deployspec in a separate hidden folder in your repository. See: Am I able to Place Release Pipeline Files In a Hidden Directory? 

## 5. Onboarding Private Repositories 

If your repository is a private repository, _**ensure that the**_ _**`sa-rpl` user has access to your repo**_ 

The sa-rpl GitHub user is responsible for pulling information about Pull Requests. It uses that information to determine if a PR has enough reviewers, and if so, will allow a deployment to production. 

If sa-rpl does not have access to this information (because the repo is set to private), then it cannot determine if a PR has had enough reviewers and will block the deployment by default. 

## 6. Next Steps 

## SAST Scans 

Company policy states that code needs to have evidence of a clean SAST scan prior to deploying to production environments 

RPL's secure promotion provides static code analysis via integration with GPS. 

Learn how to enable supported SonarQube, Mend, Checkmarx and CxOne Scanning _**here**_ . 

## Logs 

For more detailed information on your builds and deployments, please see: Viewing your CodeBuild Logs 

## Troubleshooting and Support 

Information about troubleshooting and support can be found **here** 

