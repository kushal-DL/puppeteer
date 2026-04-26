## **Watcher actions** 

Notify users options Email action Slack action PagerDuty action Microsoft Teams Action 

This is crucial part of watcher, to properly react on the situation. There are few possible action types: 

create a log about it - doesn't have any value for users 

index document(s) - used mostly by aggregation type of watches 

fire webhook event - mostly used for slack and pagerduty to notify users. There were many problems using this one due to security and proxies setup, and we do not suggest to use it as the support is heavily inconsistent across environments. It make sense only in some special cases, not discussed here **notify users/owners** - we will discuss options and possibilities for this below, as this is the most wanted part! For USPSCC/Integration/US2/EU2/ see docs at Watcher Management Process [ DEPRECATED PAGE] 

## Notify users options 

## **Email action** 

This was the most common way of sending alerts, currently being replaced more by slack action. Email action require support for SMTP server in the environment and output of this action is email (basic or HTTP) sent to one or more recipients. It is allowed to send emails ONLY to these domains: [*. concur.com, *.sap.com, *.pagerduty.com]. Even though, there is a special action for pagerduty, users often use email action, to fire PD. 

**NOTE: SMTP is not officially supported in all ATM environments, and therefore email action might not work there!** We are working on it with IOPS teams... 

Email action example: 

```
"actions": {
    "notify_email": {
        "email": {
            "body": {
                "html": "put html code here to show in the email body"
            },
            "profile": "standard",
            "subject": "Watcher Alert subject - make sure to include environment here",
            "to": [
                "first.last@sap.com"
            ]
        }
    }
}
```

## **Slack action** 

Currently most used action, as well supported in all environments. You can easily configure visual messages, and it is very simple to use. **Proper proxy has to be setup!** otherwise your slack message might not arrive! 

Slack action example: 

```
"actions": {
    "notify-slack": {
        "slack": {
            "message": {
                "attachments": [
                    {
                        "color": "warning",
                        "title": "env Watcher: my alert",
                        "text": "This is my alert message text..."
                    }
                ],
                "to": [
                    "#my-slack-group"
                ]
            },
            "proxy": {
                "host": "proxy.service.cnqr.tech",
                "port": 3128
            }
        }
    }
}
```

## **PagerDuty action** 

PagerDuty can be reached by email, but this is more preferred way of firing PDs. **Proper proxy has to be setup!** otherwise your PD might not be fired! In order to allow API PD firing, your service has to have API integration created, where you'll get INTEGRATION_KEY which you will use in below example. 

PD Generic API integration is done in PagerDuty: 

find and select your service click Integrations TAB either create new Events API v1 integration, or once created, copy the Integration key 

PagerDuty action example: 

```
"actions": {
    "notify_pager": {
        "throttle_period_in_millis": 300000,
        "webhook": {
            "body": "{\"client_url\": \"\",\"service_key\": \"INTEGRATION_KEY\",\"event_type\": \"trigger\",\"
description\": \"[watcher ENV] My Alert ...\",\"client\": \"Elasticsearch Monitoring Service\", \"
escalation_path\": \"\"}",
            "connection_timeout_in_millis": 30000,
            "headers": {
              "Content-Type": "application/json"
            },
            "host": "events.pagerduty.com",
            "method": "post",
            "params": {},
            "path": "/generic/2010-04-15/create_event.json",
            "port": 443,
            "proxy": {
              "host": "proxy.service.cnqr.tech",
              "port": 3128
            },
            "read_timeout_millis": 30000,
            "scheme": "https"
        }
    }
}
```

## **Microsoft Teams Action** 

Microsoft Teams is becoming more commonly used for watcher notifications. First, in Microsoft Teams, the user needs to create an incoming webhook for the specific channel they wish to receive alerts in. Make sure to copy the webhook URL and save it for later use. Next, add a webhook action into the watcher similar to the one listed below. The Microsoft Teams webhook URL will be used to fill the "scheme," "host," and "path." 

Test the webhook in the Simulate section of the watcher Click "execute" under the Action modes section Simulate Watch and check to see if the message was received in the specified MS Teams channel 

Microsoft Teams action example: 

```
"actions": {
        "notify_msteams": {
                "webhook": {
                "scheme": "https",
                "host": "sap.webhook.office.com",
                "port": 443,
                "method": "post",
                "path": "/webhookb2/ee3deda6-7596-403c-aae3-ae295c2ac241@42f7676c-f455-423c-82f6-dc2d99791af7
/IncomingWebhook/3a297d1c8ccc4b5790213cb37bef8c9b/cc5021dd-f587-44a4-9f76-9501e95529eb",
                "params": {},
                "headers": {},
                "body": "{\"text\": \"{{ctx.payload.hits.total}}\"}"
                }
        }
}
```

