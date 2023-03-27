# Tweaking Memory/Cpu resources
Inside `runners-autoscaler-cm-job.template.yaml`, you will notice that the `resources` tag is defined.

It might be worth tweaking the memory/cpu limits according to your needs.

For example, if you want to use an `8Gb` instance size, it might not be worth using `4Gi` since it will take slightly more than half of the allocatable memory therefore it would allow only 1 runner pod per instance.