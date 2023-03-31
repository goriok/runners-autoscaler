# Create EKS cluster with labels

To create EKS cluster with labels run the command below with provided `cluster.yaml` manifest:

```
 eksctl create cluster -f cluster.yaml
```

_Example of the cluster.yaml manifest:_

```cluster.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: "pipes-runner-test"
  region: "us-east-1"
  version: "1.25"

availabilityZones:
  - "us-east-1c"
  - "us-east-1b"

nodeGroups:
  - name: "pipes-runner-node"
    labels: { customer: shared }
    instanceType: "t3.large"
    amiFamily: "AmazonLinux2"
    desiredCapacity: 1
    minSize: 1
    maxSize: 5
```