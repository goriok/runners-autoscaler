# Runners autoscaler deployment in kubernetes cluster

Create in `config/` folder these files:

`config/runners-autoscaler-cm.yaml`,

`config/runners-autoscaler-cm-job.yaml`,

`config/runners-autoscaler-secret.yaml`,

`config/runners-autoscaler-deployment.yaml`,

`config/runners-autoscaler-deployment-cleaner.yaml`

based on templates provided inside `config` folder. 

Update next files with needed variables (these variables decorated with `<...>` inside template files):

`config/runners-autoscaler-cm.yaml`,

`config/runners-autoscaler-secret.yaml`,

`config/runners-autoscaler-deployment.yaml`,

`config/runners-autoscaler-deployment-cleaner.yaml`

You could extend/update any files inside `config` folder according to your requirements, but do not update/delete `mandatory do not modify` lines.

Next run commands below: 
```
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