# Jobs creation scenario

After testing runners autoscaler tool with escalator  the next behaviour was investigated, when despite the fact maximum number of runners was set to **10**, actually there was **15 ONLINE** runners, which is more than expected.

_runners autoscaler configMap:_

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: runners-autoscaler-config
  namespace: bitbucket-runner-control-plane
data: 
  runners_config.yaml: |
    constants:
      runner_api_polling_interval: 20
    ...
    groups:
      - name: "Runner group 1"
        ...
        strategy: "percentageRunnersIdle"
        parameters:
          min: 1
          max: 10
          scale_up_threshold: 0.5
          scale_down_threshold: 0.2
          scale_up_multiplier: 1.5
          scale_down_multiplier: 0.5
```

## General description

With initial setup of  runners autoscaler tool we have the next infrastructure:

- **1** k8s node,

- **1** runner online with **1** k8s job,

- escalator pod to create additional k8s nodes if required.

_escalator configMap:_

```yaml
data:
  nodegroups_config.yaml: |
    node_groups:
      - name: "pipes-runner-node"
        ...
        scale_up_threshold_percent: 70
        max_nodes: 5
```

With escalator configMap provided above new k8s nodes will be created after **70%** of memory or cpu will be reached on the k8s node.

**1** runners autoscaler created job take **26%** resources of 1 k8s node and maximum number of the jobs in **1** k8s node is equal to **3** (**78%** of CPU in our case). After that escalator will create a new k8s node, if additional jobs will be created by runners autoscaler tool.

So let's take a look at the next test case.

_Bitbucket pipeline configuration:_

```yaml
pipelines:
  default:
    parallel:
      - step:
          name: Test1
          runs-on:
            - self.hosted
            - linux
          script:
            - echo start
            - sleep 600
            - echo stop
          services:
            - docker
      - step:
          name: Test2
          ... same logic as Test 1
      - step:
          name: Test3
          ... same logic as Test 1
      - step:
          name: Test4
          ... same logic as Test 1
      - step:
          name: Test5
          ... same logic as Test 1
```

According to runners autoscaler tool configMap provided above the expected process should be the next (with **20** sec between iterations):

- _1 iteration_: create runners/jobs from **1** to **2** 

- _2 iteration_: from **2** to **3** 

- _3 iteration_: from **3** to **5** 

- _4 iteration_: from **5** to **10** (this is also expected, because of config)

Also remember that every k8s node could contain only **3** jobs, so it was expected to have **4** nodes (**3**, **3**, **3**, **1** jobs on every node).

But actual behaviour was the next, because of the little time between iterations (**20** sec) configured in runners autoscaler configMap:

- _1 iteration_: passed **ok**,

- _2 iteration_: passed **ok**, 

- _3 iteration_: additional **2** jobs created by runners autoscaler tool (expected), but these jobs are **RED**, because no resources in initial **number 1** k8s node,

- escalator started to create new k8s node (**number 2**), it takes time around **1** minute for the k8s node to be initialised,

- runners autoscaler tool checks the number of Bitbucket API runners with the state **ONLINE**, the number of runners is **3**, because jobs created in **3** iteration are still **RED**,

- _4 iteration_: additional **5** jobs created, with previous **2** jobs it is now **7 RED**, because no resources in initial (**number 1**) k8s node available, and new k8s node (**number 2**) created by escalator is not initialised yet,

- _5 iteration_: again additional **5** jobs created. The number of the Bitbucket API runners with a state **ONLINE** is still **3**, but should be **10** (according expected _iteration 4_). With previous **7** jobs there are **12 RED** jobs now,

- **number 2** k8s node initialised and become available,

- **4 RED** jobs are **GREEN** now. Altogether we have **2+4 GREEN** jobs (**2** k8s nodes with **3** jobs in each node) , **12-4 RED** jobs,

- escalator started to create new k8s node (**number 3**), it takes time around **1** minute for the k8s node to be initialised,

- _6 iteration_: additional **5** jobs created, The number of the Bitbucket API runners with a state **ONLINE** is **6**, but should be **10** (according expected _iteration 4_).  With previous **8** jobs we have **13 RED** jobs now,

- _so on and so on_: it will be actual **5** k8s nodes in a cluster, instead of expected **4**. And **15 GREEN** jobs (**5** k8s nodes with **3** jobs in each node) instead of expected **10**. There could be even more k8s nodes but configured limit of **5** nodes in escalator configMap was reached.

## Conclusion

Runners autoscaler tool in current logic implementation will create new runners until the desired number of Bitbucket API runners with the state **ONLINE** will be reached.

Let’s describe the _general negative case_:  no free resources in k8s node → newly created jobs are **RED** because of this → linked Bitbucket API  runners to these jobs will not have the state **ONLINE** →  runners autoscaler tool will try to create more and more jobs/runners until it reached the infrastructure limit of Bitbucket API runners (currently **100**).

There is no solution of this issue in a current state of development. Our team will work on it to provide a fix in a future releases. To temporary fix this issue do not set value of `runner_api_polling_interval` less than **120** sec in configMap `runners_config.yaml` in `config/runners-autoscaler-cm.yaml` file.
