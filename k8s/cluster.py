from prometheus.client import PrometheusClient
from k8s.node import Node


class Cluster:
    def __init__(self, prometheus_client: PrometheusClient):
        self.client = prometheus_client

    def get_nodes(self, start, end, step=60.0) -> list[Node]:
        query = 'kube_node_labels{label_spack_io_pipeline="true"}'
        resp = self.client.query_range(query, start, end, step)

        nodes = []
        for node_data in resp.json()["data"]["result"]:
            metrics = node_data["metric"]

            # always present metrics
            hostname = metrics["node"]
            first_seen = node_data["values"][0][0]
            last_seen = node_data["values"][-1][0]
            runtime = last_seen - first_seen

            # metrics present once fully booted
            instance_type = metrics["label_node_kubernetes_io_instance_type"]
            region = metrics["label_topology_kubernetes_io_region"]
            zone = metrics["label_topology_kubernetes_io_zone"]
            capacity_type = metrics["label_karpenter_sh_capacity_type"]

            nodes.append(
                Node(
                    hostname,
                    instance_type,
                    region,
                    zone,
                    capacity_type,
                    first_seen,
                    last_seen,
                )
            )

        return nodes
