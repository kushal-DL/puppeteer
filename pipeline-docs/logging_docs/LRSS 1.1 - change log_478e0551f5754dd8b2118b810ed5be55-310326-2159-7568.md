## **LRSS 1.1 - change log** 

As part of our ongoing commitment to maintaining a stable, efficient, and high-performing service, we are transitioning our LRSS service to run entirely within RPL. This transformation reduces the number of required components, enhancing overall system stability while also leveraging more efficient algorithms to minimize unnecessary call actions. Since this transition required a partial redesign of the service, we also took the opportunity to introduce various optimizations and improvements. These changes will not impact the service from a user perspective, aside from a few minor enhancements that improve the overall experience. 

## Action required 

_**No immediate action is required,**_ the transformation of the user resources is part of our upgrade. 

This update introduces significant changes and affects most of the repository. So, when you update your forked repository from the upstream, expect to see many changes, and we recommend doing so before introducing any new changes to your files. Alternatively, if you don’t have any special configurations in your fork, you may consider deleting and re-forking the repository. In some cases, starting fresh can be the simpler and cleaner approach. 

## **How to update your forks** 

```
# if have not benn done before
```

```
git remote add upstream https://github.concur.com/cia/Logging-Registration-Self-Service
```

```
git fetch upstream
git checkout
git merge upstream/master
git push origin master
```

## What changes 

Renaming folder _**config**_ to _**team-config**_ - the folder where your team and shared definitions are stored Former _**templates.yaml**_ are being renamed to _**context.yaml**_ Variables/context structure: 

## **context.yaml** 

```
---
_metadata:
    GitHubRepository: <org/project>
    JiraAlias: <MYJIRA>
    JiraComponent: <MyComponent>
    RoleType: <MyRoletype>
_all: # team shared variables
    key: value
    key_2: value_shared
integration: # Integration specific values
    key_2: value_int
uspscc:
    key_2: value_pscc
eu2:
    key_2: value_eu
us2:
    key_2: value_us
apj1:
    key_2: value_jap
```

- Add ability for having mandatory metadata defined once in _**context**_ file under the _**_metadata**_ root key Metadata are inserted into objects if the key is missing in template Context metadata cannot overwrite any values existing. 

- Adding support script so you can generate your watches locally and test everything properly scripts/generate_watch.py 

   - scripts/check_team_config.py 

- Adding shared variables, so every team does not have to define the same variable such as _**proxy host**_ and _**proxy port**_ All defaults can be found in _**team-configs/_defaults/context.yaml**_ 

- Simplifying templating and removing _**__datacenter__**_ token - datacenter is implicit based on the deployment target 

## **Before** 

```
# Watch example
{
    "query_string": {
        "query": "{{: __datacenter__.test_query :}}"
    }
}
# Templates.yaml example
---
integration|uspscc|apj1|...:
        test_query: global query
eu2:
    test_query: eu2 specific query
us2:
        test_query: us2 specific query
```

## **Now** 

```
# Watch example
{
    "query_string": {
        "query": "{{: test_query :}}"
    }
}
# Templates.yaml example
---
_all:
        test_query: global query
eu2:
    test_query: eu2 specific query
us2:
        test_query: us2 specific query
```

Logs from the build and deployment can be found in Kibana under Changes made by us to your team configs 

_**templates.yaml**_ renaming to _**context.yaml**_ update the context file so only allowed root key (_metadata, _all, <env_ names>) are present remove __datacenter usage from watch definitions rename elasticsearch_watches to watches 

