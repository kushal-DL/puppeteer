## **GDPR Log Format (v3)** 

Current supported version of data mapping for GDPR personal data access and change logs is **data version 3 (dv3).** 

NOTE: GDPR required fields are in **green** . System fields (not GDPR required, but logging service required) are in **blue** . Logs of type  'access', 'change', 'query', not compliant with format and structure below, get trashed (= are placed into trash-* index). Logs of type  'access', 'change', 'query', compliant with format and structure below, containing ADDITIONAL fields, not specified below, are not trashed, but additional fields are pruned. 


![](logging_docs/markdown_converted/images/3286770986_dc40e755e5844d978c1cbef200a68ee2-310326-2144-7486.pdf-0001-03.png)


We expect all values to be UTF-8 encoded, logging service logstashes refuse non UTF encoded messages. 

Access Logs Format Change Logs Format Sensitive data creation Sensitive data update Sensitive data deletion Query Logs Format 

## Access Logs Format 

In case of personal sensitive data access, it is perfectly acceptable (and recommended) to log only one single "access" log in case of bulk actions, i.e. bulk of users' data viewed/accessed. 


![](logging_docs/markdown_converted/images/3286770986_dc40e755e5844d978c1cbef200a68ee2-310326-2144-7486.pdf-0001-08.png)


**----- Start of picture text -----**<br>
field  type example description notes<br>name<br>@by string "filebeat" Logstash input method: filebeat, rabbitmq,  This is internally set field, do not set by yourself, it is  always  fil<br>etc led by Logstash. Defines input method used: FileBeat, RMQ,<br>TCP, GELF, Syslog, etc.<br>@env string "seapr1" Concur cloud environment name This is internally set field, always filled by Logstash, do not<br>set it by yourself. Defines which environment the logs come<br>from.<br>@times date "2015-05-29T10:16:30.605592476-04: Time of event The time of log event. If not set, Logstash will fill it<br>tamp 00" automatically using current (indexing) time. Its recommended<br>If timestamp format is not ISO8601  to set this on your side, as in case of latency with indexing,<br>compliant, or @timestamp value is not in  you will get data logs with different @timestamp value than<br>range [-23h, now], [now, +1h], then  the value of log generation.<br>Logstash will send the doc to Trash index<br>with corresponding error.<br>data_ve integer 3 Major data version Required field.<br>rsion<br>The new supported version is 3 (as integer).<br>applicat string "EMT" Application name (specific name like  Required field.<br>ion "EMT", "Outtask","Receipts", "TripIt", etc)<br>roletype string "emt" Service role type, as defined in RMS Required field.<br>type string "access" Target Elasticsearch index, where the log  Required field.<br>will get indexed.<br>For this type of log value is always "access".<br>For this type of log value is always<br>"access".<br>caller_id string "c234u62357863jas4" Id of caller accessing personal sensitive  Required field.<br>data<br>Example: acting user CTE UUID or service caller ID, to be<br>used together with  caller_id_type  to identify caller.<br>caller_i string "cte_uuid" Type of caller id, enum: Required field.<br>d_type<br>cte_uuid, hmc_id, x509, jwt, basic_auth,<br>job_code<br>**----- End of picture text -----**<br>



![](logging_docs/markdown_converted/images/3286770986_dc40e755e5844d978c1cbef200a68ee2-310326-2144-7486.pdf-0002-00.png)


**----- Start of picture text -----**<br>
custom string "c234u62357863jas4" Whose personal sensitive data is being  UUID of person whose personal data is being accessed.<br>er_user accessed<br>_id or  or UUID needs to be such, so user can be identified in Concur<br>array  systems.<br>of  [ "c234u62357863jas4",<br>strings "qwe24234234easde",  Can be also a list of UUIDs sent as an array of strings.<br>"re293849230jbfbdjk" ]<br>NOTE: logging service rejects logs with size > 100MB, if you<br>need to log access for huge amount of customers' personal<br>data, consider splitting to logs to chunks with max size<br>100MB.<br>event_t string "view profile data" Particular action/event of accessing  Required field.<br>ype personal sensitive data<br>event_o string "CTE profile page" Where the data is being accessed from Required field.<br>rigin<br>data_fie string An example of such field value might  What data field/property is being accessed Data field/property being accessed.<br>ld be Outtask DB table column, or<br>or  something like DSAmountToken. Can be also a list of data fields/properties being accessed.<br>array  CouchbaseBucketName.<br>of  JSONFieldName in Couchbase case<br>strings<br>compan string 1204a92a-909d-40bc-a177- Company UUID It is not YET required field, but very possibly will be required<br>y_uuid 76715d88ba74 by compliance team<br>**----- End of picture text -----**<br>


## Change Logs Format 

Change log for personal sensitive data covers its **creation** , **update** and **deletion** to these data. There is no specific operation type field (yet). But these scenarios are handled by data_field_* values - please see possible combinations below next table. 

NOTE: in case of personal data change, there should be one "change" log per change action. 


![](logging_docs/markdown_converted/images/3286770986_dc40e755e5844d978c1cbef200a68ee2-310326-2144-7486.pdf-0002-04.png)


**----- Start of picture text -----**<br>
field  type example description notes<br>name<br>@by string "filebeat" Logstash input method: filebeat, rabbitmq,  This is internally set field, do not set by yourself, it is  always  fil<br>etc led by Logstash. Defines input method used: FileBeat, RMQ,<br>TCP, GELF, Syslog, etc.<br>@env string "seapr1" Concur cloud environment name This is internally set field, always filled by Logstash, do not<br>set it by yourself. Defines which environment the logs come<br>from.<br>@times date "2015-05-29T10:16:30.605592476-04: Time of event The time of log event. If not set, Logstash will fill it<br>tamp 00" automatically using current (indexing) time. Its recommended<br>If timestamp format is not ISO8601  to set this on your side, as in case of latency with indexing,<br>compliant, or @timestamp value is not in  you will get data logs with different @timestamp value than<br>range [-23h, now], [now, +1h], then  the value of log generation.<br>Logstash will send the doc to Trash index<br>with corresponding error.<br>data_ve integer 3 Major data version Required field.<br>rsion<br>The new supported version is 3 (as integer).<br>applicat string "EMT" Application name (specific name like  Required field.<br>ion "EMT", "Outtask","Receipts", "TripIt", etc)<br>roletype string "emt" Service role type, as defined in RMS Required field.<br>type string "change" Target Elasticsearch index, where the log  Required field.<br>will get indexed.<br>For this type of log value is always "change".<br>For this type of log value is always<br>"change".<br>caller_id string "c234u62357863jas4" Id of caller changing personal data Required field.<br>Example: acting user CTE UUID or service caller ID, to be<br>used together with  caller_id_type  to identify caller.<br>caller_i string "cte_uuid" Type of caller id, enum: Required field.<br>d_type<br>cte_uuid, hmc_id, x509, jwt, basic_auth,<br>job_code<br>custom string "c234u62357863jas4" Whose personal data is being changed UUID of person whose personal data is being changed.<br>er_user<br>_id UUID needs to be such, so user can be identified in Concur<br>systems.<br>**----- End of picture text -----**<br>



![](logging_docs/markdown_converted/images/3286770986_dc40e755e5844d978c1cbef200a68ee2-310326-2144-7486.pdf-0003-00.png)


**----- Start of picture text -----**<br>
event_t string "change profile data" What is the type of data change operation Required field.<br>ype<br>event_o string "CTE profile page" Where the data is being changed from Required field.<br>rigin<br>data_fie string An example of such field value might  What data field/property is being changed Data field/property being changed.<br>ld be Outtask DB table column, or<br>something like DSAmountToken.<br>CouchbaseBucketName.<br>JSONFieldName in Couchbase case<br>compan string 1204a92a-909d-40bc-a177- Company UUID It is not YET required field, but very possibly will be required<br>y_uuid 76715d88ba74 by compliance team<br>data_fie string Example: customer email old value personal data value before the change This value is required to be logged in case of non-sensitive<br>ld_befo personal data values.<br>re could be also 'null'<br>Should not be used to log sensitive personal data.<br>data_fie string Example: customer email new value personal data value after the change This value is required to be logged in case of non-sensitive<br>ld_after personal data values.<br>Should not be used to log sensitive personal data.<br>**----- End of picture text -----**<br>


## **Sensitive data creation** 

When new data/field is created, this event has to be logged as a GDPR audit change event. Fill in all required fields and: 

data_field_before - leave it blank or do not include at all data_field_after - include new value 

## **Sensitive data update** 

When sensitive data are updated, this event has to be logged as a GDPR audit change event. Fill in all required fields and: 

data_field_before - include old value data_field_after - include new value 

## **Sensitive data deletion** 

When sensitive data are deleted (ie. user deletion), this event has to be logged as a GDPR audit change event. Fill in all required fields and: 

data_field_before - include old value data_field_after - leave it blank or do not include at all 

## Query Logs Format 

NOTE: query logs format is introduced to support cases like general personal data access from tools and services like DBSelect, SQL, Couchbase, Elasticsearch, etc. DO NOT use this type of log to track personal sensitive data access done thru CTE applications, for that, please use 'access' type of log. 


![](logging_docs/markdown_converted/images/3286770986_dc40e755e5844d978c1cbef200a68ee2-310326-2144-7486.pdf-0003-12.png)


**----- Start of picture text -----**<br>
field  type example description notes<br>name<br>@by string "filebeat" Logstash input method: filebeat, rabbitmq, etc This is internally set field, do not set by yourself, it is  always  filled by<br>Logstash. Defines input method used: FileBeat, RMQ, TCP, GELF, Syslog,<br>etc.<br>@env string "seapr1" Concur cloud environment name This is internally set field, always filled by Logstash, do not set it by yourself.<br>Defines which environment the logs come from.<br>@times date "2015-05- Time of event The time of log event. If not set, Logstash will fill it automatically using current<br>tamp 29T10:16: (indexing) time. Its recommended to set this on your side, as in case of<br>30.605592 If timestamp format is not ISO8601 compliant, or  latency with indexing, you will get data logs with different @timestamp value<br>476-04:00" @timestamp value is not in range [-23h, now], [now,  than the value of log generation.<br>+1h], then Logstash will send the doc to Trash index<br>with corresponding error.<br>data_ve integer 3 Major data version Required field.<br>rsion<br>The new supported version is 3 (as integer).<br>roletype string "lgs" Service role type, as defined in RMS Required field.<br>I.e logging service will log all access to personal data in logs, and uses "lgs"<br>to identify its logging services.<br>type string "query" Target Elasticsearch index, where the log will get  Required field.<br>indexed.<br>For this type of log value is always "query".<br>For this type of log value is always "query".<br>**----- End of picture text -----**<br>



![](logging_docs/markdown_converted/images/3286770986_dc40e755e5844d978c1cbef200a68ee2-310326-2144-7486.pdf-0004-00.png)


**----- Start of picture text -----**<br>
caller_id string "yovka. Id of caller accessing personal data via direct query Required field.<br>pencheva<br>@concur. User ID who runs query to view personal customer data. To be used together<br>com" with  caller_id_type  to identify caller.<br>caller_i string "concur_id" Type of caller id, enum: Required field.<br>d_type<br>cte_uuid, hmc_id, x509, jwt, basic_auth, concur_id,<br>job_code<br>query string A query executed, can be DB query, Elasticsearch  Required field.<br>query, etc.<br>**----- End of picture text -----**<br>


