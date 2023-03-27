# Runner Autoscaler Cleaner
The Runner Autoscaler Cleaner (next cleaner) is the application configured in `config/deployment-cleaner.template.yaml` that allows you automatically clean (delete) unhealthy runners and linked jobs.

Implementation based on the next algorithm:

- Check runners on Bitbucket Cloud, that:

    - do not have status `ONLINE`,
    - have `autoscaler.created` label (this label was automatically added when runner created by runners autoscaler tool),
    - have their state updated more than some period of time ago. You can tune it with `runner_cool_down_period` variable from ConfigMap `runners_config.yaml` used in `config/runners-autoscaler-cm.yaml`.

- For each runner found get it UUID and delete.

- Find jobs on kubernetes labeled with runners UUIDs if any.

- Delete jobs found since they are unhealthy.

Repeat cleaner logic after some period of time. You can tune it with `runner_api_polling_interval` variable from ConfigMap `runners_config.yaml` used in `config/runners-autoscaler-cm.yaml`.