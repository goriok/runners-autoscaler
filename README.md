# Bitbucket Runner setup and scale script

Automate routines for Bitbucket Pipelines [self-hosted Runners][runner]


### When to use this tool?
Use this tool to set up and scale Bitbucket self-hosted runners on your own infrastructure.

### What problem does it solve?
This tool allows you to:

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

- This script sends requests to the BITBUCKET API in scale runners up and down.
Make sure you are aware of the [BITBUCKET API request limits][BITBUCKET API request limits].
- Maximum allowed count of repository runners is equal to 100.
- Maximum allowed count of workspace runners is equal to 100.
- Maximum allowed count of runner groups is equal to 10.
- Labelling naming conventions should follow [Kubernetes conventions][Kubernetes conventions].
- If runner groups overlap i.e. contain the same set of labels they will fight each other to scale the group so label sets should be unique.

### Requirements

- Operating systems supported is only Linux/amd64 with Kubernetes.
- Suggested memory for the controller is 8Gb (equal to t2.large or t3.large in [AWS instance types][AWS instance types]). More details about Bitbucket runners you could find in [BITBUCKET runners guide].

## Prerequisites
- BITBUCKET_USERNAME and [BITBUCKET_APP_PASSWORD][BITBUCKET_APP_PASSWORD] (base64 representation with repository:read, account:read, runner:write permissions) should be created and passed in `config/runners-autoscaler-deployment.yaml`. See [how to create base64 password](docs/base64-password-create.md).

- _optional_: setup [kubernetes-dashboard][kubernetes-dashboard] to monitor your cluster.

- _optional_: details of how to [set up AWS EKS cluster with eksctl cli][setup cluster eksctl]. Pay attention to the nodeGroup labels, because they are important for [escalator][escalator] (more details in [Scaling Kubernetes Nodes](docs/configuration/scaling-kubernetes-nodes.md)). Also see an example of [how to create cluster with labels](docs/deployment/create-eks-cluster-with-labels.md).


## How to run

### Deployment (in Kubernetes cluster)
Before the start you should create files in `config` folder to use them with the commands provided below.
See [Runners autoscaler deployment in kubernetes cluster](docs/deployment/runners-autoscaler-deployment.md) for more details.

```yaml
# Create namespace
kubectl apply -f config/runners-autoscaler-namespace.yaml

# Create RBAC configuration
kubectl apply -f config/runners-autoscaler-rbac.yaml

# Create config map - modify to suit your needs
kubectl apply -f config/runners-autoscaler-cm.yaml

# Create job config map
kubectl apply -f config/runners-autoscaler-cm-job.yaml

# Create secret
kubectl apply -f config/runners-autoscaler-secret.yaml

# Create deployment for autoscaler
kubectl apply -f config/runners-autoscaler-deployment.yaml

# Create deployment for cleaner
kubectl apply -f config/runners-autoscaler-deployment-cleaner.yaml
```

### Runner autoscaler configuration details
In `config/runners-autoscaler-cm.yaml` you can tune `runners_config.yaml` parameters:

```yaml
groups:
  - name: "Runner repository group"       # Name of the Runner displayed in the Bitbucket Runner UI.
    workspace: "my-workspace"             # Name of the workspace the Runner is added to.
    repository: "my-awesome-repository"   # Name of the repository the Runner is added to. Optional: Provide the repository name if you want the Runner to be added at the repository level.
    labels:
      - "demo1"                           # Labels for the Runner.
      - "test2"                           # Labels for the Runner.
    namespace: "runner-group-1"           # Kubernetes namespace to set up the Runner on.
    strategy: "percentageRunnersIdle"     # Type of the strategy workflow.
    # Set up the parameters for runners to create/delete via Bitbucket API.
    parameters: 
      min: 1  # recommended minimum 1 must be in UI to prevent pipeline fails, when new build is starting.
      max: 10  # maximum allowed runners count.
      scale_up_threshold: 0.8  # The percentage of busy runners at which the number of desired runners are re-evaluated to scale up.
      scale_down_threshold: 0.2  # The percentage of busy runners at which the number of desired runners are re-evaluated to scale up.
      scale_up_multiplier: 1.5  #  scale_up_multiplier > 1  speed to scale up.
      scale_down_multiplier: 0.5  #  0 < scale_down_multiplier < 1  speed to scale down.
    # Set up the resources for kubernetes job template.
    # This section is optional. If not provided the default values for memory "4Gi" and cpu "1000m" for requests and limits will be used.
    # More information https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#requests-and-limits
    resources:  # autoscaler kubernetes job template resources available for tuning.
      requests:
        memory: "2Gi"
        cpu: "1000m"
      limits:
        memory: "2Gi"
        cpu: "1000m"

constants:  # autoscaler parameters available for tuning.
  default_sleep_time_runner_setup: 5  # seconds. Time between runners creation.
  default_sleep_time_runner_delete: 5  # seconds. Time between runners deletion.
  runner_api_polling_interval: 600  # seconds. Time between requests to Bitbucket API.
  runner_cool_down_period: 300  # seconds. Time reserved for runner to set up.
```

## Documentation

This script allows you to automate routines for Bitbucket Pipelines self-hosted Runners.
With this script you can, create runners on Bitbucket Cloud via API requests, setup Kubernetes jobs on your host, connect Bitbucket Cloud runners with Kubernetes jobs, and provide artifacts kubespec files for created Bitbucket Cloud runners.
This scaling tool supports the next types of the workflow (strategy):

- [percentageRunnersIdle](docs/strategies/percentage-runners-idle-strategy.md)

Also see [Docs](docs/README.md) for deployment, configuration, cleaner, current issues and other topics related to runners autoscaler tool.

## Configuring
There are additional things you could configure listed below:

- [Scaling Kubernetes Nodes](docs/configuration/scaling-kubernetes-nodes.md)

- [Configuring Kubernetes Nodes](docs/configuration/configuring-kubernetes-nodes.md)

- [Tweaking Memory/Cpu resources](docs/configuration/tweaking-memory-cpu-resources.md)

## Runners autoscaler cleaner

The Runner Autoscaler Cleaner (next cleaner) is the application configured in `config/deployment-cleaner.yaml` that allows you automatically clean (delete) unhealthy runners and linked jobs.

See [Runners autoscaler cleaner](docs/cleaner.md) for more details.

## Known issues

- [Job creation scenario](docs/issues/jobs-creation-scenario.md)

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

[escalator]: https://github.com/atlassian/escalator/
[community]: https://community.atlassian.com/t5/forums/postpage/board-id/bitbucket-questions?add-tags=pipelines,pipes,runner,autoscaler
[runner]: https://support.atlassian.com/bitbucket-cloud/docs/runners/
[BITBUCKET_APP_PASSWORD]: https://support.atlassian.com/bitbucket-cloud/docs/app-passwords
[BITBUCKET API request limits]: https://support.atlassian.com/bitbucket-cloud/docs/api-request-limits/
[BITBUCKET runners guide]: https://support.atlassian.com/bitbucket-cloud/docs/runners/
[kubernetes-dashboard]: https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/
[Kubernetes conventions]: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set
[setup cluster eksctl]: https://eksctl.io/usage/creating-and-managing-clusters/
[AWS instance types]: https://aws.amazon.com/ec2/instance-types/
