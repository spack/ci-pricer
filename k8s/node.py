class Node:
    def __init__(self, hostname, instance_type, region, zone, capacity_type, start, end):
        self.hostname = hostname
        self.instance_type = instance_type
        self.region = region
        self.zone = zone
        self.capacity_type = capacity_type
        self.start = start
        self.end = end

    def update(self, start=None, end=None):
        if start is not None:
            self.start = start

        if end is not None:
            self.end = end

    @property
    def runtime(self):
        return (self.end - self.start)/60
