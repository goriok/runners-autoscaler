# Scaling Kubernetes Nodes

Your kubernetes cluster will need to have a node horizontal autoscaler configured.

We recommend using a tool that is optimized for large batch or job based workloads such as [escalator][escalator].

Please check the [deployment docs][escalator-docs].

If you are using AWS, you'll need to use this deployment `aws/escalator-deployment-aws.yaml` instead of the regular one.

[escalator-docs]: https://github.com/atlassian/escalator/tree/master/docs/deployment
[escalator]: https://github.com/atlassian/escalator/