# Bitbucket Runner setup and scale script

Automate routines for Bitbucket Pipelines [self-hosted Runners][runner]


Usage
========

```
python3 runner-scale.py --workspace myworkspace --repository myrepo --name cool --labels abc aaa ddd --runners-count 4
```

or config-file
```
python3 runner-scale.py --config filepath/config.yaml
```


## Parameters

| Variable                        | Usage                                             |
| ------------------------------- | --------------------------------------------------|
| workspace (*)                   |  Name of the workspace to setup Runner on.        |
| repository                      |  Name of the repository to setup Runner on. Optional: provide to create repository runner. |
| name (*)                        |  Name of the Runner displayed in Bitbucket Runner UI. |
| labels (*)                      |  Labels for Runner. |
| runners-count                   |  Count of Runners to setup. Automatically scale up or scale down runners according to Bitbucket runners with status "ONLINE". If value `0` all idle runners with status "ONLINE" will be deleted. Default: 1. |
| namespace                       |  Kubernetes namespace to setup Runner on. Default provided in [constants.py][constants.py] file will be created automatically. |
| debug                           |  Debug. Default: `false`. |
_(*) = required variable. This variable needs to be specified always when using the pipe._


Prerequisites
============
- BITBUCKET_USERNAME and [BITBUCKET_APP_PASSWORD][BITBUCKET_APP_PASSWORD] (with repository:read, workspace:read, runner:write) is required in your local environment.
- Python3.9
- python3 -m venv <MYVENV>
- pip install -r requirements.txt
- kubectl cli


Limitation
============
Script does requests to BITBUCKET API to scale up/down runners.
Make sure you acknowledged with [BITBUCKET API request limits][BITBUCKET API request limits].

Documentation
=============
This script allow you to automate routines for Bitbucket Pipelines self-hosted Runners
- create runner on Bitbucket cloud via API requests
- setup Kubernetes jobs on your local host
- connect them together
- provide artifacts kubespec files for "ONLINE" runners


Links
========
https://support.atlassian.com/bitbucket-cloud/docs/configure-your-runner-in-bitbucket-pipelines-yml
https://support.atlassian.com/bitbucket-cloud/docs/runners/

[runner]: https://support.atlassian.com/bitbucket-cloud/docs/runners/
[runner-config]: https://support.atlassian.com/bitbucket-cloud/docs/configure-your-runner-in-bitbucket-pipelines-yml
[BITBUCKET_APP_PASSWORD]: https://support.atlassian.com/bitbucket-cloud/docs/app-passwords
[BITBUCKET API request limits]: https://support.atlassian.com/bitbucket-cloud/docs/api-request-limits/
