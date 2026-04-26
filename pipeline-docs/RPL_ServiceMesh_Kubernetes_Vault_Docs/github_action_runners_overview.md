## **GitHub Action Runners** 

## Overview 

Release Pipeline provides GitHub action self hosted runners on demand. These runners are provisioned at the GitHub organization level, meaning that they are connected to an org, and will run workflows for all the repositories under that org. These runners are container pods inside an EKS cluster, and will autoscale as new workflow executions are triggered. A runner pod is assigned to every workflow execution and is destroyed afterward, to ensure that each workflow runs in a clean workspace. 

The following video briefly summarizes the instructions in this document to onboard and start using these runners for GHAS scans and general purpose CI. 

Github Action Runners - Linux Github Action Runners - Windows 

