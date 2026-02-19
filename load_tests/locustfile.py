from locust import HttpUser, task, between
import os
import random

# Default secret for local testing if not set
RAPIDAPI_SECRET = os.getenv("X_RAPIDAPI_PROXY_SECRET", "your-rapidapi-secret")

class OGMinerUser(HttpUser):
    wait_time = between(1, 4)  # Simulate a user waiting 1-4 seconds between requests
    
    def on_start(self):
        """Called when a User starts running."""
        self.client.headers.update({"X-RapidAPI-Proxy-Secret": RAPIDAPI_SECRET})

    @task(3)
    def extract_metadata(self):
        """Test the main extraction endpoint (higher weight)."""
        urls = [
            "https://www.github.com",
            "https://www.netflix.com",
            "https://www.youtube.com",
            "https://stackoverflow.com",
            "https://example.com"
        ]
        target_url = random.choice(urls)
        
        self.client.post("/v1/extract", json={
            "url": target_url,
            "enable_javascript": False, # Keep it light for load testing unless specifically testing browser
            "force_refresh": False      # Allow caching to be tested
        }, name="/v1/extract (light)")

    @task(1)
    def extract_spa(self):
        """Test heavier SPA extraction (lower weight)."""
        self.client.post("/v1/extract", json={
            "url": "https://reactjs.org",
            "enable_javascript": True,
            "force_refresh": True
        }, name="/v1/extract (SPA)")

    @task(2)
    def get_screenshot(self):
        """Test screenshot generation."""
        self.client.get("/v1/screenshot", params={
            "url": "https://example.com",
            "width": 1280,
            "height": 720
        }, name="/v1/screenshot")

    @task(4)
    def proxy_image(self):
        """Test image proxy (highest weight as it should be fast)."""
        # Using a stable image URL
        img_url = "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"
        self.client.get("/v1/image", params={
            "url": img_url,
            "width": 300
        }, name="/v1/image")
