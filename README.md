# Bitbucket Runner setup and scale script

Automate routines for Bitbucket Pipelines [self-hosted Runners][runner]

# TODO ADD BITBUCKET API rate limit links

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
| name (*)                        |  List of Runner’s labels space separated.         |
| labels (*)                      |  Labels for Runner                                |
| runners-count (*)               |  Count of Runners to setup                        |
| debug                           |  Debug                                            |
_(*) = required variable. This variable needs to be specified always when using the pipe._


Prerequisites
============
- BITBUCKET_USERNAME and [BITBUCKET_APP_PASSWORD][BITBUCKET_APP_PASSWORD] (with repository:read, workspace:read, runner:write) is required in your local environment.
- Python3
- python3 -m venv <MYVENV>
- pip install -r requirements.txt
- kubectl cli
- running kubectl cluster with namespace bitbucket-runner or provide your own in the config
- 


Documentation
=============
This script allow you to automate routines for Bitbucket Pipelines self-hosted Runners
- create runner on Bitbucket cloud via API requests
- setup Kubernetes jobs on your local host
- connect them together




Links
========
https://support.atlassian.com/bitbucket-cloud/docs/configure-your-runner-in-bitbucket-pipelines-yml
https://support.atlassian.com/bitbucket-cloud/docs/runners/

[runner]: https://support.atlassian.com/bitbucket-cloud/docs/runners/
[runner-config]: https://support.atlassian.com/bitbucket-cloud/docs/configure-your-runner-in-bitbucket-pipelines-yml
[BITBUCKET_APP_PASSWORD]: https://support.atlassian.com/bitbucket-cloud/docs/app-passwords
