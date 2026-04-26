## **Winlogbeat (Windows logs and events)** 

## What is Winlogbeat 

You can use Winlogbeat to ship Windows event logs to Logging Service (Elasticsearch/Kibana). You can install and run it as a Windows service. 

Winlogbeat reads from one or more event logs using Windows APIs, filters the events based on user-configured criteria in _winlogbeat.ymI_ file, then sends the event data to the configured in _winlogbeat.ymI_ output. 

Winlogbeat watches the event logs all the time, so that new event data is sent in a timely manner. 

## Winlogbeat version 

Elastic release all their tools together, so they have same versioning. Although in case of beats, there usually is support between minor or even major versions, always try to use closest possible version of winlogbeat as the logging service runs in particular location. You can find this information in version column on Service Endpoints - Logging Service. 

As we run in mixed version mode (some locations are v5, others v6), we managed to support winlogbeat v5 everywhere, and v6 on v6 environments only. 

## How to Install and Configure Winlogbeat 

Coming soon: out of the box Heartbeat install: Puppet module, Ansible script, DA workflow lib. 

1.  You can get WinlogBeat from https://www.elastic.co/downloads/past-releases#winlogbeat 2.  Unzip the WinlogBeat package 

3.  Configure log types you want to ship in _winlogbeat.ymI_ file, in _events_logs_ section. By default, its is configured to ship System, Security and Application events. 

   - `event_logs: - name: Application` 

   - `name: Security` 

   - `name: System` 

To obtain a list of available event logs, run `Get-EventLog *` in PowerShell. For more information about this command, see the configuration details for event_logs.name. 

4.  Configure outuput in _winlogbeat.ymI_ file.  In _output_ section, comment _elasticsearch_ section, and uncomment _logstash_ section.  Set correct Logstash URL, depending on the cloud environment (see Service Endpoints - Logging Service for Logstash VIPs), port is always **10301** . 

```
# Configure what outputs to use when sending the data collected by the beat.
# Multiple outputs may be used.
output:
  ### Elasticsearch as output
  #elasticsearch:
...
  ### Logstash as output
  logstash:
    # The Logstash hosts
    hosts: ["lp-index-sea.concurasp.com:10301"]
    ssl:
       enabled: true
       verification_mode: none
...
```

5.  To run it either: a.  run in PowerShell: _winlogbeat.exe -c winlogbeat.yml_ b.  or (recommended) install it as Windows Service (use _install-service-winlogbeat.ps1)_ , then run the service: _Start-Service winlogbeat ._ 

## How to View Winlogbeat Data 

WinlogBeat logs are indexed in _winlogbeat-*_ indices.  Once you configure Winlogbeat to send data to Logging Service Logstash, you will be able to find the logs in Kibana . 

## **Discover Tab** 

All WinlogBeat beats logs are indexed into _winlogbeat-*_ indices. Just choose _winlogbeat-*_ index pattern in Discover tab to explore WinlogBeat logs. 


![](logging_docs/markdown_converted/images/3286770236_ea4e6e70d53949b88363f7e381eaf4ec-310326-2148-7518.pdf-0002-02.png)


## **Sample Dashboards** 

Find **Winlogbeat-Dashboard** Kibana dashboard, in corresponding Kibana instance. 


![](logging_docs/markdown_converted/images/3286770236_ea4e6e70d53949b88363f7e381eaf4ec-310326-2148-7518.pdf-0002-05.png)


This is sample dashboard for quick start.  You can create your own vizualizations and dashboards, but please, 

do not modify this dashboard . 


![](logging_docs/markdown_converted/images/3286770236_ea4e6e70d53949b88363f7e381eaf4ec-310326-2148-7518.pdf-0002-08.png)


