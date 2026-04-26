## **How to get access...** 

US-comm2 - Elastic Cloud (US2 data) 

ATM PSCC ATM Integration ATM EU2 ATM APJ1 DR's (AMSDR) 

Instances of LoggingService (might) have a different way of authentication setup. This page will describe all of those which require some attention in order to access Kibana/REST APIs of particular instances. 

Information on this page is updated with process changes, so should be always up-to-date. 

## US-comm2 - Elastic Cloud (US2 data) 

service-now request for OKTA group membership: 


![](logging_docs/markdown_converted/images/3286770993_65ded73675b246c881a5126387ba197c-310326-2158-7556.pdf-0001-07.png)


**----- Start of picture text -----**<br>
Service Account  Environment Group  Group Name Network Connection  NOTE:<br>type Type Prerequisite<br>us-comm2 User  US2 OKTA US2- Be connected one of  click on the  LoggingService-US Comm icon in cnqr.<br>Account LoggingService- these VPNs: okta.com to view the app<br>(Application &  Users<br>Akamai data) SAP VPN<br>SAP Office<br>us-comm2 (Audit  US2- Concur Production<br>data) LoggingService- VPN<br>Audit AWS US2<br>**----- End of picture text -----**<br>


## ATM PSCC 

service-now request for OKTA group membership: 


![](logging_docs/markdown_converted/images/3286770993_65ded73675b246c881a5126387ba197c-310326-2158-7556.pdf-0001-10.png)


**----- Start of picture text -----**<br>
Service Account type Environment Group Type Group Name Network Connection Prerequisite<br>Logging User Account USPSCC OKTA USPSCC_LoggingService_Users Concur US Public Sector VPN<br>(Application & Akamai data)<br>Audit USPSCC-LoggingService-Audit<br>**----- End of picture text -----**<br>


## ATM Integration 

service-now request for OKTA group membership: 


![](logging_docs/markdown_converted/images/3286770993_65ded73675b246c881a5126387ba197c-310326-2158-7556.pdf-0001-13.png)


**----- Start of picture text -----**<br>
Service Account  Environment Group  Group Name Network Connection<br>type Type Prerequisite<br>Logging User Account Integration OKTA Integration-LoggingService-Users Concur AWS Integration VPN<br>(Application & Akamai  birthright -  everyone with an account in cnqr-nonprod<br>data) OKTA get access<br>Audit Integration-LoggingService-Audit<br>**----- End of picture text -----**<br>


## ATM EU2 

service-now request for OKTA group membership: 


![](logging_docs/markdown_converted/images/3286770993_65ded73675b246c881a5126387ba197c-310326-2158-7556.pdf-0001-16.png)


**----- Start of picture text -----**<br>
Service Account  Environment Group  Group  Network  Note<br>type Type Name Connection<br>Prerequisite<br>**----- End of picture text -----**<br>



![](logging_docs/markdown_converted/images/3286770993_65ded73675b246c881a5126387ba197c-310326-2158-7556.pdf-0002-00.png)


**----- Start of picture text -----**<br>
EU- User  EU2 OKTA EU2- NOTE:  Once you have  "LoggingService-EU" access via the cnqr.okta.com,<br>comm2 Account LoggingS Concur  you need to add https://access-eu2.concursolutions.com/ to use kibana on<br>ervice- AWS EU2 EU2, (you connect to the VPN on EU2 and click on the LoggingService-EU<br>(Applicatio Users  VPN icon in okta to view app).<br>n  Data) SAP<br>Corporate To add VPN:<br>EU- EU2- VPN<br>comm2 LoggingS Open BIG IP App<br>ervice- Click manage VPN Servers<br>(Audit  Audit Add VPN with the above URL<br>Data)<br>https://lp-search.eu2.concur.global is also accessible without the EU2 VPN via<br>GlobalProtect<br>**----- End of picture text -----**<br>


## ATM APJ1 

service-now request for OKTA group membership: 


![](logging_docs/markdown_converted/images/3286770993_65ded73675b246c881a5126387ba197c-310326-2158-7556.pdf-0002-03.png)


**----- Start of picture text -----**<br>
Service Account  Environment Group  Group Name Network Connection  Note<br>type Type Prerequisite<br>APJ-comm User  APJ1 OKTA LoggingService- NOTE:  APJ Logging Service is available ONLY from<br>Account APJ1-Users SAP Corporate VPN SAP Corporate network.<br>(Application<br>Data)<br>APJ-comm LoggingService-<br>APJ1-Audit<br>(Audit Data)<br>**----- End of picture text -----**<br>


## DR's (AMSDR) 


![](logging_docs/markdown_converted/images/3286770993_65ded73675b246c881a5126387ba197c-310326-2158-7556.pdf-0002-05.png)


**----- Start of picture text -----**<br>
Service Access type Access object Note/link Prerequisite<br>Logging open Any Concur Prod VPN<br>Audit ConcurASP LDAP group ESGDPRUsers service-now request for group membership Any Concur Prod VPN<br>**----- End of picture text -----**<br>


## **Resources:** 

USPSCC Kibana Access Request steps 

