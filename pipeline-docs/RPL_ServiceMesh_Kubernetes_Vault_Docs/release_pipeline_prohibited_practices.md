## **Release Pipeline - Prohibited Practices** 

The purpose of this page is to highlight and identify specific use cases that the RPL team deems to be out of scope of our tooling. 

_**Do not register a single Github repository to two APRs.**_ Currently the RPL tooling doesn't allow two sets of infrastructure for the same Github repo.  If you require deployments to multiple accounts that are not covered in the existing APR's , please submit a request in the #ask-release-pipeline channel for a new APR that meets your needs. 

## _**Do not use wildcard permissions.**_ 

SAP completed an audit on RPL and stated that we are not allowed to use wildcard permissions. The reason for this restriction is that secure role design, account management, provisioning and deprovisioning of support and administrative accounts prevents unauthorized access to a system. 

In the following scenario, each specific entry that is required would need to be listed:ex: ec2:createEC2, ec2:assignroletype, etc, in order to adhere to the least-privilege model. 


![](pipeline-docs/markdown_converted/images/release_pipeline_prohibited_practices.pdf-0001-06.png)


Note: For the implementation on March 14, 2023, where we are preventing wildcards from being used, we are **not** going to go through and invalidate existing roles with policies that contain noncompliant wildcards. Your existing deployer roles will stay the same. We are changing our Pipeline tooling to enforce the new requirements going forward. That means new repos being added to an APR will need to be compliant, and existing repos will not be able to be updated through their APR unless their deploy policy is compliant. 

