## **Heartbeat (Service health monitoring)** 

Heartbeat is a lightweight daemon that you install on a remote server to periodically check the status of your services and determine whether they are available. Unlike Metricbeat, which only tells you if your servers are up or down, Heartbeat tells you whether your services are reachable. 

The beat ships all collected metrics into Logging Service in corresponding datacenter, and you can set up monitoring (or auto-remediation actions) using Elastic Watcher (Watcher) 


![](logging_docs/markdown_converted/images/3286771128_ee9a4160d6004465b66d464408e9f911-310326-2148-7520.pdf-0001-03.png)



![](logging_docs/markdown_converted/images/3286771128_ee9a4160d6004465b66d464408e9f911-310326-2148-7520.pdf-0001-04.png)



![](logging_docs/markdown_converted/images/3286771128_ee9a4160d6004465b66d464408e9f911-310326-2148-7520.pdf-0001-05.png)


Heartbeat is useful when you need to verify that you’re meeting your service level agreements for service uptime.  You can use it to check if all services behind ELB/VIP are up and running, or you can use it in many-to-many fashion and check inter-services dependences. 

Sample dashboard how to use HeartBeat for SLI/SLA monitoring: https://lp-search-sea.concur.com/app/kibana#/dashboard/LoggingService-status. You can also build watchers over Heartbeat metrics. 

## How to Install and Configure Heartbeat 

## 1. Install Heartbeat, 

Note In most cases we run ElasticSearch version 5.6 , in some cases version 6.x, check the version under the management link in kibana, e.g. https://lpsearch-sea.concur.com/app/kibana#/management 

**version 5, see** : https://www.elastic.co/guide/en/beats/heartbeat/5.6/heartbeat-installation.html 

**version 6, see** : https://www.elastic.co/guide/en/beats/heartbeat/6.6/heartbeat-installation.html 

2. Configure Heartbeat, see https://www.elastic.co/guide/en/beats/heartbeat/current/heartbeat-configuration.html 

Sample config, Heartbeat which monitors each 60s web app reachable at https://lp-kibana-mapping-aws.concurasp.com 

To configure HeartBeat in other environments, just use corresponding logstash endpoint for that environment, see endpoints on Service Endpoints - Logging Service .  Port is always 10301. 

```
heartbeat.monitors:
- check.request:
    method: GET
  check.response.status: 200
  schedule: "@every 60s"
  ssl:
    verification_mode: none
  type: http
  urls:
  - https://lp-kibana-mapping-aws.concurasp.com
output.logstash:
  hosts:
  - lp-index-awsqa.concurasp.com:10301
  ssl.enabled: true
  ssl.verification_mode: none
```

3. Run Heartbeat, see https://www.elastic.co/guide/en/beats/heartbeat/current/heartbeat-starting.html 

## How to View Heartbeat Data 

## **Discover Tab** 

All Heartbeat data is indexed into _heartbeat-*_ indices. Just choose _heartbeat-*_ index pattern in Discover tab in Kibana to explore Heartbeat metrics. 


![](logging_docs/markdown_converted/images/3286771128_ee9a4160d6004465b66d464408e9f911-310326-2148-7520.pdf-0002-09.png)


