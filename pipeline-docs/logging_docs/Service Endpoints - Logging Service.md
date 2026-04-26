## **Service Endpoints - Logging Service** 

Overview of the most common Kibana instances Application Logging Service Akamai Logging Service Full list of Logging Service endpoints and versions US Commercial (us-comm2) EU Commercial (eu-comm2) APJ Commercial AWS ATM Integration AWS ATM USPSCC AWS GLZ managed 

We run Logging Service clusters in each Concur cloud environment.  We do not support mixed/hybrid environments, meaning if you have applications /services running in f.e. the US2 datacenter, you should send logs to US2 Logging Service.  If you have applications/services running in RQA/Dev /localhost, you should send logs to RQA Logging Service cluster, etc. 

## Overview of the most common Kibana instances 

## **Application Logging Service** 


![](logging_docs/markdown_converted/images/Service_Endpoints_-_Logging_Serv_ded4ffa44ded42e28e57c812c664723b-310326-2200-7574.pdf-0001-05.png)


**----- Start of picture text -----**<br>
environment link to Kibana access network notes<br>US Commercial OKTA authentication (CNQR  domain)  SAP Corp (office, SAP VPNs) Data from AWS US2<br>AWS US2 VPN<br>EU Commercial OKTA authentication (CNQR domain) SAP Corp (office, SAP VPNs) Data from AWS EU2<br>AWS EU2 VPN<br>APJ commercial OKTA authentication (CNQR domain) SAP Corp (office, SAP VPNs) Data from AWS APJ1<br>AWS GLZ managed OKTA authentication (CONCURASP<br>domain)<br>AWS ATM USPSCC OKTA authentication (CNQR-PSCC) Concur USPSCC VPN<br>AWS ATM Integration OKTA authentication ( CNQR-nonprod) SAP Corp (office, SAP VPNs) Data from AWS Integration<br>AWS Integration VPN<br>**----- End of picture text -----**<br>


## **Akamai Logging Service** 


![](logging_docs/markdown_converted/images/Service_Endpoints_-_Logging_Serv_ded4ffa44ded42e28e57c812c664723b-310326-2200-7574.pdf-0001-07.png)


**----- Start of picture text -----**<br>
environment link to Kibana access network notes<br>Commercial Akamai AKAMAI Commercial service was migrated to US commercial cluster<br>CCPS Akamai AKAMAI PSCC service was migrated to PSCC Logging cluster Concur USPSCC VPN<br>**----- End of picture text -----**<br>


## Full list of Logging Service endpoints and versions 


![](logging_docs/markdown_converted/images/Service_Endpoints_-_Logging_Serv_ded4ffa44ded42e28e57c812c664723b-310326-2200-7574.pdf-0001-09.png)


**----- Start of picture text -----**<br>
Environment Elastic  VPN Kibana Access RESTful API Logstash VIP<br>Stack  /Network<br>version<br>US Commercial (us-comm2)<br>**----- End of picture text -----**<br>



![](logging_docs/markdown_converted/images/Service_Endpoints_-_Logging_Serv_ded4ffa44ded42e28e57c812c664723b-310326-2200-7574.pdf-0002-00.png)


**----- Start of picture text -----**<br>
us-comm2 8.19 SAP  lp-index.service.cnqr.tech<br>(US2 data) corporate<br>network,  https://lp-search.us2.concur. How to collect and send log data<br>Concur<br>global<br>prod VPNs<br>https://lp-search-rest.us2.<br>concur.global/<br>see REST API<br>This REST API link<br>is  NOT  accessible<br>from the DC's itself<br>(FabianUS, US2).<br>We created a<br>separate link for<br>this purpose: https://<br>lp-search-rest.<br>service.cnqr.tech/<br>which accept the   F<br>ABIAN-US-2022<br>PKI Root CA<br>EU Commercial (eu-comm2)<br>eu-comm2 8.19 SAP  lp-index.service.cnqr.tech<br>(EU2 data) corporate<br>network, https://lp-search.eu2.concur. How to collect and send log data<br>Concur<br>global<br>prod VPNs<br>https://lp-search-rest.eu2.<br>concur.global/<br>see REST API<br>This REST API link<br>is  NOT  accessible<br>from the DC's itself<br>(EU2).<br>We created a<br>separate link for<br>this purpose: https://<br>lp-search-rest.<br>service.cnqr.tech/<br>which accept the   F<br>ABIAN-EMEA-<br>2022 PKI Root<br>CA<br>APJ Commercial<br>**----- End of picture text -----**<br>



![](logging_docs/markdown_converted/images/Service_Endpoints_-_Logging_Serv_ded4ffa44ded42e28e57c812c664723b-310326-2200-7574.pdf-0003-00.png)


**----- Start of picture text -----**<br>
apj-comm 8.19 SAP  lp-index.service.cnqr.tech<br>corporate<br>network https://lp-search.apj1.concur. How to collect and send log data<br>global<br>https://lp-search-rest.apj1.<br>concur.global<br>see REST API<br>This REST API link<br>is  NOT  accessible<br>from the DC's itself<br>(EU2).<br>We created a<br>separate link for<br>this purpose: https://<br>lp-search-rest.<br>service.cnqr.tech/<br>which accept the   F<br>ABIAN-EMEA-<br>2022 PKI Root<br>CA<br>AWS ATM Integration<br>(service structure)<br>Integration 8.19 SAP  lp-index.service.cnqr.tech<br>corporate<br>network, How to collect and send log data<br>Concur  https://lp-search.integration.<br>AWS  concur.global<br>Integration<br>VPN OKTA authentication<br>https://lp-search-rest.service.<br>cnqr.tech (from integration<br>network only)<br>https://lp-search-rest.integration.<br>concur.global<br>needs x509 cert, see REST API<br>AWS ATM USPSCC<br>(service structure)<br>USPSCC 8.19 Concur US  lp-index.service.cnqr.tech<br>Public<br>Sector VPN How to collect and send log data<br>https://lp-search.service.<br>cnqr.tech<br>https://lp-search-rest.service.<br>OKTA authentication cnqr.tech<br>needs x509 cert, see REST API<br>AWS GLZ managed<br>GLZ  (managed) 8.19 Public site Everyone  NO Logstash for this environment. It is in<br>with  temporary design, where apps send data<br>concurasp  directly to Elasticsearch over REST API!<br>OKTA<br>https://6629ef1c7c1b4af2ac access<br>733a6b23883829.us-west-2.<br>aws.found.io:9243/app<br>/kibana<br>**----- End of picture text -----**<br>


**NOTE:** Current GLZ cluster is NOT build as standard Logging Service instance. But only as Cluster as a Service with integrated authentication. That means, there is no (internal) proxy, no Logstash, no Watches automation. We don't plan any future (new features) for this environment, but rather let ALL GLZ services to start logging into standard Logging Services (in US2, EU2, ...). 

