import requests
import urllib.parse

class PrometheusClient():
    def __init__(self, url, cookie):
        self.url = url
        self.cookies = {"_oauth2_proxy": cookie}

    def query_range(self, query, start, end, step=60.0):
        query = urllib.parse.quote(query)
        url = f"{self.url}/query_range?query={query}&start={start}&end={end}&step={step}"
        return requests.get(url, cookies=self.cookies)
