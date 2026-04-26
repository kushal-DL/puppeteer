## **How to collect and send log data** 

1. What do you cant to collect? - pick a shipper 

2. Visit shipper detail page 

3. Get Logging Service endpoint based on your env - Logstash VIP 


![](logging_docs/markdown_converted/images/How_to_collect_and_send_log_data_19b9b75cd22f4deb95dfa01fdee9b514-310326-2145-7492.pdf-0001-04.png)


## Logging Service Data shippers 


![](logging_docs/markdown_converted/images/How_to_collect_and_send_log_data_19b9b75cd22f4deb95dfa01fdee9b514-310326-2145-7492.pdf-0001-06.png)


**----- Start of picture text -----**<br>
data  usage platform FIPS-compliant notes<br>shipper<br>ships log files Linux  requires package  filebeat-fips<br>FIleBeat<br>(built with BoringCrypto)<br>Windows exception approved<br>ships Windows Event Logs Windows exception approved<br>Winlog<br>Beat<br>ships OS and applications metrics Linux  requires package  metricbeat-<br>MetricB fips<br>eat<br>(built with BoringCrypto)<br>Windows exception approved<br>checks remote network services Linux  requires package  elasic-<br>HeartBe heartbeat-fips<br>at<br>(built with BoringCrypto)<br>Windows exception approved<br>ships logs from AWS CloudWatch or Kinesis AWS<br>Functio lambda<br>nBeat (cannot be rebuilt due to licensing<br>issue; seeking exception)<br>ingests, transforms, and ships your data  Linux,<br>Logsta regardless of format or complexity Windows<br>sh (cannot run with BouncyCastle;<br>seeking exception)<br>ships log files, Windows Event Logs, OS and  Linux  requires package  fluentbit-*.<br>Bit Fluent applications metrics cnqr<br>Windows<br>(not recommended due to untrusted<br>encryption library)<br>ships JSON logs over plain TCP connection * Deprecated, not available in<br>TCP Integration, USPSCC, Fabian<br>(deprecated)<br>ships SYSLOG messages * Not available in Integration,<br>SYSL USPSCC, Fabian<br>OG<br>ships AWS logs for ELB, VPC and lambdas  AWS Available only in Integration,<br>AWS  USPSCC, Fabian<br>services<br>**----- End of picture text -----**<br>


ships container 's STDOUT/STDERR `*` in K8s team jurisdiction _cont ainer_ ships Cloud Monitor logs Akamai Akam ai 

