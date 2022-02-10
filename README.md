# Bitbucket Runner setup and scale script

Automate routines for Bitbucket Pipelines [self-hosted Runners][runner]


### When to use this tool?
Use this tool to set up and scale Bitbucket self-hosted runners on your own infrastructure.

### What problem does it solve?
This tool allows you to

- avoid manual setup runners in the Bitbucket UI.
- setup multiple runners at once.
- use the provided functionality for the file-based configuration, i.e., all the settings you provide in the config file.
- autoscale runners according to the current workload in the build.

### About the Bitbucket Runner
You've always been able to execute CI/CD workflows via Bitbucket Pipelines using Atlassian's infrastructure. This is the easiest way to use Bitbucket Pipelines because you don't need to host or manage any servers. We host it and manage it for you. But sometimes you need more control of your hardware, software, and the environment your builds are executed into. For example, you may need builds to access internal systems that are behind the firewall, or configure your hardware with more memory to run complex builds.

Runners allow you to execute your pipelines builds on your own infrastructure, so you have more control over your server configurations and budgets.
Here are some of the benefits of using runners.

- **Custom build configurations:** Runners allow you to configure your hardware for different types of builds. For example, if you have resource-intensive builds, using hardware with more memory can improve build execution time.
- **Access internal applications or databases:** When running pipelines on Atlassian's infrastructure, we cannot access your internal systems. If you need to run integrations tests against your internal databases or applications, you can do so with runners. Since these runners are hosted/managed by you, you can provide any access needed to internal services.
- **Hybrid workflows:** You can optimize your resources by using self-hosted runners with custom configurations for builds that require it and use Atlassian's infrastructure for other jobs. When using your own runners, we don't charge you for build minutes consumed by your runner.


### Limitation

This script sends requests to the BITBUCKET API in scale runners up and down.
Make sure you are aware of the [BITBUCKET API request limits][BITBUCKET API request limits].

## Prerequisites
- BITBUCKET_USERNAME and [BITBUCKET_APP_PASSWORD][BITBUCKET_APP_PASSWORD] (base64 representation with repository:read, workspace:read, runner:write permissions) should be created and passed in `config/runners-autoscaler-deployment.yaml`
- [optional] setup [kubernetes-dashboard][kubernetes-dashboard] to monitor your cluster

- [optional] details how to [set up AWS EKS cluster with eksctl cli][setup cluster eksctl]
  ```
  eksctl create cluster --name ${NAME_CLUSTER} --version 1.21 --region us-east-1 --zones us-east-1b,us-east-1c --nodegroup-name ${NODE_GROUP_NAME} --node-type t3.medium --nodes 2 --nodes-min 1 --nodes-max 2
  ```

## How to run

### Deployment (in Kubernetes cluster)

Create in `config/` folder three files:

`config/runners-autoscaler-rbac.yaml`,

`config/runners-autoscaler-cm.yaml`,

`config/runners-autoscaler-deployment.yaml`

based on templates provided inside this folder. 

Fill them with needed variables (these variables decorated with `<...>` inside template files).

Next run commands below: 
```
# Build the docker image
docker build -t bitbucketpipelines/runners-autoscaler .

# Create namespace
kubectl apply -f config/runners-autoscaler-namespace.yaml

# Create RBAC configuration
kubectl apply -f config/runners-autoscaler-rbac.yaml

# Create config map - modify to suit your needs
kubectl apply -f config/runners-autoscaler-cm.yaml

# Create deployment
kubectl apply -f config/runners-autoscaler-deployment.yaml
```



## Runner config details
In `config/runners-autoscaler-cm.yaml` you can tune `runners_config.yaml` parameters

```yaml
config:
  - name: "Runner repository group"       # Name of the Runner displayed in the Bitbucket Runner UI.
    workspace: "myworkspace"              # Name of the workspace the Runner is added to. 
    repository: "my-awesome-repository"   # Name of the repository the Runner is added to. Optional: Provide the repository name if you want the Runner to be added at the repository level.
    labels:
      - "demo1"                           # Labels for the Runner.
      - "test2"                           # Labels for the Runner.
    namespace: "runner-group-1"           # Kubernetes namespace to set up the Runner on.
    strategy: "percentageRunnersIdle"     # Type of the strategy workflow.
    parameters:
      min: 1  # recommended minimum 1 must be in UI to prevent pipeline fails, when new build is starting
      max: 10  # 
      scaleUpThreshold: 0.8  # The percentage of busy runners at which the number of desired runners are re-evaluated to scale up
      scaleDownThreshold: 0.2  # The percentage of busy runners at which the number of desired runners are re-evaluated to scale up
      scaleUpMultiplier: 1.5  #  scaleUpMultiplier > 1  speed to scale up
      scaleDownMultiplier: 0.5  #  0 < scaleDownMultiplier < 1  speed to scale down

  constants:  # autoscaler parameters available for tuning
    default_sleep_time_runner_setup: 5  # seconds
    default_sleep_time_runner_delete: 5  # seconds
    runner_api_polling_interval: 600  # seconds
    runner_cool_down_period: 300  # seconds

```

## Documentation

This script allows you to automate routines for Bitbucket Pipelines self-hosted Runners.
With this script you can, create runners on Bitbucket Cloud via API requests, setup Kubernetes jobs on your host, connect Bitbucket Cloud runners with Kubernetes jobs, and provide artifacts kubespec files for created Bitbucket Cloud runners.
This scaling tool supports the next types of the workflow (strategy):
- percentageRunnersIdle

## percentageRunnersIdle strategy

The Runner Autoscaler Controller (next autoscaler) will poll Bitbucket Cloud API based on the configuration sync period for the number of available ONLINE/BUSY runners which live in the workspace/repository and scale based on the settings provided by autoscaler configuration file.
The autoscaler automatically scales the number of Jobs relates to the Bitbucket Runner in the Kubernetes Namespace based on custom metrics.

Implementation based on the next scaling algorithm:
The Runner Autoscaler Controller reads the configuration file provided by a user, periodically polls Bitbucket Cloud Runner API for available runners and automatically increases or decreases the count of "ONLINE" runners.
At start, the autoscaler checks for the min and max count of "ONLINE" runners.
If less than min - creates a new up to min count, if max already reached - just notify a user about max reached.

The limit runners count per workspace/repository is 100.

Then the autoscaler calculates runners scale threshold value: 
```
runners scale threshold value = BUSY_ONLINE_RUNNERS / ALL_ONLINE_RUNNERS
```
and compares it with scaleUpThreshold and scaleDownThreshold from the configuration file.

If runners scale threshold value more than scaleUpThreshold, it means that most "ONLINE" runners are BUSY (executing some pipelines job) and new runners will be created.
If runners scale threshold value less than scaleDownThreshold, it means that most "ONLINE" runners are in IDLE state and the count of online runners should be decreased to min count.

A speed to increase and decrease the count of runners could be turned with scaleUpMultiplier and scaleDownMultiplier values in the configuration file.

Finally, desired count of runners calculated by autoscaler:
```
desired count of runners = ALL_ONLINE_RUNNERS * scaleUpMultiplier  # scale up case
or
desired count of runners = ALL_ONLINE_RUNNERS * scaleDownMultiplier # scale down case
```


### An example

a user starts autoscaler with configuration previously provided (Bitbucket workspace has 0 runners).


#### *With the first autoscaler attempt:*

The autoscaler set up a new 1 (one) "ONLINE" runner.

Then a user runs pipeline that uses this runner, so 1 (one) BUSY runner present.

The autoscaler calculates **runners scale threshold** value as BUSY runners / ONLINE runners = 1/1 = **1.0**

In the configuration file value of scaleUpThreshold = 0.8, the autoscaler compare it with calculated value 1.0, so new runners should be created.

Then the autoscaler calculates **desired count of runners** = ONLINE runners * scaleUpMultiplier = ceil(1 * 1.5) = 2

Action: So, autoscaler should automatically create +1 ONLINE runner in addition to the existing 1 BUSY runner.


#### *With the next autoscaler attempt:*


The Bitbucket workspace has 2 ONLINE runners (1 BUSY and 1 IDLE).

User runs pipeline that still uses one runner, so BUSY runners 1.

The autoscaler calculates **runners scale threshold** value BUSY/ONLINE = 1/2 = **0.5**

So, value between scaleDownThreshold < runners scale threshold value < scaleUpThreshold (0.2 < 0.5 < 0.8)

Action: nothing to do.


#### *With the next autoscaler attempt:*


The Bitbucket workspace has 2 ONLINE runners (2 IDLE).

Because, a user’s pipeline job finished, so BUSY runners 0.

The autoscaler calculates **runners scale threshold** value BUSY/ONLINE = 0/2 = **0**

The value 0 under the scaleDownThreshold = 0.2, so count of runners should be decreased.

Then **desired count of runners** = ONLINE runners * scaleDownMultiplier = floor(2 * 0.5) = 1

And autoscaler should automatically delete 1 ONLINE (IDLE) runner.



## Links

- https://support.atlassian.com/bitbucket-cloud/docs/runners/
- https://support.atlassian.com/bitbucket-cloud/docs/configure-your-runner-in-bitbucket-pipelines-yml


## Support
If you’d like help with this tool, or you have an issue or feature request, [let us know on Community][community].

If you’re reporting an issue, please include:

- the version of the tool
- relevant logs and error messages
- steps to reproduce


## License
Copyright (c) 2021 Atlassian and others.
Apache 2.0 licensed, see [LICENSE.txt](LICENSE.txt) file.


[community]: https://community.atlassian.com/t5/forums/postpage/board-id/bitbucket-questions?add-tags=pipelines,pipes,runner,autoscaler
[runner]: https://support.atlassian.com/bitbucket-cloud/docs/runners/
[BITBUCKET_APP_PASSWORD]: https://support.atlassian.com/bitbucket-cloud/docs/app-passwords
[BITBUCKET API request limits]: https://support.atlassian.com/bitbucket-cloud/docs/api-request-limits/
[kubernetes-dashboard]: https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/
[setup cluster eksctl]: https://eksctl.io/usage/creating-and-managing-clusters/
