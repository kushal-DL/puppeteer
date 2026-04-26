## **Application Log Format (v2)** 

Data Size Limitations Data Mapping Rules Analyzed (.analyzed) fields Common fields for all data types: log, metric, txn Extra fields for 'log' type data index name pattern: log-* Shared Buckets (Nested JSON Objects) Custom Buckets ("MyApp" Buckets) Custom Buckets best practices When you need a field to be indexed Custom Buckets mapping data types Process to manage Custom Bucket(s) Custom buckets regular clean-up 

Mapping is the process of defining how a document - and the fields it contains - are stored and indexed.  We use mappings to define which string fields should be treated as full-text fields, which should be tokenized, which fields contain numbers, dates, geolocations, etc.  More can be read on Elasticsearch Mapping documentation. 

The currently supported version of data mapping for application logs is **data version 2 (dv2).** 

## Data Size Limitations 

To prevent failures or performance degradation, and make our service available for everyone, we put **these size limitation rules to place** : 

if a document > 10MB, we drop it immediately (before it is parsed by our data processor) 

if a document is > 1MB, we parse every single field and truncate it (that field) to max 256kB. It is usually 1 or 2 fields being huge (sometimes up to 4). We found that 256kB should be more than enough to cover 99.99% of needs 

## **Why?** 

It was common that our systems received HUGE log files. Like tens of thousands per hour > 1MB, or hundreds per hour > 10MB. But some teams went to extreme, and were sending us up to 900MB single log file (that was a movie or what??). These big files were causing us serious damage, like: 

significant ingestion pipeline slowness. Our data processor (logstash) parse EVERY single document and read (and process) each field in it. Simultaneously processing thousands of such documents, building bulks, compressing... Average document is about 1.6 kB big. Having there one or more documents that are bigger than 10MB might be causing rejections of the bulk due to its size by elasticsearch, slowness in processing, and slowness in ingesting 

bulks rejections. Elasticsearch has some limitations on how big bulk (size) it can receive. If we put coincidentally more than 2-3 big logs into single bulk, it could be rejected and had to be re-bulked again. 

Kibana failing on Out Of Memory. Kibana in discovery tab by default load first 500 documents. If one of those documents was > 10MB, it took significant time to load at all or sometimes it failed on either timeout. If there were 2 or more such documents, kibana client failed almost every time. Sometimes it cause kibana server to crash too (OOM). 

Above failures always lead to users being unhappy. 

## Data Mapping Rules 

Logging Service is **not** a SIEM service, we do not store PCI data into Logging Service. 

It is the responsibility of each team to ensure that no Sensitive data is sent to Logging Service. Accountability of all data from each product team is **owned** by the product team as a whole with the Product Mgr. and Dev Mgr. as primary contacts. 

This is a list of all fields that are supported by Concur Logging Service mapping.  Any other doc fields will be still stored into Elasticsearch, but not usable for search/sort/aggregation operations. 

## **Analyzed (.analyzed) fields** 

As a general rule, use: 

_**analyzed**_ fields for full-text search _**not_analyzed**_ fields for sorting/term aggregations. 

Some fields are indexed in both _**analyzed**_ and _**not_analyzed**_ manner. 

Example of the field **`application`** : 

**`application`** can be used for sorting and term aggregations **`application.analyzed`** can be used for full-text search. 

Analyzed field means, its value is analyzed and split into tokens (words, from a very simple perspective). These are some basic delimiters for analyses: [  , | / \ - " ' ( ) ...]. For a complete overview of analyzer behavior, visit the Elastic page for the standard analyzer. 

ALL string fields are ALWAYS _lowercased_ at index time. As well as ALL queries at query time. This means, **LoggingService is case-insensitive for searched values, but NOT for field names!!!** 

These two queries are _**equal**_ : 

```
level: Error
level: error
```

These two queries are _**completely different**_ , as they refer to different fields (where the field **`Level`** doesn't exist): 

**`level`** `: error` **`Level`** `: error` **Common fields for all data types:** **`log` ,** **`metric` ,** **`txn`** 

Required fields are in green, if your log document does not contain all required fields, it will not be indexed properly, your log will end up in **`trash`** index with the corresponding filed **`@error`** added. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0002-07.png)


The field **`correlation_id`** is marked as red - it is not required by Logging Service, but ALL logs that handle Concur requests require it!! 

Be aware of yellow fields as well - these are for large text fields and have special mapping: index ONLY the first 80 tokens (~words) from the value, store it whole. Also, these fields are not usable for aggregations! 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0002-10.png)


We expect all values to be UTF-8 encoded, Logging Service refuses non-UTF encoded messages. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0002-12.png)


**----- Start of picture text -----**<br>
field  type indexing sort example description notes<br>name /aggregations<br>@by string "filebea Ingestion type: filebeat, http,  This is an internally set field, do not set it by yourself, it is  always  f<br>t" etc. illed by Logging Service. Defines input method used: FileBeat,<br>TCP, GELF, Syslog, etc.<br>@env string "seapr1" Concur cloud environment  This is an internally set field, always filled by Logging Service, do<br>name not set it by yourself. Defines which environment the logs come<br>from.<br>@times date "2015- Time of event The time of log event. If not set, Logging Service will fill it<br>tamp 05- automatically using current (indexing) time. It's recommended to<br>29T10: If timestamp format is not  set this on your side, as in case of latency with indexing, you will<br>16: ISO8601 compliant, or  get data logs with a different value than the value of log<br>30.60559 @timestamp value is not in  generation.<br>2476-04: the range [-23h, now], [now,<br>00" +1h], then Logging Service will<br>send the doc to Trash index<br>with corresponding error.<br>type string not_analyzed yes "log" Target Elasticsearch index,  Logging Service fills this field automatically if the value is missing,<br>where the doc will get indexed. but only on inputs with an unambiguous type (like SYSLOG<br>messages).<br>Available options: [ log ,  metric<br>,  txn ,  gds ]<br>data_ve integer 2 Major data version The only supported value is " 2 ", if the value is not '2' even if your<br>rsion log structure follows data v2 format, the log will be trashed.<br>applicat string not_analyzed not_analyzed yes "EMT" Application name (specific  You can use  application.analyzed  for full-text search<br>ion name like "EMT", "Outtask"," operations.<br>.analyzed Receipts", "TripIt", etc)<br>roletype string not_analyzed yes "emt" role type, as defined in RMS Documents with evidently invalid roletypes will be trashed!  T<br>his regular expression condition has to be met:<br>[0-9a-zA-Z_-]{2,20}<br>**----- End of picture text -----**<br>



![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0003-00.png)


**----- Start of picture text -----**<br>
correlati string not_analyzed yes "60bfa23 Unique identifier of a complete  The first service that handles Concur request (web, API, event-<br>on_id b-9bfe- end-to-end request to Concur  subscriber, etc) should generate a correlation_id, and pass it to<br>4280- services. downstream services in the HTTP header (  concur-correlationid<br>5c49- ). Every service which receives a correlation_id is obligated to<br>28c77f1c This differs from request_id. use that correlation_id and pass it to next service. If a correlation<br>16ab" ID is not provided in the request, the service should generate its<br>own.<br>correlation_id field should be still used always when<br>possible, in context of related CONCUR services logs<br>name string not_analyzed yes "DbConne Event/log name<br>ctionSuc<br>cessful" limited to 80 characters<br>descripti string analyzed  no "Connect Description Description field is heavily used - is not an exception where<br>on (80 tokens) ion to  description field contain up to 10MB value.<br>the<br>database We index description field value as analyzed string - but  only<br>has  first 80 tokens are analyzed , rest is skipped!<br>been<br>establis Because it is analyzed, do NOT use wildcards to search in. This<br>hed." is field with high cardinality, and wildcard first won't help you<br>much and second will take a lot of resources to find proper value!<br>Description field is also NOT allowed for aggregations or sorting.<br>count long yes 12 counter<br>category string not_analyzed yes trip log category This might look like a redundancy with cte.category. But category<br>field is very helpful field, and not all logs belong to CTE.<br>.analyzed<br>subcate string not_analyzed yes booked log subcategory This might look like a redundancy with cte.subcategory. But<br>gory subcategory field is very helpful field, and not all logs belong to<br>.analyzed CTE.<br>environ string not_analyzed yes "pr" Environment, set by data  This is logical replacement of datacenter_location<br>ment producer<br>"qa"<br>service string not_analyzed yes core  Service or source of the data<br>method string not_analyzed yes "GetDbCo The method or function<br>nnection" invoked<br>.analyzed<br>applicati string not_analyzed yes<br>on_versi<br>on<br>client string not_analyzed yes "8.9.10. Client hostname or IP Proper host name or IP is provided. Just one value, no comma-<br>11" separated list allowed.<br>.analyzed<br>client_g geo_po Useful for geo map  Generated by Logging Service, based on client field value, only if<br>eo int visualizations in Kibana. proper name or IP is provided in client field value.<br>server string not_analyzed yes "192.168 Server hostname or IP<br>.1.1"<br>.analyzed<br>host string not_analyzed yes "rqa3- Host hostname or IP<br>cb.<br>.analyzed concurte<br>ch.org"<br>request_ string not_analyzed yes "60bfa23 Unique identifier of a request  The request_id is most useful when a particular service is called<br>id b-9bfe- to a standalone Concur  multiple times with same correlation_id.<br>4280- service.<br>5c49-<br>28c77f1c<br>16ab"<br>login_id string not_analyzed yes "mlore@o User login ID You can use login_id.analyzed for full text search operations.<br>uttask.<br>.analyzed com"<br>user_uuid string not_analyzed yes "60bfa23 The profile service uuid of the  In the case of a delegation or proxy scenario, this is the<br>b-9bfe- user for which the action is  delegatee.<br>4280- performed.<br>5c49-<br>28c77f1c<br>16ab"<br>**----- End of picture text -----**<br>



![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0004-00.png)


**----- Start of picture text -----**<br>
delegate string not_analyzed yes "60bfa23 The profile service uuid of the<br>_user_u b-9bfe- delegate or proxy user if<br>uid 4280- applicable. If no delegation<br>5c49- session is in place then this<br>28c77f1c field is left blank<br>16ab"<br>compan string not_analyzed yes "60bfa23 The profile service uuid of the<br>y_uuid b-9bfe- affected company.<br>4280-<br>5c49-<br>28c77f1c<br>16ab"<br>session string not_analyzed yes "60bfa23 User's session ID<br>_id b-9bfe-<br>4280-<br>5c49-<br>28c77f1c<br>16ab"<br>number long yes 2 number of logged events<br>_of_eve<br>nts<br>resource string not_analyzed yes inbound<br>/outbound<br>.analyzed<br>sourcefile string not_analyzed yes /opt Source file for an event<br>/file.<br>log<br>endpoint string not_analyzed yes web  Formerly called "action".  You can use endpoint.analyzed for full text search operations.<br>service  Examples:<br>.analyzed endpoint GetExpenseFormControls,<br>EmployeeService.<br>saveEmployee<br>tags string  not_analyzed yes jwt, ["foo",  These are tags for any purpose Logging service use this field even for their type of metadata.<br>"bar", ... ] Don't be confused to see mix of values there<br>request_ string analyzed no <request Request body<br>payload (first 80  /><br>tokens)<br>respons string analyzed no <respons Response body<br>e_paylo (first 80  e/><br>ad tokens)<br>duration double yes<br>_ms<br>average double yes<br>_ms<br>sum_ms double yes<br>databas double yes<br>e_ms<br>start_time date ignore_malf "2015- ... if not in proper format, this  field to support envoy logging. In case of different format then<br>ormed 05- field is ignored, but rest of the  ISO86701 (as in example), it is taken as malformed. In such<br>29T10: document is not rejected from  case, log is not rejected, but the value in this field is ignored.<br>16: indexing<br>30.605-<br>04:00"<br>respons string field to support envoy logging<br>e_code<br>respons string field to support envoy logging<br>e_flags<br>downstr string field to support envoy logging<br>eam_loc<br>al_addre<br>ss<br>upstrea string field to support envoy logging<br>m_clust<br>er<br>upstrea string field to support envoy logging<br>m_local<br>_Address<br>**----- End of picture text -----**<br>



![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0005-00.png)


**----- Start of picture text -----**<br>
upstrea string field to support envoy logging<br>m_trans<br>port_fail<br>ure_rea<br>son<br>upstrea double field to support envoy logging<br>m_durati<br>on_ms<br>route string not_analyzed yes "unstable- the route that handled the  the field is used for Named Routing (defined in https://github.<br>foobar",  request. concur.com/ap/proposals/tree/master/concur-route) and this field<br>"stable" ... is used to identify the actual route that was used. This field can<br>be used in conjunction with  request_obj.route  to identify<br>issues with routing.<br>**----- End of picture text -----**<br>


**Example of minimal valid log document:** ( _@timestamp is semi-required. If not present, one will be added by Logging Service, but at index time, not generation time_ ) 

```
{ "type":"log", "application":"lgs", "roletype":"lgs", "level":"info", "data_version":2 }
```

Example how to use not_analyzed and .analyzed fields in search operations 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0005-04.png)


**not_analyzed** string fields are ALSO case insensitive. We apply lowercase filter on all analyzed and even not_analyzed fields. 

**analyzed** string fields are split to tokens by standard tokenizers (like space, comma, dash, quote ...). Then you search only for these tokens and NOT whole sentences anymore. Wildcards doesn't make much sense here. 

## **Extra fields for 'log' type data** 

## **index name pattern: log-*** 

Log data type has the following additional common fields: 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0005-10.png)


**----- Start of picture text -----**<br>
field  type indexing sort example description notes<br>name /aggregations<br>level string not_analyzed yes info, INFO, warning, error, 30, 40 ... ONLY these values are allowed:<br>(case-insensitive)<br>[fatal|panic|emerg|alert|crit|err|warn|notice|info].*<br>if (is Numeric) level >= 20<br>class string not_analyzed not_analyzed yes "FabledIter Class name (used by Java  You can use class.analyzed for full text search operations.<br>ator" code typically)<br>.analyzed<br>thread string not_analyzed yes "Thread-1" Thread name/id (used by Java<br>code typically)<br>line long yes 42 Code line number<br>error_id string not_analyzed yes 123abc ID of error this is old way to log error id.<br>But since many apps use, we will still support it together<br>.analyzed with  error  object<br>**----- End of picture text -----**<br>



![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0005-11.png)


## **IMPORTANT** 

Because of budget or other limitations, specific acceptance criteria can be applied to various environment(s) - please, read through Data optimizations wiki page, for more details 

## **Shared Buckets (Nested JSON Objects)** 

## **Metric bucket** 

Metric bucket great for metric type of info within log/metric indexes. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0006-00.png)


**----- Start of picture text -----**<br>
field  type indexing sort example description notes<br>name /aggregations<br>instance string not_analyzed yes "my host" Related to instance<br>(host, container, ...)<br>path string not_analyzed yes "http::success::200" path to metric<br>service string not_analyzed yes "Travel-NUI" metric for service<br>time date yes "2015-05-29T10:16: time of metric event This is specifically usable if metric bucket is<br>30.605592476-04:00" used as nested array of metrics<br>value double yes 123.45<br>**----- End of picture text -----**<br>


## **CTE bucket** 

This is a nested JSON called cte. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0006-03.png)


**----- Start of picture text -----**<br>
field  type indexing sort example notes<br>name /aggregations<br>entity_code string not_analyzed yes "phos123488" Expense entity code<br>category string not_analyzed yes "Database" Error categorization<br>.analyzed You can use category.analyzed for full text search operations.<br>subcategory string not_analyzed yes "Timeout" Sub-category of the log<br>.analyzed You can use subcategory.analyzed for full text search<br>operations.<br>company_id string not_analyzed yes 123abc company ID<br>cuuid string not_analyzed yes 123e4567-e89b-12d3-a456- Concur Unique User ID<br>426655440000<br>user_id string not_analyzed yes 123e4567-e89b-12d3-a456- User's ID in the Outtask database<br>426655440000<br>company_n string not_analyzed yes "Concur" Company name<br>ame<br>.analyzed You can use company_name.analyzed for full text search<br>operations.<br>user_name string not_analyzed yes "Vernon Bear" User name<br>.analyzed You can use user_name.analyzed for full search operations.<br>pool_name string not_analyzed yes pool<br>saw_error_ boolean true Whether the user saw an error page (I have never liked this<br>page field - it's unreliable by default)<br>handled boolean true Whether the error was handled or not<br>prod_offeri string not_analyzed yes<br>ng<br>**----- End of picture text -----**<br>


## **Travel bucket** 

This is a nested JSON called travel. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0006-06.png)


**----- Start of picture text -----**<br>
field  type indexing sort example description notes<br>name /aggregations<br>application_n string not_analyzed yes LOG-2099<br>ame<br>booking_pcc string not_analyzed yes "6YB9" Pseudo-city code used for<br>travel booking<br>meeting_id string not_analyzed yes<br>gds_type long yes 3 Travel reservation system<br>type<br>travel_config long yes 42 Company's travel config ID<br>_id<br>agency_name string not_analyzed not_analyzed yes "Amex UK" Name of the TMC You can use agency_name.analyzed for full text<br>search operations.<br>.analyzed<br>**----- End of picture text -----**<br>


record_locat string not_analyzed yes "C4WG5H" GDS PNR code or 

## **Expense bucket** 

This is a nested JSON called expense. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0007-03.png)


**----- Start of picture text -----**<br>
field name type indexing sort/aggregations example description notes<br>expense_db string not_analyzed yes SEAPR1DB0094 Expense database server<br>is_expense_multitenant boolean TRUE Whether the expense company is multi-tenant<br>**----- End of picture text -----**<br>


## **Mobile bucket** 

This is a nested JSON called mobile. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0007-06.png)


**----- Start of picture text -----**<br>
field name type indexing sort example description notes<br>/aggregations<br>platform string not_analyzed not_analyzed yes "android" Android/Ios You can use platform.analyzed for full text search<br>operations.<br>.analyzed<br>network string not_analyzed yes "Verizon" Carrier<br>device_manufact string not_analyzed yes "Apple" Apple, Samsung,<br>urer HTC, etc<br>**----- End of picture text -----**<br>


## **Web access bucket (web_access)** 

This is a nested JSON called mobile. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0007-09.png)


**----- Start of picture text -----**<br>
field  type indexing sort example description notes<br>name /aggregations<br>request_m string not_analyzed yes "POST"<br>ethod<br>request_p string not_analyzed yes "/foo/bar"<br>ath<br>request_pr string not_analyzed yes "HTTP/1.1"<br>otocol<br>body_byte long yes 213<br>s_sent<br>http_user_ string not_analyzed yes "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36<br>agent (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"<br>remote_ad string not_analyzed yes 10.20.30.40<br>dr<br>**----- End of picture text -----**<br>


## **Kubernetes bucket** 

This is a nested JSON called kubernetes. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0007-12.png)


**----- Start of picture text -----**<br>
field name type indexing sort example description notes<br>/aggregations<br>container_id string not_analyzed yes d304f86a98ec112<br>e22a6...<br>container_name string not_analyzed yes healthz You can use container_name.analyzed for full text<br>search operations.<br>.analyzed<br>namespace string not_analyzed yes kube-system<br>pod string not_analyzed yes kube-dns-v9-f0fqw<br>node string not_analyzed yes Kubernetes<br>node name<br>replication_cont string not_analyzed yes kube-dns-v9<br>roller<br>labels.name string not_analyzed yes<br>labels.instance string not_analyzed yes<br>**----- End of picture text -----**<br>



![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0008-00.png)


**----- Start of picture text -----**<br>
labels.version string not_analyzed yes<br>labels. string not_analyzed yes<br>component<br>labels. string not_analyzed yes<br>managed_by<br>labels.part_of string not_analyzed yes<br>**----- End of picture text -----**<br>


## **Request bucket (request_obj)** 

This is a nested JSON called request_obj. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0008-03.png)


**----- Start of picture text -----**<br>
field name type indexing sort/aggregations example description notes<br>cn string not_analyzed yes<br>concur-referer string not_analyzed yes<br>host string not_analyzed yes since ~ late November 2023<br>path string not_analyzed yes<br>uri string not_analyzed yes<br>route string not_analyzed yes<br>method string not_analyzed yes<br>query string analyzed (80 tokens) no<br>body string analyzed (80 tokens) no<br>**----- End of picture text -----**<br>


## **Response bucket (response_obj)** 

This is a nested JSON called response_obj. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0008-06.png)


**----- Start of picture text -----**<br>
field  type indexing sort example description notes<br>name /aggregations<br>content string analyzed  no Caution : our service (& data) are all open to anyone in Concur<br>(80 tokens) network (except SEAG env). Please consider what you put in<br>here.<br>status string not_analyzed yes success<br>status_c long yes 200<br>ode<br>**----- End of picture text -----**<br>


## **Headers data bucket (headers_data)** 

This is a nested JSON called headers_data. All fields in this bucket are keyword (string) type. Here is the list of keys: 

```
accept
accept_encoding
accept_langauge
akamai_origin_hop
cache_control
client_ip
concur_apigateway_is_concur_caller
concur_apigateway_processed
concur_correlationid
concur_forwarded_for
connection
content_length
content_type
dnt
front_end_https
host
http_client_ip
http_referer
http_true_client_ip
http_user_agent
http_x_forwarded_for
path_info
pragma
query_string
remote_addr
request_method
true_client_ip
upgrade_insecure_requests
url
user_agent
via
x_abuse_info
x_edgeconnect_session_id
x_external
x_forwarded_for
x_forwarded_host
x_forwarded_port
x_forwarded_proto
x_mbr_ref_id
x_mbs_ref_id
x_orig_host
x_powered_by
```

## **Error bucket (available ONLY in log index)** 

This is a nested JSON object called error. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0009-03.png)


**----- Start of picture text -----**<br>
field  type indexing sort example description notes<br>name /aggregations<br>id string not_analyzed yes 90c1dbf6-42b9-465b-a805-<br>75ab0c37149e<br>pid string not_analyzed yes  2468<br>type string not_analyzed yes 7<br>cause string not_analyzed yes Caused by: com.concur...<br>message string analyzed (80  no Error message<br>tokens)<br>stacktrace string analyzed (80  no at ...<br>tokens)<br>code string not_analyzed yes<br>source string not_analyzed yes abc ie. roletype that caused the<br>error<br>seen bool yes false<br>**----- End of picture text -----**<br>


handled bool yes true data_path string not_analyzed yes /customFields/3/value/ schema_path string not_analyzed yes "/ab/c/2/d" or ".ab.c[2].d", ... 

## **Exception bucket (exception_obj)** 

This is a nested JSON called exception_obj. 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0010-03.png)


**----- Start of picture text -----**<br>
field name type indexing sort/aggregations example description notes<br>type string not_analyzed yes<br>source string not_analyzed yes<br>message string analyzed (80 tokens) no<br>cause string analyzed (80 tokens) no<br>stacktrace string analyzed (80 tokens) no<br>**----- End of picture text -----**<br>


## Custom Buckets ("MyApp" Buckets) 

Custom buckets are great for [app, service, team]-specific data. Teams/services can request own buckets to fulfill their logging needs. 

Custom Bucket Example: 

`"service_data": { "color": "red", "team": "giants", "value": 42, "foo": "bar" }` Custom buckets has to be separate from general mapping, so that when a change (create/update/delete) is requested, it doesn't affect anyone else or others data. Here we applied naming rule, where each custom bucket is an object located in root level mapping and its name has **_data** suffix (mandatory). 

**Actual custom buckets** : 

Custom buckets for data-2 indexes (same for both: log-2 & metric-2) Custom buckets for txn-2 indexes 

Since **log-2** and **metric-2** indexes are commonly used with their virtual alias **data-2** , we decided to merge log and metric custom buckets definition into one. 

## **Custom Buckets best practices** 

Custom buckets can add great value to specific needs of each team. But before requesting own custom bucket, or extending existing one, please think twice and try to follow these best practices: 

- Overall try to request only custom buckets fields which you really need and it has some business value to your team/service. The more fields, the more resources it takes in Elasticsearch cluster to process it (each indexed field generate its own search index) NEVER request redundant fields. For example, in the root mapping is field **company_uuid** - use that one field, instead of requesting such field in your own bucket (ie. **abc_data.company_uuid** ) Design your fields also as generic as possible. Instead of creating field for each event, rather create one field for event name and another field for event value, like: 

```
// instead of bucket like this:
bad_bucket_data: {
  trip_event: string,
  expense_event: string,
  mobile_event: string,
  dark_event: string,
  whatever_else_event: string
}
```

```
// manage to use better way:
good_bucket_data: {
  event_name: string,
  event_value: string
}
// or, in case you need more events in single log file (ie, dependency)
good_bucket_data: {
  event: string,
  event_value: string,
  dependency_event: string,
  dep_event_value: string
}
```

This way, you'll always have chance to search for your even types and their values. Moreover, you will be able to easily aggregate on event types, what can give you extra value 

Ideally use one or two object levels within your custom bucket. The deeper, the more complex internal processes are created and the more resources are taken 

## **When you need a field to be indexed** 

## This is very important to understand! 

In most cases, users do NOT need their field to be indexed - let me explain why. Whenever a document is retrieved by elasticsearch, it does store source of this document 'as is' in a so called **_source** index. Then elasticsearch goes and check EVERY single field in that document and ONLY in case there is respective mapping definition for the field, it takes its value and store it separately in that field index. This can be later used for searching and/or aggregation. But, whenever you search for your documents, you'll always retrieve the whole document, from the _source index. 

To describe it in a usage form: you need to index only fields that you plan to search or aggregate on it. We did a usage analyses, and from those 3500+ fields (across log and metric buckets), **only about ~200 fields are really used for its purpose** !!! 

## **Custom Buckets mapping data types** 

As you can guess, elasticsearch support all basic data types (string, integer, boolean...). In below table, we introduce some of them, with their limitations and possibilities 


![](logging_docs/markdown_converted/images/3286770416_8555fc9a90d04e5798b89f7ea05f3953-310326-2144-7484.pdf-0011-10.png)


**----- Start of picture text -----**<br>
Data  Description Example Indexed  Purpose Note<br>type as<br>keyword Not analyzed string type. "My  "my  Short string values,  Can request for inner analyzed field.<br>Indexed as one token. Service" service" usually searched for  It is then used as:<br>Lowercased whole value.Used for  field.analyzed<br>aggregating data<br>text Analyzed string type. Each  "My  "my",  Easy search without<br>word (token) is indexed and  Service is  "service",  wildcards for words<br>searchable separately.Only  great" "is", "great" that are present in<br>first 80 tokens are analyzed,  some field.Not<br>rest is skipped.Lowercased usable for<br>aggregations (even<br>not allowed)<br>integer numeric fields. Whole  123 123 Range queries,<br>/long numbers statistical<br>aggregations<br>float numeric fields. Decimal  123.01 123.01 Range queries,<br>/double numbers statistical<br>aggregations<br>bool Boolean fields TRUE true binary field. Rather don't use it, as it is often misused and doesn't assign true/false<br>always the way how users expect. Read more on elastic documentation<br>**----- End of picture text -----**<br>


date date field 

2020-022020-02date ranges, data This is very tricky! because while defining the mapping, user has to 02T02:02: 02T02:02: operations decide what format dates will be in, and then you have to always keep 02.000Z 02.000Z the format. If not kept consistent, users might be seeing very unexpected results.If you need to do some time comparisons or so, we do suggest you use long, and on your end compute time in milliseconds. That will work for you nicely too. 

## **Process to manage Custom Bucket(s)** 

Before requesting ANY change for custom bucket, please read carefully these notes: 

Users tend to request custom bucket for any possible future use (what if?). But with that approach, we ended having 3000+ fields definitions for log index. After analyzing use of these, we found 75% of them were never used, and therefor we did deep cleanup. Therefore: 

think twice before requesting new field for custom bucket, and do NOT request redundant field - ie. which in same or similar form is already available in root fields!! Just for example, we register many named 'company_id' within custom buckets, or many other fields which are representing 'company' value 

Do not request fields to be mapped, which you don't need for search or aggregation Follow Best, resp. Bad practices wiki pages before you do any changes to your log structure 

In order to manage your custom bucket, use this process: 

>> Concur Logging - Service Requests Procedure 

## **Custom buckets regular clean-up** 

Custom buckets definitions tends to grow. Teams usually don't come back to request cleanup themselves. And that leads to a significant resources consumption (memory and CPU usage footprint). Which is not necessary, if most fields from those are not used. 

Elasticsearch API offers fields analyses, and we use it to monitor usage of every single custom bucket. We now perform %-age analyses of NOT used fields from custom buckets and based on the results we do logical clean-up. That means: 

custom buckets that are not used are deleted 

**not used** fields from custom buckets that are used are further analyzed: is it redundant field with some root field (like company_id)?  Deleted does it logically and/or visually belong... TBD 

