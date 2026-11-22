"""Thin client for the Meta Graph API test-user endpoints.

Docs: https://developers.facebook.com/docs/graph-api/reference/app/accounts/test-users
"""
import requests


class GraphError(RuntimeError):
    pass


class GraphClient:
    def __init__(self, app_id, app_secret, api_version=None, session=None, timeout=30):
        self.app_id = app_id
        # An app access token is "<app id>|<app secret>". It is sent in the
        # Authorization header so it never ends up in a URL or a log line.
        self._token = f"{app_id}|{app_secret}"
        self.base = "https://graph.facebook.com" + (f"/{api_version}" if api_version else "")
        self.session = session or requests.Session()
        self.timeout = timeout

    def _request(self, method, url, **kwargs):
        if not url.startswith("https://"):
            url = f"{self.base}/{url}"
        try:
            resp = self.session.request(
                method,
                url,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise GraphError(f"{method} failed: {type(exc).__name__}") from None
        try:
            body = resp.json()
        except ValueError:
            raise GraphError(f"{method} returned HTTP {resp.status_code} (non-JSON body)") from None
        if resp.status_code >= 400 or (isinstance(body, dict) and "error" in body):
            err = body.get("error", {}) if isinstance(body, dict) else {}
            raise GraphError(
                f"Graph API error {err.get('code', resp.status_code)}: "
                f"{err.get('message', 'unknown error')}"
            )
        return body

    def create_test_user(self, name, permissions=(), installed=True):
        """Create one test user. Returns id, email, password, login_url, access_token."""
        data = {"name": name, "installed": "true" if installed else "false"}
        if permissions:
            data["permissions"] = ",".join(permissions)
        return self._request("POST", f"{self.app_id}/accounts/test-users", data=data)

    def list_test_users(self):
        """Yield every test user of the app (id, login_url, access_token)."""
        url, params = f"{self.app_id}/accounts/test-users", {"limit": 100}
        while url:
            page = self._request("GET", url, params=params)
            yield from page.get("data", [])
            url, params = page.get("paging", {}).get("next"), None

    def delete_test_user(self, user_id):
        return self._request("DELETE", str(user_id))
