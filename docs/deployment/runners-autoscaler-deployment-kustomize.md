# Runners autoscaler deployment in kubernetes cluster - Kustomize

1. Go to in `kustomize` folder.
```
cd kustomize
```

2. Configure the files in the `values` folder.

3. Verify the generated output.
```
kubectl kustomize values
```

4. Apply it.
```
kubectl apply -k values
```

5. Verify if the runner-controller pod works.

```
kubectl logs -f -l app=runner-controller -n bitbucket-runner-control-plane
```

6. Verify if runners are being created.
```
kuctl logs -l runner_uuid -c runner
```
