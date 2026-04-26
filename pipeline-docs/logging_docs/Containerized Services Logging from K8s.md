## **Containerized Services Logging from K8s** 

We provide "out of the box" logging for applications running in containers hosted on Concur K8s/Tectonic infrastructure. 

The applications just need to send logs to stdout/stderr, properly formatted, and logs are automatically collected and shipped to corresponding logging service in corresponding cloud environment. 

K8s Team run **kube-logging (fluentbit)** as a DaemonSet (meaning its running on each and every K8s worker node), which automatically reads all pods logs and ships them. 

See Kube-logging for details. 

## How to send logs from K8s tenant application to Logging Platform 

1.  Log to **stdout** or **stderr** 

2.  User need to use correct JSON format and correct JSON structure as required by logging service, see Application Log Format (v2) Note: if you use incorrect log format, your logs won't appear in Kibana at all, or you can find them in Kibana's "trash" index 

## Where do I find my logs? 

Use the corresponding Kibana, in corresponding cloud environment (see Service Endpoints - Logging Service), and search for your kubernetes. namespace or roletype. 

