"""Publish photos to your own Instagram professional account.

Uses the official content publishing API:
https://developers.facebook.com/docs/instagram-platform/content-publishing
"""
import time

import requests


class InstagramError(RuntimeError):
    pass


class InstagramBot:
    def __init__(self, user_id, access_token, base_url="https://graph.instagram.com",
                 session=None, timeout=30, sleep=time.sleep):
        self.user_id = user_id
        self._token = access_token
        self.base = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout
        self._sleep = sleep

    def _request(self, method, path, **kwargs):
        # The token goes in the Authorization header so it never appears in a URL or log.
        try:
            resp = self.session.request(
                method,
                f"{self.base}/{path}",
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise InstagramError(f"{method} {path} failed: {type(exc).__name__}") from None
        try:
            body = resp.json()
        except ValueError:
            raise InstagramError(f"{method} {path} returned HTTP {resp.status_code}") from None
        if resp.status_code >= 400 or "error" in body:
            err = body.get("error", {})
            raise InstagramError(
                f"Instagram API error {err.get('code', resp.status_code)}: "
                f"{err.get('message', 'unknown error')}"
            )
        return body

    def create_container(self, image_url, caption="", alt_text=""):
        data = {"image_url": image_url}
        if caption:
            data["caption"] = caption
        if alt_text:
            data["alt_text"] = alt_text
        return self._request("POST", f"{self.user_id}/media", data=data)["id"]

    def wait_until_ready(self, container_id, attempts=10, interval=3):
        """Poll until Instagram has fetched and processed the image."""
        for _ in range(attempts):
            status = self._request(
                "GET", container_id, params={"fields": "status_code"}
            ).get("status_code")
            if status == "FINISHED":
                return
            if status in ("ERROR", "EXPIRED"):
                raise InstagramError(f"Media container {container_id} is {status}")
            self._sleep(interval)
        raise InstagramError(f"Media container {container_id} not ready in time")

    def publish(self, container_id):
        return self._request(
            "POST", f"{self.user_id}/media_publish", data={"creation_id": container_id}
        )["id"]

    def post_photo(self, image_url, caption="", alt_text=""):
        """Post one photo; returns (media_id, permalink)."""
        container_id = self.create_container(image_url, caption, alt_text)
        self.wait_until_ready(container_id)
        media_id = self.publish(container_id)
        permalink = self._request(
            "GET", media_id, params={"fields": "permalink"}
        ).get("permalink", "")
        return media_id, permalink
