## **Logging - Best Practices and Hints** 

## On this page 

On this page Queries hints & recommendations Always query your data with time range query/filter KQL is now the default query Use Saved Sessions in Kibana for querying more days of data Data tiers - hot/cold/frozen Data Tiers Performance Track total hits Total hits path Log content Best Practices Don’t log sensitive data Avoid excessive logging Don’t use cryptic log messages Choose the correct logging level per environment Use correlation_id UUID identifier to help track operations across multiple systems Use good patterns and make it easy to read Design your kibana content properly and efficiently 

## Queries hints & recommendations 

## **Always query your data with time range query/filter** 

If you run your query (over REST API, DevTools or in watch), make always sure you use time range query/filter, otherwise your query might overload the whole cluster. Specially Cold and Frozen tiers. When these are overloaded with unnecessary queries, other users might be affected as well, and their queries might timeout. 

```
POST *:log-2/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "@timestamp": {
              "gte": "now-30m",
              "lte": "now"
            }
          }
        },
        {
          "query_string": {
            "query": "application: myApp"
          }
        }
      ]
    }
  }
}
```

## **KQL is now the default query** 

Kibana Query Language (KQL) was introduced in v6.3 as an opt-in. It is the default query language since v7, that brings some benefits over Lucene syntax. But users will need to do a bit of learning. Eventually opt-in to use Lucene Syntax. All saved searches will continue to work. 

Showing few examples of differences: 

> **Suggestions** : KQL enables getting suggestions for fields, values, and operators as you type your query **Operators** : among others, Lucene supports only uppercase (AND, OR, NOT) operators, whereas KQL works the same with upper- or lower-case (and, AND, or, OR, not, NOT) 

**Exists** : In Lucene: **_exists_:field_name** , in KQL: **field_name: *** 

## **Use Saved Sessions in Kibana for querying more days of data** 

For Long-running searches (search that process huge amount of data or data from frozen tier - typically searching in data older than 5d), Elasticsearch has a built in Async search. 

After you execute ANY query in Kibana (whether it is in Discover tab or Dashboard), Kibana send a request to elasticsearch which timeout within 2 minutes. 

If you don't receive your data (timeout), you rather save your session and review the data later (once it is all loaded on background - it can take 5-20 minutes): 

1.  Click on the clock icon on top left: 


![](logging_docs/markdown_converted/images/Logging_-_Best_Practices_and_Hin_5d8cc689fddf48d1a453b60d2f0d5c57-310326-2157-7550.pdf-0002-06.png)


2.  Save session. You can name your session for easier finding (I suggest you put your initials as a prefix): 


![](logging_docs/markdown_converted/images/Logging_-_Best_Practices_and_Hin_5d8cc689fddf48d1a453b60d2f0d5c57-310326-2157-7550.pdf-0002-08.png)


3.  To review your sessions: 

   - a.  Open Stack Management 


![](logging_docs/markdown_converted/images/Logging_-_Best_Practices_and_Hin_5d8cc689fddf48d1a453b60d2f0d5c57-310326-2157-7550.pdf-0002-11.png)



![](logging_docs/markdown_converted/images/Logging_-_Best_Practices_and_Hin_5d8cc689fddf48d1a453b60d2f0d5c57-310326-2157-7550.pdf-0003-00.png)


**----- Start of picture text -----**<br>
b.  Find your session in Search Sessions<br>**----- End of picture text -----**<br>


## **Data tiers - hot/cold/frozen** 

Elasticsearch v7 within Elastic Cloud, they support more naturally data tiering. It means, we can hold hot data (ingestion, heavy disk operations and searches for last few hours) on super fast and most expensive hardware (AWS: c6gd). After HOT tier, we move data to so called cold tier, where data are still stored on fast SSD drives, but with less CPU cores per GB and also without replicas (replicas are stored in S3 - so HA is achieved). For this tier, we use much cheaper hardware /GB (AWS: i3en). Finally, data which are older than 8d are only rarely queried, and Elastic Enterprise license allow us to store them as a searchable snapshot in S3. 

This architecture gives us much more value for significantly decreased price. But it also means, response for searching older data is much longer. 

## **Data Tiers** 

hot: up to 4h of data, store primary+replica cold: up to 5d of data, primary on SSD, replica in S3 frozen: >5d and till data retention, only primary and in S3 

## **Performance** 

Measured performance on typical query with simple aggregation (like data histogram) - response times: 

hot: < 5 s cold: < 20 s frozen: not cached (first query): < 5 m cached (follow-up query): < 20 s 

_NOTE: these above numbers are based on real measurement. However, if you use async_search (resp. Saved sessions), the search might take even up to 20-30 minutes. This is a_ _**feature** of the Frozen tier & async search. So instead of overloading the cluster, the search is done on much lower pace and allow many more consecutive searches without any damage_ . 

## **Track total hits** 

Heavily used feature - tracking total hits for the query. 

Generally the total hit count can’t be computed accurately without visiting all matches, which is costly for queries that match lots of documents. The **track_t otal_hits** parameter allows you to control how the total number of hits should be tracked. Given that it is often enough to have a lower bound of the number of hits, such as "there are at least 10000 hits", the default is set to 10,000. This means that requests will count the total hit accurately up to 10,000 hits. It is a good trade off to speed up searches if you don’t need the accurate number of hits after a certain threshold. 

Add **track_total_hits: true** to your query **ONLY** if you need to track exact number of total hits which is higher than 10000: 

```
POST *:metric-2/_search
{
  "track_total_hits": true,
  "query": {
    ...
  }
}
```

For example, if you use total hits in your watch in the condition, and your threshold is ie. 1000, then you don't care what is the exact number. However, if you NEED to check, that total hits is for example less then 12345 hits, then use above parameter - otherwise the result will be ALWAYS less. 

## **Total hits path** 

Total hits is often used mainly in watches to compare amount of hits to some static threshold. In the older versions (v5 & v6), users could use path: `ctx. payload.hits.total` . Since v7, the path has changed to `ctx.payload.hits.total.value` . 

NOTE: to make the query (or watcher) backward compatible, you can use switch: `rest_total_hits_as_int: true` , and `ctx.payload.hits.total` will continue to be a number (as in v5) 

## Log content Best Practices 

## **Don’t log sensitive data** 

Whenever is possible, avoid having any kind of sensitive data in your logs Remember all that GDPR work - well don't start leaking out personal data into logs 

## **Avoid excessive logging** 

If 4 log statements will tell the whole story then don't log 20 items Include information that could help you investigate, but don't log anything you don't need Avoid any redundancy in your log Don't log so much that impacts your application's performance Never log in a manner that it causes some other type of side effects 

## **Don’t use cryptic log messages** 

Don't log "Failed", use enough words that everyone knows what happened "File upload failed" 

## **Choose the correct logging level per environment** 

It's great to log at Debug while running your application on your PC or in QA, but not in production 

Rare occasions it makes sense to turn on debug in production for a short timeframe to track down some new serious problem. This should not be business as normal 

Do not use obscure level values, ie. level: 50 

## **Use correlation_id UUID identifier to help track operations across multiple systems** 

The first service that handles Concur request (web, API, event-subscriber, etc) should generate a correlation_id, and pass it to downstream services in the HTTP header ( **concur-correlationid** ). Every service which receives a correlation_id is obligated to use that correlation_id and pass it to next service. If a correlation ID is not provided in the request, the service should generate its own **correlation_id field should be used always when possible, in context of related CONCUR services logs** 

## **Use good patterns and make it easy to read** 

You want to be able to search for the same type of errors in Kibana, so make sure that you will be able to do this by logging with the correct keywords 

## **Design your kibana content properly and efficiently** 

Always think what you really need to visualize and what historical data to show/compare (ie. in Timelions) If possible, use always auto interval. This will adjust automatically for you when you change time range Use offset (in Timelion) very carefully. Be aware about big performance impact on whole cluster, when it needs to cache old (warm) data 

Minimize number of offsets. Ie, instead of comparing last 7 days (one line per each day), isn't it better to compare only with 7d ago? Or is it necessary to compare today with -7d AND -14d AND -28d? 

