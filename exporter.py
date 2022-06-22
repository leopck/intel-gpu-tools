"""Application exporter"""

import os
import time
from prometheus_client import start_http_server, Gauge, Enum
import requests
import zmq
import struct

topic = "fancyhw_data".encode('ascii')

print("Reading messages with topic: {}".format(topic))

class AppMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    application metrics into Prometheus metrics.
    """

    def __init__(self, app_port=80, polling_interval_seconds=5):
        self.app_port = app_port
        self.polling_interval_seconds = polling_interval_seconds

        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)

        self.socket.connect("tcp://127.0.0.1:5555")
        self.socket.setsockopt(zmq.SUBSCRIBE, topic)
        # Prometheus metrics to collect
        self.current_requests = Gauge("gpu_utilization", "GPU Utilization")
        self.pending_requests = Gauge("app_requests_pending", "Pending requests")
        self.total_uptime = Gauge("app_uptime", "Uptime")
        self.health = Enum("app_health", "Health", states=["healthy", "unhealthy"])

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:
            self.fetch()
            time.sleep(self.polling_interval_seconds)

    def fetch(self):
        """
        Get metrics from application and refresh Prometheus metrics with
        new values.
        """

        # Fetch raw status data from the application
        # resp = requests.get(url=f"http://localhost:{self.app_port}/status")
        # status_data = resp.json()

        binary_topic, data_buffer = self.socket.recv().split(b' ', 1)

        topic = binary_topic.decode(encoding = 'ascii')

        # print("Message {:d}:".format(i))
        print("\ttopic: '{}'".format(topic))

        packet_size = len(data_buffer) // struct.calcsize("h")

        print("\tpacket size: {:d}".format(packet_size))

        struct_format = "{:d}h".format(packet_size)

        data = struct.unpack(struct_format, data_buffer)

        print("\tdata: {}".format(data))

        x, = data

        # i += 1

        # Update Prometheus metrics with application metrics
        # self.current_requests.set(status_data["current_requests"])
        # self.pending_requests.set(status_data["pending_requests"])
        # self.total_uptime.set(status_data["total_uptime"])
        # self.health.state(status_data["health"])
        self.current_requests.set(x)
        self.pending_requests.set("51")
        self.total_uptime.set("512")
        self.health.state("healthy")

    def __exit__(self):
        self.socket.close()

def main():
    """Main entry point"""

    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "1"))
    app_port = int(os.getenv("APP_PORT", "80"))
    exporter_port = int(os.getenv("EXPORTER_PORT", "9877"))

    app_metrics = AppMetrics(
        app_port=app_port,
        polling_interval_seconds=polling_interval_seconds
    )
    start_http_server(exporter_port)
    app_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()