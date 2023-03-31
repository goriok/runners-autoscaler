# Configuring Kubernetes Nodes

In the job config map `runners-autoscaler-cm-job.template.yaml`, you will notice there's a `nodeSelector` in there.

Therefore, the nodes where the runners will be running on need to have a label that matches it. In AWS EKS, this can be configured via [EKS Managed Node Groups][eks-node-groups].

In example in `runners-autoscaler-cm-job.template.yaml` next label present: `customer=shared`.
So the Kubernetes node should be updated with this label:
`kubectl label nodes <kubernetes-node> customer=shared`

This label also must match the one you configured in [escalator config map][escalator-cm].

[eks-node-groups]: https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html
[escalator-cm]: https://github.com/atlassian/escalator/blob/master/docs/deployment/escalator-cm.yaml#L10-L11