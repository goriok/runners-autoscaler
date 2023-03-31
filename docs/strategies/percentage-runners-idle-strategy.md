# percentageRunnersIdle strategy

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
and compares it with scale_up_threshold and scale_down_threshold from the configuration file.

If runners scale threshold value more than scale_up_threshold, it means that most "ONLINE" runners are BUSY (executing some pipelines job) and new runners will be created.
If runners scale threshold value less than scale_down_threshold, it means that most "ONLINE" runners are in IDLE state and the count of online runners should be decreased to min count.

A speed to increase and decrease the count of runners could be turned with scale_up_multiplier and scale_down_multiplier values in the configuration file.

Finally, desired count of runners calculated by autoscaler:
```
desired count of runners = ALL_ONLINE_RUNNERS * scale_up_multiplier  # scale up case
or
desired count of runners = ALL_ONLINE_RUNNERS * scale_down_multiplier # scale down case
```


## An example

a user starts autoscaler with configuration previously provided (Bitbucket workspace has 0 runners).


### *With the first autoscaler attempt:*

The autoscaler set up a new 1 (one) "ONLINE" runner.

Then a user runs pipeline that uses this runner, so 1 (one) BUSY runner present.

The autoscaler calculates **runners scale threshold** value as BUSY runners / ONLINE runners = 1/1 = **1.0**

In the configuration file value of scale_up_threshold = 0.8, the autoscaler compare it with calculated value 1.0, so new runners should be created.

Then the autoscaler calculates **desired count of runners** = ONLINE runners * scale_up_multiplier = ceil(1 * 1.5) = 2

Action: So, autoscaler should automatically create +1 ONLINE runner in addition to the existing 1 BUSY runner.


### *With the next autoscaler attempt:*


The Bitbucket workspace has 2 ONLINE runners (1 BUSY and 1 IDLE).

User runs pipeline that still uses one runner, so BUSY runners 1.

The autoscaler calculates **runners scale threshold** value BUSY/ONLINE = 1/2 = **0.5**

So, value between scale_down_threshold < runners scale threshold value < scale_up_threshold (0.2 < 0.5 < 0.8)

Action: nothing to do.


### *With the next autoscaler attempt:*


The Bitbucket workspace has 2 ONLINE runners (2 IDLE).

Because, a user’s pipeline job finished, so BUSY runners 0.

The autoscaler calculates **runners scale threshold** value BUSY/ONLINE = 0/2 = **0**

The value 0 under the scale_down_threshold = 0.2, so count of runners should be decreased.

Then **desired count of runners** = ONLINE runners * scale_down_multiplier = floor(2 * 0.5) = 1

And autoscaler should automatically delete 1 ONLINE (IDLE) runner.