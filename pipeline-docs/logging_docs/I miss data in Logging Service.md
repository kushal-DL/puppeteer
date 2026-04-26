## **I miss data in Logging Service...** 

Possible problems: 

Delayed data Partial data outage - from k8s Search problems Mapping problem Trashing problem 

There are various possible reasons why users can miss their data. This wiki page will help you identify what might be the reason why you don't see the data you expect. Please, exercise all examples here and follow given suggestions to find/fix the problem. 

## Delayed data 

## Description: 

Majority of the data (usually all logs from k8s, and some applications) are ingested through S3. We use AWS S3 as a queue mechanism. These might naturally get delayed when some teams/applications create a bursts of logs - until our data processor layer scale-up and consume all load above average. 

## Validate: 

search for your older data, and check, if they contain `s3i` value in the field `@by` . If YES then your data are being ingested through s3 - continue search for last occurrence of your data - it should be minutes or max hours back, not days 

once you find the minute when the load dropped down, zoom the view (time range filter) in to show about +- 15 minutes around that time refresh the search every 2 minutes and 

if you see that your data are going in - they are just delayed. Otherwise it is some different problem 

## Actions: 

You recognized delayed data - what to do now? 

Delays up to 10 minutes happen quite regularly. We can see them about 2-3x a day. 

If you see delay longer than 1 hour, and you are concerned about the situation, you can ping us to **#ask-logging** slack channel and describe the details. We will check it and let you know more details about the situation and approximate estimate when it will be resolved 

## Partial data outage - from k8s 

## Description: 

You can see (significant) decrease in your data load and your application is running in k8s. K8s team use fluentbit data shippers which from time to time can get stuck and stop sending data from one or more hosts. This is usually happened when that shipper is overloaded by HUGE log documents (not amounts, but big single documents) 

## Validate: 

search for your data in the discovery tab. Zoom in to the timeframe where you can see the drop in the volume of your data visualize histogram per `host` . Click on the field `host` in the left pane, click on Visualize button. Once data are loaded, click on the visualization in the bottom: Over time (that will show the histogram) 

you should see a correlation between the drop of your data and some host stopped reporting data completely 

## Actions: 

ping k8s team on slack channel: #ask-k8s, saying that you have a suspicion about fluentbit failure on a particular host 

## Search problems 

## Description: 

Your query doesn't return any data or data you expected. 

## Validate: 

You wrote a new query but it doesn't return what you've expected. You know there are your data, just your query doesn't return them 

## Actions: 

These are few of many possible reasons what could be wrong: 

- Be aware about querying differences between KQL and Lucene. In v7 kibana, you can select which one you want to use (right next to the search box), in v8, KQL is used by default. Few notes about KQL even here: Logging - Best Practices and Hints#KQLisnowthedefaultquery. There are two types of string fields and they behave differently to search query: 

   - **keyword** : the whole value is a single token, and you have to search for the whole token here. You need to use wildcard if you know just part of the token **text** : (or analyzed string) every word is a separate token. We index only first 80 tokens (means, anything after that is stored, but not indexed for search!!). 

## Mapping problem 

## Description: 

Users often misuse mapped fields for different purpose, or mistakenly add value with different type. There are three difference scenarios that can happen: 

If a value can be cast to the defined mapping, it is casted and properly indexed. Examples: boolean or numeric - to the string field "123" (means string) - to numeric field Value cannot be cast - this field is completely ignored - not indexed. Means, it is not searchable Examples: "123a" - to the numeric field 123.45 (float) - to an integer type "I am a human" (string) - to a boolean type Primitive types (including String) to an object or vice-versa. This is a fatal issue, and the whole document will be rejected by elasticsearch Examples: { "name":"foo", "type":"bar"} - to a string field "I am human" - to an object field 

## Validate: 

Check your original document for existence of such mistype with Application Log Format (v2) or custom buckets definitions 

## Actions: 

fix your code, to properly map your data as they should be 

## Trashing problem 

Description: 

We require specific format of the data in order to accept them. We also have set of required fields - like: application, roletype, data_version, type (search for more at Application Log Format (v2)). If you miss any of these required fields, your document will be send to the trash index. Another example would be @timestamp field out of range. We accept only timestamp between -23h & +1h from now (it is the moment when our logstash process data. For log data, we also expect proper value in the `level` field: 

[fatal|panic|emerg|alert|crit|err|warn|notice|info].* if (is Numeric) level >= 20 

## Validate: 

in Kibana, Discovery Tab. Switch the index pattern to the `*:trash` and search for your roletype data (we index only few very basic fields in the trash index) 

## Actions: 

fix your data generation, to include all required fields or their proper values. 

