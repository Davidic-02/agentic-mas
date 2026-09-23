# Deploying to Kubernetes

Assumes a local cluster (kind) and an image built into it.

    # 1. cluster
    kind create cluster --name agentic-mas

    # 2. image (built locally, loaded straight into the cluster --
    #    no registry needed)
    docker build -t agentic-mas:latest .
    kind load docker-image agentic-mas:latest --name agentic-mas

    # 3. deploy
    kubectl apply -f k8s/agents.yaml
    kubectl get pods -l app=agentic-mas -w

    # 4. reach an agent's card from outside the cluster
    kubectl port-forward svc/research 8101:8101
    curl localhost:8101/.well-known/agent-card.json

    # 5. the demonstration the spec calls for: kill one and watch it return
    kubectl delete pod -l agent=research
    kubectl get pods -l app=agentic-mas -w

    # 6. scale one agent independently of the others
    kubectl scale deployment/research --replicas=3
