# M-Flow Kubernetes Deployment via Helm

Deploy M-Flow to any Kubernetes cluster using the bundled Helm chart with PostgreSQL and pgvector support.

> **Note**: This chart is intended for development and staging environments. Review and harden configurations before using in production.

## Requirements

| Tool | Purpose | Install Guide |
|------|---------|---------------|
| Kubernetes cluster | Runtime (Minikube, GKE, EKS, etc.) | — |
| Helm 3+ | Chart management | [helm.sh/docs](https://helm.sh/docs/intro/install/) |
| kubectl | Cluster interaction | [kubernetes.io/docs](https://kubernetes.io/docs/tasks/tools/install-kubectl/) |

## Getting Started

1. Clone this repository and navigate to the project root.

2. Install the chart:

```bash
helm install m_flow ./deployment/helm
```

3. Verify the deployment:

```bash
kubectl get pods
```

## Removing the Deployment

```bash
helm uninstall m_flow
```
