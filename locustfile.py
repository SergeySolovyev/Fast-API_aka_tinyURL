from locust import HttpUser, between, task


class ShortenerUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def open_health(self):
        self.client.get("/health")

    @task(2)
    def open_docs_info(self):
        self.client.get("/api")

    @task(1)
    def create_short_link(self):
        self.client.post(
            "/links/shorten",
            json={"original_url": "https://example.com/load-test"},
        )
