## **Application Logging** 

Primary purpose of Concur logging services is to collect logs from Concur applications and services.  We allow large number of input channels, but we do have expectations and requirements how logs are formatted and structured. 

We want to make it clear that Logging Service is **not** a SIEM service, we do not store PCI and/or sensitive PII data into Logging Service. 

It is the responsibility of each team to ensure that no Secret data (as noted in the Sensitive Information Policy located here: https://concur.box.com/s /s1nel4zbyrp3aq2tab4n) is sent to Logging Service. Accountability of all data from each product team is **owned** by the product team as a whole with the Product Mgr. and Dev Mgr. as primary contacts. 

## How to Format Application Logs 

In order to be able to treat date fields as dates, numeric fields as numbers, and string fields as full-text or exact-value strings, Elasticsearch needs to know what type of data each field contains. This information is contained in the mapping. 

We support following mapping and log format for application logs, GDPR logs, and Akamai logs: 

Application Log Format (v2) 

GDPR Log Format (v3) 

Akamai Log Format 

## How to Collect and Send Application Logs 


![](logging_docs/markdown_converted/images/Application_Logging_c2c735bbe4ea4f43bad5a68b409bb6ec-310326-0656-320.pdf-0001-11.png)


Today, we support several ways how you can ship your logs to Logging Service: 

(1) **RECOMMENDED** If you run a containerized service on Concur K8s/Tectonic, use "out of the box" logging in K8s, simply send your application logs to stdout/stderr, no need to install Filebeat or anything, our kube-logstash docker will collect those and ship to logging service in corresponding cloud environment. See Containerized Services Logging from K8s for all details. 

(2)  If you run a containerized service on standalone host (or if you want to send logs from docker on DevVM),  simply send your application logs to stdout /stderr, and use docker GELF log driver to send logs to Logging Service, see Containerized Services Logging from Standalone Docker. We do not recommend this logging channel as UDP is not reliable and there is no any queueing or retry mechanisms, in case of issue on logging service logstashes side, data loss might occur. 

(3) **RECOMMENDED** If you run a service on VM/EC2, recommended approach is to use Filebeat to ship your logs to logging service.  Filebeat reads logs from file(s) and ship them over secure SSL connection to logging service in corresponding cloud environment. Filebeat has native communication channels to Elasticsearch/Logstash and native push back (and later push forward) in case of performance issues on server side. Find logging services logstash endpoints on Service Endpoints - Logging Service page. 

(4)  Send logs to Logging Service Logstash directly, through Logstash Forwarder, or through middle-man Logstash.  As we expect logs to be in certain predefined format, if you are not able to format logs properly when you write them, you would need to set up your own (as we call it middle-man) Logstash to do the transformation with grok filters, before logs are shipped to logging service logstashes. We do not plan to stop supporting Logstash/Logstash Forwarder, but consider using Filebeat instead as recommended and better practice. 

(5)  Send logs to Logging Service Logstash directly via TCP or GELF.  We do not recommend these logging channels for Prod logging, as there is no any queueing or retry mechanisms, in case of issue on logging service logstashes side, data loss might occur. 

(6)  DO **NOT** Send logs to RabbitMQ **. See RabbitMQ Clusters - End of life** 

(7)  If you want to collect standard Windows events logs, see Winlogbeat (Windows logs and events). 

(8)  If you want to perform health check/heartbeat pings to dependent services or monitor uptime of your service, see how to use Heartbeat (Service health monitoring). 

## How to Display and Query Application Logs 


![](logging_docs/markdown_converted/images/Application_Logging_c2c735bbe4ea4f43bad5a68b409bb6ec-310326-0656-320.pdf-0002-06.png)


Kibana is a data visualization platform that allows you to interact with your Elasticsearch data through stunning, powerful graphics. From histograms to geomaps, Kibana brings your data to life with visuals that can be combined into custom dashboards that help you share insights from your data far and wide. 

Additionally to Kibana, you can use Timelion to create visualizations and dashboards, and Development Tools Console (Sense) and Elasticsearch REST API to poll and search for raw data. 

Kibana 

Timelion 

REST API 

Dev Tools (Sense) 

## How to Monitor and Detect Changes in Application Logs 

Elastic stack offers alerting features, as part of its X-Pack features set. 

Using Elasticsearch Watcher, you can monitor over changes in your logging data.  You can choose the proper method for notification, suitable for your team, like email, Slack, PagerDuty. 

Watcher 

Watcher Tips 

Watch definitions samples: https://github.concur.com/cia/watcher 

