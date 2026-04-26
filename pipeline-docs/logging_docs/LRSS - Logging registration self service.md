## **LRSS - Logging registration self service** 

LRSS is a system designed to automate the deployment of logging-related objects through a REST API. It enables teams to manage Elasticsearch watches efficiently across multiple data centers by defining watch configurations in a structured repository. LRSS validates and deploys these configurations via GitHub pull requests, ensuring compliance with metadata and formatting requirements. The system supports dynamic and templated variables for flexibility, provides deployment logs, and integrates with Slack for notifications. It streamlines watch registration and maintenance while enforcing consistency across logging clusters. 

_**Table of content**_ Getting Started Team folder structure Coverage Deployment Objects metadata Templating Elasticsearch objects Context Context Merging Process Default shared variables Team context file Templates of Elasticsearch objects Watches Troubleshooting & Common Issues 

## _**External links**_ 

LRSS Github repo Kibana dashboards docs Elasticsearch watcher docs Official sample watches 

## Getting Started 

Each team should have its forked repository and directory within the LRSS repository where your context/variables and templates are located. Follow these steps: 

1.  Fork the LRSS repository - https://github.concur.com/cia /Logging-Registration-Self-Service 

2.  Create your team directory under _**team-configs**_ Please use a clear name for the team/project. We recommend using your JIRA alias for visibility - but there are no restrictions for the name except allowed characters **[a-zA-Z0-9_-]** You can copy the _**team-configs**_ **/** _**_proto**_ as your starting point 

## Team folder structure 

aggs - _**COMMINT in the near future**_ dashboards - _**COMMINT in the near future**_ mls - _**COMMINT in the near future**_ searches - _**COMMINT in the near future**_ watches - folder with team watch templates context.yaml - team context file 

3.  Update your _**context**_ file and templates for any Elasticsearch objects 

4.  Commit your changes to your forked repository and create a pull request to the original LRSS repository and its master branch 

5.  Wait for the PR to be merged 

## Coverage 

LRSS is currently running in most environments where we are operating our logging service. To 


![](logging_docs/markdown_converted/images/LRSS_-_Logging_registration_self_99aa8285d32d42658158f6088ae1a3d0-310326-2159-7566.pdf-0001-15.png)


**----- Start of picture text -----**<br>
Env. name Auto deploy Proxy req. Email actions<br>AWS ATM Integration integration Yes Yes No<br>AWS ATM USPSCC uspscc No (HSPD-12) Yes No<br>EU commercial eu2 Yes No No<br>US commercial us2 Yes No No<br>APJ commertial apj1 Yes No No<br>China commercial beipr1 TBD Yes Yes<br>**----- End of picture text -----**<br>


## Deployment 

Our repository is designed for automated deployments, with multiple validation steps to ensure consistency and compliance. The deployment process follows these key steps: 

**Auto merge reqs.** 

## **Automated Deployment Process** 

1.  When a pull request (PR) is created from your forked repository to the main LRSS repository (master branch), automated validation checks are triggered. 

2.  If all validation checks pass, the PR is automatically merged into the master branch. 

3. Once merged into master, the deployment process is triggered, applying the changes to the specified environment(s). 

4. The deployment targets are determined based on the _**metadata.deploy_to**_ values in your configuration. These values must correspond to one of the predefined environment names listed in the table above. 

## **Handling PR Check Failures** 

If any validation check fails, the PR cannot be auto-merged. In this case: 

A manual review by a member of our team is required. 

The reviewer must approve and manually merge the PR before the deployment can proceed. 

This ensures that all changes meet the required standards before being applied. 

## **Special Process for USPSCC (HSPD-12 Compliance)** 

Due to HSPD-12 compliance requirements, deployments to the USPSCC environment follow a stricter approval process: 

1. Changes intended for USPSCC must be merged into the deploy-pscc branch instead of being deployed directly from master. 

2. To facilitate this, a PR from master to deploy-pscc is automatically created whenever changes are merged into master. 

3. A designated reviewer from the responsible authority reviews this PR daily. 

4. Once approved, the reviewer manually merges the PR into deploy-pscc, which then triggers the deployment to USPSCC. 

This process ensures that all changes to USPSCC are reviewed and approved by the appropriate authorities before deployment, maintaining regulatory compliance while keeping the workflow as efficient as possible. 

## **Example of deployment target** 

## **Example: metadata.deploy_to** 

```
{
  # body of Elasticsearch object
  "metadata": {
    # Other metadata
    "deploy_to": [
      "integration",
      "us2"
    ]
  }
}
```

## Objects metadata 

Every template must include mandatory metadata fields to ensure proper identification of resources and their owners. These fields help track where the resource originates from and who is responsible for it. 

## **Required Metadata Fields:** 

- GitHubRepository - The forked repository where the resource originates. JiraAlias - The Jira alias of the owner team. 

## **<team_name>/context.yaml** 

```
---
_metadata:
    GitHubRepository: cia/Logging-Registration-
Self-Service
    JiraAlias: LAMA
    JiraComponent: Logging
    RoleType: lssl
```

- JiraComponent - The Jira component associated with the owner team. 

RoleType - The role type of the resource or team. 

## **Defining Metadata in Templates and Context Files** 

These metadata fields can be defined in two ways: 

Per Resource - Directly inside the object template. Globally in Context - Inside your team’s context.yaml file under the _metadata root key. 

## **Example of an object template metadata** 

```
{
        "metadata": {
                "RoleType": "lama"
        }
}
```

If a resource template does not contain any of the required fields, the system automatically pulls those values from the team context file. 

However, if a field is explicitly defined in a resource template, it takes precedence over the context file value. 

This ensures that every resource has the necessary metadata while allowing flexibility in defining these values either globally or at the individual resource level. 

In this example the rendered object will look like as follows; 

**Example of an object template metadata** `{ "metadata": { "GitHubRepository": "cia/LoggingRegistration-Self-Service", "JiraAlias": "LAMA", "JiraComponent": "Logging", "RoleType": "lama" } }` 

## Templating Elasticsearch objects 

Templating enables dynamic content generation by using templates with placeholders which are replaced with actual values from a provided context. This allows for flexibility, as the same template can be reused with different data sets. The context supplies the necessary data, ensuring that variables are populated correctly based on the environment in which the template is deployed. 

For object templating, we use the standard Jinja2 templating engine but with custom opening and closing tags - example: _**{{: variable_name :}}**_ - to prevent conflicts, as Elasticsearch reserves the default Jinja2 syntax for its own variable references. 

## Context 

The **context** contains dynamic data that is injected into templates. It is both **team-specific** and **environment-specific** , ensuring that configurations adapt to different deployment scenarios. 

To understand how the context is created, it’s important to note that **two context files are involved** : 

- **`_defaults/context.yaml`** Contains default variables defined globally. **`<team_folder>/context.yaml`** Contains team-specific variables, managed by each team. 

## **Context Merging Process** 

The final context used for deployment is built through a **layered merging process** , applying values in the following order: 

1. **Start with an Empty Context** Initialize an empty dictionary. 2. **Load Global Default Variables** Merge values from the _**`_all`**_ key in _**team-configs/_defaults/context.yaml**_ . 3. **Apply Environment-Specific Defaults** Override with values from the key matching the target environment in _**team-configs/_defaults /context.yaml**_ . 

4. **Apply Team-Specific Global Variables** Merge values from the _**_all**_ key in _**team-configs/<team_folder>/context.yaml**_ . 5. **Apply Team-Specific Environment Variables** Override with values from the key matching the target environment in _**team-configs /<team_folder>/context.yaml**_ . 

Each step progressively refines the context, ensuring that environment-specific and team-specific configurations are correctly applied. 

## **Default shared variables** 

As mentioned above, default shared variables are loaded and can be find in _**team-configs/_defaults/context.yaml**_ file of the LRSS repository. There is a list of the most significant ones: 

shortEnvName - short environment name longEnvName - long environment name index.log - index pattern of log-* data index.metric- index pattern of metric-* data index.data- index pattern of data-* data proxy.host - host for env. proxy proxy.port - port for env. proxy 

You help us to extend the list. 

## **Example usage** 


![](logging_docs/markdown_converted/images/LRSS_-_Logging_registration_self_99aa8285d32d42658158f6088ae1a3d0-310326-2159-7566.pdf-0003-21.png)


**----- Start of picture text -----**<br>
Example of default usage<br>{<br>#...<br>  "actions": {<br>        "notify-slack": {<br>            "throttle_period_in_millis": 1800000,<br>            "slack": {<br>                "proxy": {<br>                    "host": "{{: proxy.host :}}",<br>                    "port": "{{: proxy.port :}}"<br>                },<br>                "message": {<br>**----- End of picture text -----**<br>


```
                    "to": [
                        "{{: notify_slack.main :}}"
                    ],
                    "attachments": [
                        {
                            "color": "warning",
                            "title": "{{:
longEnvName :}} warning",
                            "text": "{{ctx.payload.
hits.total}} docs in log index"
                        }
                    ]
                }
            }
        }
    }
# ...
}
```

## **Team context file** 

Context file has a strict root key rules, there can we only _**_metadata, _all**_ and keys of _**supported environment names**_ . Everything else is skipped during context creation. 

## **<team_name>/context.yaml** 

```
---
_metadata:
    GitHubRepository: <org/project>
    JiraAlias: <MYJIRA>
    JiraComponent: <MyComponent>
    RoleType: <MyRoletype>
_all: # team shared variables
    key_1: value_1
    key_2: value_2
    key_3: value_3
integration: # Integration specific values
    key_2: value_int
        key_3: value_int_2
uspscc: # USPSCC specific values
    key_2: value_pscc
        key_3: value_pscc_2
eu2: # EU com. specific values
    key_2: value_eu
us2: # US com. specific values
    key_2: value_us
apj1: # APJ com. specific values
    key_2: value_jap
```

## Templates of Elasticsearch objects 

## **Watches** 

## **Deactivating a Watch by Environment** 

You can control whether a watch is active or inactive in specific environments using the state object. 

By default, a watch is enabled in all environments listed in metadata.deploy_to. 

To deactivate a watch in specific environments, add those environments to the state object and set them to "false". If _**state._all**_ is set to "false" globally, the watch is deactivated in all environments. 

**Example: metadata.deploy_to** 

```
{
  "metadata": {
    "deploy_to": [
      "integration",
      "us2"
    ]
  },
  "state": {
    "us2": false
  }
}
```

This configuration deploys the watch to both Integration and US com., but deactivates it in the second one. 

## Troubleshooting & Common Issues 

We are here for you! If any problems or questions arise, please don't hesitate to contact us via the #ask-logging channel on Slack. 

