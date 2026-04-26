## **Release Pipeline Best Practices** 

Running into issues with production deployments? Follow the best practices below to ensure you can successfully deploy to production every time. 

## GitHub Actions 

Use Github Actions for your builds Using Supply Chain Actions (only possible with GitHub Actions) GitHub's Security Hardening best practices for Github Actions Repository Configuration Repository names should be lowercase-kebab-style Ensuring only one SAST scanning tool is enabled per repo Application Permissions Repositories(APRs) Wildcards Reference the APR templates for more details on all the available configuration options 

## GitHub Actions 

## **Use Github Actions for your builds** 

Using GitHub Actions instead of AWS CodeBuild for your CI or building your artifacts will decrease wait times, allow for retrying builds (and individual steps) in a workflow, and it removes the need to sign into the AWS Build Account to check build logs. 

## **Using Supply Chain Actions (only possible with GitHub Actions)** 

Supply Chain CLI is the best way to manage the software supply chain and establish a chain of custody for artifacts. Click here to get started. 

Ensure you are on the latest supply chain version. Always use the RPL supported Github Actions for easy and fast promotions rather then setting up your actions 

## **GitHub's Security Hardening best practices for Github Actions** 

Please read GitHub's best practices for security hardening. 

Summary (TL;DR) 

You should **ALWAYS** : 

Restrict the `GITHUB_TOKEN` 's permissions Use credentials that are minimally scoped Check the source-code of third-party actions and how it uses secrets Pin third-party actions to a full length commit SHA and use OSPO Renovate to manage them _(or at least use a Tag)_ 

If any concepts mentioned here are unfamiliar to you, please read GitHub's Understanding GitHub Actions documentation. 

Internal SAP guide is located here External Github guide is located here 

## Repository Configuration 

## **Repository names should be lowercase-kebab-style** 

A good naming convention for GitHub repositories includes using all lowercase letters, separating words with hyphens, and ensuring the name is descriptive and specific to the project's purpose. This helps with organization, clarity, and makes it easier for others to understand the content of the repository at a glance. 

## **Ensuring only one SAST scanning tool is enabled per repo** 

Every promotion is dependent on SAST scans completing so ensure you are following the best practices below for a smooth experience: 

To successfully deploy to production, ensure you have properly setup your SAST scanning with either Cx one or GHAS. 

For faster and smoother deployments, only enable the scanning tool needed If using GHAS, ensure your scans are running using our dedicated 'rpl-ghas-linux-runners'. Thes e are specialized runners which should only be used to perform CodeQL scans. These runners are specially configured to send CodeQL scan findings to RPL's Attestation Database 

## Application Permissions Repositories(APRs) 

## **Wildcards** 

**Reference the APR templates for more details on all the available configuration options** 

