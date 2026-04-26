## **Application Security Logging (v1)** 

The shared responsibility model Data processing Data format Data verification in Integration References 

These application messages goes through an S3 bucket into **Splunk** , **not** into **Kibana** . (The only exception is in AWS Integration, where we are allowed to ingest these data - to make it easier to users to verify their data compliancy) 

## The shared responsibility model 

**The Logging team do maintain** : 

ingestion pipeline (Logstash) 

**The Logging team doesn't maintain** : 

the message format the S3 bucket the Splunk collectors 

## Data processing 

The intermediate Logging Service ingestion software (Logstash) only do that data processing with these messages: 

**Drop** message when: 

it doesn’t look like a JSON ( `/^\s*\{.*\}\s*$/` ) at all 

**Trash** message into Logging Service index trash when: 

invalid JSON no / invalid / unsupported field **`type`** no / invalid / unsupported field **`data_version`** 

**Alter** message when: 

no/invalid field **`@timestamp`** => add/fix it with the actual time JWT tokens ( `/(eyJhbGciOi|eyJ0eXAiOiJKV1Qi|eyJraWQiOi)[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+/` ) found => mask them 

all the time => remove fields **`type`** and **`data_version`** _(not needed for next processing)_ all the time => add fields **`@env`** and **`@by`** field **`client`** is present and its a valid IP address => field **`client_geo`** is populated with sub-fields: **`location`** (f.e. `{"lat": 47.6062, "lon": -122.3321}` ) **`country`** (f.e. `US` ) 

## Data format 

Data format was developed by Talbot, Mark and it's stored and maintained externally at https://github.concur.com/ap/proposals/blob/master/appsec-logging /README.md. 

## Data verification in Integration 

Data owners can verify their appsec_event data in _**Integration**_ in **two** different ways: 

we ingest these data into Logging Service with shorten retention of 1w. To search for the data, select **log-2** index-pattern, and search for: 

```
tags: _appsec
```

search in central S3 bucket: concur-devtest-central-logs. Your data are either in _exported_ or _internal_ directories: **exported** : this is used if company_uuid field is present and is not empty, and category value is one of these: ("authz_failed", "authz_successful", "authn_failed", "authn_successful", "config_created", "config_updated", "config_removed", "user_auth_changed", "user_created", "user_deactivated", "user_reactivated", "user_login", "user_logout", "user_permissions_changed") 

**internal** : ANY other appsec_event data 

## References 

AppSec Logging Requirements/Guidance https://github.concur.com/ap/proposals/blob/master/appsec-logging/README.md Application Security Logging Requirements 

