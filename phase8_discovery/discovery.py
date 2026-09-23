"""Finding out which agents exist, at runtime.

Up to phase 7 the coordinator's team was a literal in a Python file:

    PORTS = {"research": 8101, "analysis": 8102, "writer": 8103}

That line is the assumption this phase removes. It asserts, at authoring
time, three things that are not knowable at authoring time: which agents
exist, how many there are, and where they live. In a cloud-native
deployment all three change while the system is running -- pods are
rescheduled, replicas scale, new agents are deployed.

A `Discovery` answers the same question by asking the infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

# Agents opt in by carrying this label. It is already on every Deployment
# and Service in k8s/agents.yaml -- unused until now.
AGENT_LABEL = "a2a.agent/enabled=true"


@dataclass(frozen=True)
class Endpoint:
    """Where an agent is, before we know anything about what it does."""

    name: str
    url: str

    def __str__(self) -> str:
        return f"{self.name} @ {self.url}"


class Discovery(Protocol):
    def find_agents(self) -> list[Endpoint]: ...


class StaticDiscovery:
    """A fixed list. Exists so the rest of the system can be developed and
    tested without a cluster -- and as the baseline the dynamic version is
    compared against."""

    def __init__(self, urls: dict[str, str]) -> None:
        self._urls = dict(urls)

    def find_agents(self) -> list[Endpoint]:
        return [Endpoint(n, u) for n, u in sorted(self._urls.items())]


class KubernetesDiscovery:
    """Ask the cluster which agents are running.

    Queries Services rather than Pods deliberately. A Pod's address dies
    with the Pod; a Service is the stable name that survives rescheduling
    and load-balances across replicas. Asking for pods would give us
    addresses that are correct for a few seconds at a time.
    """

    def __init__(self, namespace: str = "default", label: str = AGENT_LABEL) -> None:
        from kubernetes import client, config

        try:
            # Works when the coordinator is itself a pod.
            config.load_incluster_config()
            self.context = "in-cluster"
        except Exception:
            # Falls back to your kubeconfig when run from a laptop.
            config.load_kube_config()
            self.context = "kubeconfig"

        self._api = client.CoreV1Api()
        self._namespace = namespace
        self._label = label

    def find_agents(self) -> list[Endpoint]:
        services = self._api.list_namespaced_service(
            namespace=self._namespace, label_selector=self._label
        )
        found = []
        for svc in services.items:
            ports = svc.spec.ports or []
            if not ports:
                continue
            name = svc.metadata.labels.get("agent", svc.metadata.name)
            # Cluster-internal DNS. Valid for callers inside the cluster --
            # which is where a coordinator belongs.
            found.append(
                Endpoint(name=name, url=f"http://{svc.metadata.name}:{ports[0].port}/")
            )
        return sorted(found, key=lambda e: e.name)


def get_discovery(kind: str, **kwargs) -> Discovery:
    if kind == "static":
        return StaticDiscovery(kwargs.get("urls", {}))
    if kind == "kubernetes":
        return KubernetesDiscovery(**{k: v for k, v in kwargs.items() if k != "urls"})
    raise ValueError(f"unknown discovery {kind!r}")
