# Group-(b) methodology — deploy jira-nano to a local kind cluster (JN-46)

Runnable on a developer machine (needs `kind`, `kubectl`, `helm`, `docker`). Not
in CI (needs a cluster). Claude runs this during development; a human can repeat it.

```bash
# 1. Cluster + image
kind create cluster --name jira-nano
DOCKER_BUILDKIT=1 docker build -t jira-nano:kind .
kind load docker-image jira-nano:kind --name jira-nano

# 2. Install the chart with the local image
helm install jn ./chart \
  --set image.repository=jira-nano --set image.tag=kind --set image.pullPolicy=Never

# 3. Assertions
kubectl rollout status statefulset/jn-jira-nano --timeout=120s   # becomes Ready
kubectl get pvc                                                  # data + models PVCs Bound
kubectl exec statefulset/jn-jira-nano -- test -d /data/repo/.git # init ran (idempotent)
kubectl port-forward svc/jn-jira-nano 8080:80 &
curl -fsS localhost:8080/rest/api/2/myself                       # API answers

# 4. Cleanup
helm uninstall jn && kind delete cluster --name jira-nano
```

Record pass/fail per row in [../../docs/tests.md](../../docs/tests.md).
