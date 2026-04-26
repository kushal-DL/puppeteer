## **Deployment Environments - Release Pipeline** 

Release Pipeline is a pipeline tool that enables users to deploy to various production and integration environments. 

Users will have to make use of supply-chain CLI to deploy to supported environments - using supply-chain CLI. 

## **Supported Environments** 


![](pipeline-docs/markdown_converted/images/release_pipeline_deployment_environments.pdf-0001-04.png)


The supported environments of this table have a 1to1 relation with the files defined under the APR .plz folder; meaning that any _**new files created**_ under the .plz folder won't be taken into account. 


![](pipeline-docs/markdown_converted/images/release_pipeline_deployment_environments.pdf-0001-06.png)


**----- Start of picture text -----**<br>
Environment Key Supported In which case should we use it?<br>Integration Environment integration To deploy to integration accounts<br>Fabian USA fabian-us To deploy to fabian-us accounts<br>Fabian EMEA fabian-emea To deploy to fabian-emea accounts<br>CCPS ccps To deploy to ccps accounts<br>US2 us2 To deploy to us2 accounts<br>EU2 eu2 To deploy to eu2 accounts<br>China* china To deploy to China target account (542931487864)<br>APJ1 (Japan) apj1 To deploy to apj1 (Japan) accounts<br>CCPS us-pscc Deprecated: use 'ccps' instead  To deploy to ccps accounts<br>Fabian USA fabian Deprecated: use 'fabian-us'  To deploy to fabian-us accounts<br>GS1 gs1<br>**----- End of picture text -----**<br>



![](pipeline-docs/markdown_converted/images/release_pipeline_deployment_environments.pdf-0001-07.png)


## **More information for China** 

RPL automation is supported in China 

Unlike other environments, China deployment supports only one target account (542931487864) Deployer code build projects are created in China deploy account (432486609652) 


![](pipeline-docs/markdown_converted/images/release_pipeline_deployment_environments.pdf-0001-11.png)


## **China Zip Deployments** 

In China environment, zip files will no longer be synced to `446304402574` account, as before. RPL automation now promotes the zip files to China deploy account (432486609652) 

