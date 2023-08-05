import time
from locust import HttpUser, task, between

class TestUser(HttpUser):
    wait_time = between(1, 2.5)
    host = "http://127.0.0.1:8000"

    @task
    def hello_world(self):
        self.client.get("/")

    @task(3)
    def view_items(self):
        for item_id in range(10):
            self.client.get(f"/items/{item_id}", name="/items")
            time.sleep(1)