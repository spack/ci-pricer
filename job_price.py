import os
import time
from datetime import datetime

from prometheus.client import PrometheusClient
from k8s.node import Node
from k8s.cluster import Cluster
from k8s.pricing import PriceIndex


class Job:
    def __init__(self, gitlab_job_id, pod, node, mem_request, cpu_request, package=None):
        self.gitlab_id = gitlab_job_id
        self.pod = pod
        self.node = node
        self.package = package
        self.mem_request = mem_request
        self.cpu_request = cpu_request


def get_jobs(prometheus_client, start, end):
    client = prometheus_client

    filters = 'namespace="pipeline", container="build"'

    # this query should be first since it controls the loop
    # if other queries run first it's possible this will contain a pod that
    # doesn't exist in previous queries
    cpu_util_query = 'sum(rate(container_cpu_usage_seconds_total{' + filters + '}[90s])) by (pod)'
    resp = client.query_range(cpu_util_query, start, end)
    cpu_utilization = resp.json()["data"]["result"]

    pod_labels_query = 'kube_pod_labels{namespace="pipeline"}'
    resp = client.query_range(pod_labels_query, start, end)
    pod_labels = resp.json()["data"]["result"]
    pod_labels_dict = {x["metric"]["pod"]: x["metric"] for x in pod_labels}

    cpu_request_query = 'kube_pod_container_resource_requests{' + filters + ', resource="cpu"}'
    resp = client.query_range(cpu_request_query, start, end)
    cpu_requests = resp.json()["data"]["result"]
    cpu_requests_dict = {x["metric"]["pod"]: x for x in cpu_requests}

    mem_request_query = 'kube_pod_container_resource_requests{' + filters + ', resource="memory"}'
    resp = client.query_range(mem_request_query, start, end)
    mem_requests = resp.json()["data"]["result"]
    mem_requests_dict = {x["metric"]["pod"]: x for x in mem_requests}

    mem_util_query = 'sum(container_memory_working_set_bytes{' + filters + '}) by (pod)'
    resp = client.query_range(mem_util_query, start, end)
    mem_utilization = resp.json()["data"]["result"]
    memory_utilization_dict = {x["metric"]["pod"]: x for x in mem_utilization}

    jobs = []
    for cpu_utilization_data in cpu_utilization:
        pod = cpu_utilization_data["metric"]["pod"]

        # disregard builds that haven't yet started running on a node
        try:
            node = cpu_requests_dict[pod]["metric"]["node"]
            gitlab_job = pod_labels_dict[pod]["label_gitlab_ci_job_id"]
            cpu_request = cpu_requests_dict[pod]["values"][0][1]
            mem_request = mem_requests_dict[pod]["values"][0][1]

            first_seen = cpu_utilization_data["values"][0][0]
            last_seen = cpu_utilization_data["values"][-1][0]

            package = None
            if "label_metrics_spack_job_spec_pkg_name" in pod_labels_dict[pod]:
                package = pod_labels_dict[pod]["label_metrics_spack_job_spec_pkg_name"]

            jobs.append(Job(gitlab_job, pod, node, mem_request, cpu_request, package=package))
        except KeyError:
            pass

    return jobs


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
    jobs = get_jobs(client, start, end)

    for job in jobs:
        print(f"{job.gitlab_id}: {job.pod} :: {job.node}")


if __name__ == "__main__":
    main()
