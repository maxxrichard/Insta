import argparse

import pytest

from testusers import cli
from testusers.graph import GraphClient, GraphError
from testusers.names import generate_names
from testusers.tracker import Tracker


class FakeResponse:
    def __init__(self, body, status=200):
        self._body, self.status_code = body, status

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


def test_names_are_unique_and_respect_exclude():
    first = generate_names(50, seed=1)
    second = generate_names(50, exclude=first, seed=1)
    assert len(set(first)) == 50
    assert not set(first) & set(second)
    assert all(len(n.split()) == 2 for n in first)


def test_names_exhausted():
    with pytest.raises(ValueError):
        generate_names(401)


def test_create_sends_token_in_header_not_url():
    session = FakeSession([FakeResponse({"id": "1", "email": "a@tfbnw.net", "password": "pw"})])
    client = GraphClient("123", "secret", "v1.0", session=session)
    user = client.create_test_user("Alex Becker", ["email"])
    method, url, kwargs = session.calls[0]
    assert (method, url) == ("POST", "https://graph.facebook.com/v1.0/123/accounts/test-users")
    assert "secret" not in url
    assert kwargs["headers"]["Authorization"] == "Bearer 123|secret"
    assert kwargs["data"] == {"name": "Alex Becker", "installed": "true", "permissions": "email"}
    assert user["id"] == "1"


def test_graph_error_is_raised_without_leaking_secret():
    session = FakeSession([FakeResponse({"error": {"code": 190, "message": "bad token"}}, 400)])
    client = GraphClient("123", "secret", session=session)
    with pytest.raises(GraphError) as exc:
        client.create_test_user("Alex Becker")
    assert "190" in str(exc.value) and "secret" not in str(exc.value)


def test_list_follows_paging():
    session = FakeSession([
        FakeResponse({"data": [{"id": "1"}], "paging": {"next": "https://graph.facebook.com/next"}}),
        FakeResponse({"data": [{"id": "2"}]}),
    ])
    client = GraphClient("123", "secret", session=session)
    assert [u["id"] for u in client.list_test_users()] == ["1", "2"]
    assert session.calls[1][1] == "https://graph.facebook.com/next"


def test_tracker_appends_across_runs(tmp_path):
    path = tmp_path / "t.xlsx"
    t = Tracker(path)
    t.add("Alex Becker", {"id": 1, "email": "a@x", "password": "p", "login_url": "u"})
    t.save()
    t = Tracker(path)
    t.add("Maria Rossi", {"id": 2})
    t.mark_deleted(1)
    t.save()
    rows = Tracker(path).rows()
    assert [r["name"] for r in rows] == ["Alex Becker", "Maria Rossi"]
    assert [r["status"] for r in rows] == ["deleted", "active"]
    assert rows[0]["password"] == "p"


class StubClient:
    def __init__(self, fail_after=None):
        self.created, self.fail_after = [], fail_after

    def create_test_user(self, name, permissions=()):
        if self.fail_after is not None and len(self.created) >= self.fail_after:
            raise GraphError("limit reached")
        self.created.append(name)
        return {"id": str(len(self.created)), "email": f"u{len(self.created)}@tfbnw.net", "password": "pw"}


def _args(tmp_path, count):
    return argparse.Namespace(count=count, output=str(tmp_path / "t.xlsx"), permissions="", seed=7)


def test_cli_create_writes_tracker(tmp_path):
    assert cli.cmd_create(_args(tmp_path, 3), client=StubClient()) == 0
    assert cli.cmd_create(_args(tmp_path, 3), client=StubClient()) == 0
    rows = Tracker(tmp_path / "t.xlsx").rows()
    assert len(rows) == 6 and len({r["name"] for r in rows}) == 6


def test_cli_create_saves_partial_progress_on_failure(tmp_path):
    assert cli.cmd_create(_args(tmp_path, 5), client=StubClient(fail_after=2)) == 1
    assert len(Tracker(tmp_path / "t.xlsx").rows()) == 2


def test_cli_rejects_bad_count(tmp_path):
    with pytest.raises(SystemExit):
        cli.cmd_create(_args(tmp_path, 0), client=StubClient())
