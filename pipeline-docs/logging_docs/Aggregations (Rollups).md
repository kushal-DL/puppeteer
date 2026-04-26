## **Aggregations (Rollups)** 

We provide the ability to aggregate data, which are then kept "forever" (in data lifetime context we define "forever" as 5+ years). Aggregations is great way to keep some high-level or important metrics from your data. Typical example could be daily or hourly metrics of submits, errors, events... 

Each aggregation has to contain '@timestamp' bucket with 1h -to- 1d interval (1h, 3h, 12h, 24h | 1d). We ask you to not over-use this service to generate tons of useless data, but instead, just pick-up the value from your data for future reports. Aggregations are generated (computed) by watcher, and stored in special 'agg' index. It is strongly suggested that you execute these watches on daily basis. Ideally in morning UTC hours, and compute data for previous day - see in examples. 

## Features 

## **Aggregate on terms** 

You can include up to 2 terms - aggregate (group) on up to 2 keyword fields. PLEASE, be aware of using terms aggregations on high-cardinality fields. That can end-up generating thousands or even millions of buckets, and there is a limitation of max ~65k buckets, that you cannot go over with chained aggregations. 

Example: search for MyData, compute statistical values (min, max, avg, sum) on duration_ms, aggregate over 1h time period and group by fields: host, method. 

## **Metrics/statistics calculations** 

If your data contains a numeric field, you can include basic stats computation (min, max, avg, sum) on them. 

Other possibility is to calculate cardinality aggregation. 

## Requirements 

time bucket aggregation HAS TO be named ' **@timestamp** ', otherwise your aggregation will be ignored. terms bucket aggregation name will be included in the output doc as the field name - so we suggest to name it the same way aggregations are computed by basic scripts. Any deviations from below templates can cause misusing or missing aggregations 

## Templates 

Watch structure for aggregations is very similar to just normal watch. Final watch has to contain ALL these parts: 

```
{
  "trigger" : {
        ...
  },
  "condition": {
    ...
  },
  "input": {
        ...
  },
  "transform": {
        ...
  },
  "actions": {
        ...
  },
  "metadata": {
        ...
  }
}
```

In following sections, each part will be described separately - but you know, you have to build it all together into a single watch. 

**Trigger** 

In this part, you define how often your watch should be executed! We strongly recommend to use daily basis, and ideally in morning UTC time. It should also correlate to your input - range part. 

We suggest you put in cron type of schedule, which is using system time - UTC. Just be careful, because elasticsearch cron is slightly different to linux cron, and first value is second!!! Following example means: 3:44:00 am UTC every day! Nice example to use (but don't hesitate to change minutes, so that all aggregations are not computed at the same time ) 

```
"trigger": {
  "schedule": {
    "cron": "0 44 3 * * ?"
  }
}
```

## **Condition** 

You most probably want your aggregation watch to execute always, therefore 

```
"condition": {
  "always" : {}
}
```

eventually you can execute action only if some documents were actually found (but is not necessary - the watch will only fail, but will normally run next time): 

```
"condition": {
    "compare": {
        "ctx.payload.hits.total": {
            "gt": 0
        }
    }
}
```

## **Input** 

Input is the part that defines type of aggregation mentioned in Features part on this wiki. All is driven by the aggregations part. But first, you have to have clear query to search for your data. 

Following example shows the maximum allowed for aggregations so that we can explain every part of the query. Other (simpler) possibilities are discussed later 

_NOTE: comments in below example make it invalid JSON (of course). In case you copy-paste it, make sure to remove all of them!_ 

```
"input": {
  "search": {
    "request": {
      "indices": ["*:log-2"],                                        # put index pattern here - which indexes
will be searched
      "body": {
        "size": 0,                                                                 # for aggregations, we
actually don't want any raw data, just aggregations. Size has to be set to 0.
        "query": {
          "bool": {                                                                # bool type of query
followed by must, is required so that we can combine range and query
            "must": [
              {
                "range": {                                                # range query on '@timestamp' field
is a must in v6+ elasticsearch, as we don't use daily indexes anymore!
                  "@timestamp": {
                    "gte": "now-1d/d",                        # this case will be the most common. It simply
defines 'yesterday UTC'. '/d' at the end means, round to day.
                    "lte": "now-1d/d"
                  }
                }
              },
              {
                "query_string": {                                # kibana UI - discover tab uses query_string.
```

```
So it will be 1-to-1 with what you are used to. Be aware to use even double-quotes if needed, they just need to
be escaped '\"'
                  "query": "QUERY TO PROCESS ONLY MY DATA - SAME AS IN KIBANA UI"
                }
              }
            ]
          }
        },
        "aggs": {                                                                # first level aggregation
          "field1": {                                                        # this is name of the aggregation.
You can use whatever name, however this name will be used in output documents for field1 values.
            "terms": {
              "field": "field1",
              "size": 10                                                # top X fields to be processed (order
by count desc). Do NOT put more then 10000
            },
            "aggs": {                                                        # second level aggregation
              "field2": {                                                # this is name of the aggregation. You
can use whatever name, however this name will be used in output documents for field2 values.
                "terms": {
                  "field": "field2",
                  "size": 10                                        # top X fields to be processed (order by
count desc). Do NOT put more then 10000
                },
                "aggs": {
                  "@timestamp": {                                # time aggregation, which is required to be
last bucket aggregation. It's name has to be exactly 'timestamp', otherwise it will be completely ignored
                    "date_histogram": {
                      "field": "@timestamp",
                      "fixed_interval": "1d"                        # put your interval of wish, but between 1h
and 1d. For eventual other values, always reach to Logging team!!
                    },
                    "aggs" : {
                      "myStats" : {                                # name of stats aggregations. Can be of your
choice
                        "stats" : {                                # type of aggregation - only 'stats' is
allowed, resp. only these metrics are taking [min, max, avg, sum, count]
                          "field" : "duration_ms"        # this HAS TO be numeric field, so that these basic
stats can be computed [min, max, avg, sum, count]
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

More input possibilities - examples: 

## **Input without aggregated (terms) fields, calulating cardinality on a company_uuid:** 

```
"input": {
  "search": {
    "request": {
      "indices": ["*:log-2"],
      "body": {
        "size": 0,
        "query": {
          "bool": {
            "must": [
              {
                "range": {
                  "@timestamp": {
                    "gte": "now-1d/d",
                    "lte": "now-1d/d"
                  }
                }
              },
              {
                "query_string": {
                  "query": "QUERY TO PROCESS ONLY MY DATA - SAME AS IN KIBANA UI"
                }
              }
            ]
          }
        },
        "aggs": {
          "@timestamp": {
            "date_histogram": {
              "field": "@timestamp",
              "fixed_interval": "1d"
            },
                    "aggs": {
              "unique_company": {
                "cardinality": {
                  "field": "company_uuid"
                }
              }
            }
          }
        }
      }
    }
  }
}
```

**Input without statistical field (one aggregated field):** 

```
"input": {
  "search": {
    "request": {
      "indices": ["*:log-2"],
      "body": {
        "size": 0,
        "query": {
          "bool": {
            "must": [
              {
                "range": {
                  "@timestamp": {
                    "gte": "now-1d/d",
                    "lte": "now-1d/d"
                  }
                }
              },
              {
                "query_string": {
                  "query": "QUERY TO PROCESS ONLY MY DATA - SAME AS IN KIBANA UI"
                }
              }
            ]
          }
        },
        "aggs": {
          "field1": {
            "terms": {
              "field": "field1",
              "size": 10
            },
            "aggs": {
              "@timestamp": {
                "date_histogram": {
                  "field": "@timestamp",
                  "fixed_interval": "1d"
                }
              }
            }
          }
        }
      }
    }
  }
}
```

**Input for simple counter (neither statistical field nor aggregated field)** 

```
"input": {
  "search": {
    "request": {
      "indices": ["*:log-2"],
      "body": {
        "size": 0,
        "query": {
          "bool": {
            "must": [
              {
                "range": {
                  "@timestamp": {
                    "gte": "now-1d/d",
                    "lte": "now-1d/d"
                  }
                }
              },
              {
                "query_string": {
                  "query": "QUERY TO PROCESS ONLY MY DATA - SAME AS IN KIBANA UI"
                }
              }
            ]
          }
        },
        "aggs": {
          "@timestamp": {
            "date_histogram": {
              "field": "@timestamp",
              "fixed_interval": "1d"
            }
          }
        }
      }
    }
  }
}
```

## **Transform** 

Transform part is responsible to take query output and format it properly for agg index. Format is given: 

```
"transform": {
  "script": {
    "id": "aggregations_parsing",                # this is pointer to a painless script which computes output
    "params": {
      "aggregation_name": "my_agg",         # define agg_name
      "interval": "1d"                                        # this is not functional value, but is included
in output documents, and should be same as in query part
    }
  }
}
```

## **Actions** 

```
"actions": {
  "index_payload": {
    "index": {
      "index": "agg"
    }
  }
}
```

## **Metadata** 

This part is not required by aggregations, you can have your own parameters or metadata here. Some of our automation tools however, may require values here - so it is to follow-up on how you manage your watches. 

## How to view aggregated data 

Each aggregation definition is stored internally as a watch definition, with an action to index the result of defined aggregation query.  All the aggregation jobs run once per day, over the night, when service is under low load. 

Once your aggregation is run, you can find your definition on Aggregation.Main dashboard, or you can search for it in Discover tab. 

You can find your aggregated data in Kibana under the ***:agg** index patterns, and you can create KIbana dashboards to visualize the values. Sample Kibana dashboards: 

CIA_top20_roletypes 

