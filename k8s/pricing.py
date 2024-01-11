class PriceIndex():
    def __init__(self, prometheus_client, region, start, end, capacity_type=None):
        client = prometheus_client

        filters = [f"region='{region}'"]
        if capacity_type:
            filters.append(f"capacity_type='{capacity_type}'")

        filters_str = ", ".join(filters)
        query = "karpenter_cloudprovider_instance_type_price_estimate{"+filters_str+"}"

        resp = client.query_range(query, start, end)
        data = resp.json()["data"]["result"]

        self.data = {x["metric"]["instance_type"]: x["values"] for x in data}

    def get_node_cost(self, instance_type, zone, start, end):
        cost = 0
        for value in self.data[instance_type]:
            if value[0] >= start and value[0] <= end:
                cost += float(value[1])/60
        return round(cost, 5)
