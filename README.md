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


## Usage

```
python3 runner-scale.py --config filepath/config.yaml
```


## Parameters
| Parameter             | Usage                                             |
| --------------------- | --------------------------------------------------|
| --config(*)           |  Path to runners-autoscaler config file. Use template [`runner-config.yaml.template`](./runner-config.yaml.template). Setup will start with parameters provided in the config. |
| --debug               |  Debug details of the script execution. Change this to `true` if you would like to debug. Default: `false`. |
_(*) = required variable. This variable needs to always be specified when using the pipe._

The runners setup will start with the parameters provided from the config file.
An example of the config file is provided in the following template: [`runner-config.yaml.template`](./runner-config.yaml.template).


## Runner config details:

```yaml
config:
  - name: Runner repository group       # Name of the Runner displayed in the Bitbucket Runner UI.
    workspace: myworkspace              # Name of the workspace the Runner is added to. 
    repository: my-awesome-repository   # Name of the repository the Runner is added to. Optional: Provide the repository name if you want the Runner to be added at the repository level.
    labels:
      - demo1                           # Labels for the Runner.
    namespace: runner-group-1           # Kubernetes namespace to set up the Runner on. The default namespace that is provided in the constants.py file will be used, if you do not create or add a different namespace.
    type: manual                        # Type of the setup workflow. Will be extended with a new types soon.
    parameters:
      runners_count: 1                  # Count of Runners to set up. Automatically scale up or scale down runners according to Bitbucket runners with status "ONLINE". If value `0` all idle runners with status "ONLINE" will be deleted. Default: 1.
  - name: Runner workspace group
    workspace: myworkspace
    labels:
      - demo2
    namespace: runner-group-2
    type: manual
    parameters:
      runners_count: 0
```


## Prerequisites

Before executing the script, make sure it meets the following requirements:

- BITBUCKET_USERNAME and [BITBUCKET_APP_PASSWORD][BITBUCKET_APP_PASSWORD] (with repository:read, workspace:read, runner:write permissions) in the local environment.
     ```
     export BITBUCKET_USERNAME=username
     export BITBUCKET_APP_PASSWORD=password
     ```
- Python3.7+
- python [virtual environments][venv] - to create and activate it, use the following commands: 
    ```
    python3 -m venv <MYVENV>  # create a virtual environment
    . <MYVENV>/bin/activate  # activate a virtual environment
    ```
- python dependencies installed:
  ```
  pip install -r requirements.txt
  ```
- [kubernetes (k8s) cluster and client][k8s install] installed:
  ```
  kubectl version
  ```


## Documentation

This script allows you to automate routines for Bitbucket Pipelines self-hosted Runners.
With this script you can, create runners on Bitbucket Cloud via API requests, setup Kubernetes jobs on your host, connect Bitbucket Cloud runners with Kubernetes jobs, and provide artifacts kubespec files for created Bitbucket Cloud runners.

## Scale down logic:

If the value is set to '0' for the scale down logic, all idle runners with an “ONLINE” status will be deleted, or if the count of runners that you’ve provided is less than the current runners count, then idle runners with an “ONLINE” status will be deleted.


## Links

- https://support.atlassian.com/bitbucket-cloud/docs/runners/
- https://support.atlassian.com/bitbucket-cloud/docs/configure-your-runner-in-bitbucket-pipelines-yml

[runner]: https://support.atlassian.com/bitbucket-cloud/docs/runners/
[runner-config]: https://support.atlassian.com/bitbucket-cloud/docs/configure-your-runner-in-bitbucket-pipelines-yml
[BITBUCKET_APP_PASSWORD]: https://support.atlassian.com/bitbucket-cloud/docs/app-passwords
[BITBUCKET API request limits]: https://support.atlassian.com/bitbucket-cloud/docs/api-request-limits/
[venv]: https://docs.python.org/3/library/venv.html
[k8s install]: https://kubernetes.io/docs/tasks/tools/
