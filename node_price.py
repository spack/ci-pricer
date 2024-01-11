import os
import time
from datetime import datetime

from prometheus.client import PrometheusClient
from k8s.node import Node
from k8s.cluster import Cluster
from k8s.pricing import PriceIndex


def main():
    prometheus_url = os.environ.get("CIDA_PROMETHEUS_URL")
    if prometheus_url is None:
        print("Error: CIDA_PROMETHEUS_URL is undefined")
        exit(1)

    prometheus_cookie = os.environ.get("CIDA_PROMETHEUS_COOKIE")
    if prometheus_cookie is None:
        print("Error: CIDA_PROMETHEUS_COOKIE is undefined")
        exit(1)

    client = PrometheusClient(prometheus_url, prometheus_cookie)
    cluster = Cluster(client)

    now = time.time()
    start = now - (60 * 60 * 6)  # grab the last 6 hours worth of data
    end = now

    price_index = PriceIndex(client, "us-east-1", start, end, capacity_type="spot")
    nodes = cluster.get_nodes(start, end)

    total_cost = 0
    for node in nodes:
        cost = price_index.get_node_cost(node.instance_type, node.zone, node.start, node.end)
        total_cost += cost
        print(f"{node.hostname}: {datetime.fromtimestamp(node.start)} -> {datetime.fromtimestamp(node.end)} ({round(node.runtime, 2)}min): {node.instance_type} [Cost: ${cost}]")

    print(total_cost)

if __name__ == "__main__":
    main()
