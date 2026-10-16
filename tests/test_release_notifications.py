"""Execute the workflow's actual inline script without making network requests."""
import json
from pathlib import Path
import textwrap
from unittest.mock import MagicMock
from urllib.error import HTTPError, URLError

import pytest


@pytest.fixture
def run_notification(monkeypatch, tmp_path):
    workflow = Path(".github/workflows/release_notify.yaml").read_text()
    script = textwrap.dedent(workflow.split("python - <<'PY'\n", 1)[1].rsplit("          PY", 1)[0])
    monkeypatch.chdir(tmp_path)
    environment = {
        "PROJECT_NAME": "Example",
        "INPUT_VERSION": "1.2.3",
        "VERSION_SOURCE": "toml",
        "VERSION_PATH": "VERSION",
        "CHANGELOG_PATH": "",
        "RELEASE_SUCCESS": "true",
        "COMMIT_SHA": "abcdef123456",
        "COMMIT_URL": "https://github.com/example/project/commit/abcdef123456",
        "REPOSITORY": "example/project",
        "DISCORD_ROLE_ID": "",
    }
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    sender = MagicMock()
    monkeypatch.setattr("urllib.request.urlopen", sender)

    def run(destinations, fallback=""):
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", destinations)
        monkeypatch.setenv("DISCORD_ROLE_ID", fallback)
        exec(compile(script, "release_notify.yaml", "exec"), {})
        return [json.loads(call.args[0].data) for call in sender.call_args_list]

    run.sender = sender
    return run


def test_legacy_url_with_fallback_role(run_notification):
    payload, = run_notification("https://discord.com/api/webhooks/one/token", "123")
    assert payload["content"].startswith("<@&123> Example 1.2.3 was released successfully.")
    assert payload["allowed_mentions"] == {"parse": [], "roles": ["123"]}


def test_multiple_destinations_override_fallback_and_ignore_blank_lines(run_notification):
    payloads = run_notification(
        " \r\n https://discord.com/api/webhooks/one/token 111 222 111\r\n"
        "\r\nhttps://discord.com/api/webhooks/two/token\t333\n"
        "https://discord.com/api/webhooks/three/token\n", "999"
    )
    assert [p["allowed_mentions"]["roles"] for p in payloads] == [["111", "222"], ["333"], ["999"]]
    assert payloads[0]["content"].startswith("<@&111> <@&222> Example")
    assert "<@&999>" not in payloads[0]["content"]
    requests = [call.args[0] for call in run_notification.sender.call_args_list]
    assert [request.full_url for request in requests] == [
        f"https://discord.com/api/webhooks/{name}/token" for name in ("one", "two", "three")
    ]
    assert all(request.method == "POST" for request in requests)


def test_no_roles_disables_mentions(run_notification):
    payload, = run_notification("https://discord.com/api/webhooks/one/token")
    assert payload["content"].startswith("Example")
    assert payload["allowed_mentions"] == {"parse": [], "roles": []}


@pytest.mark.parametrize("destinations", ["", " \n\t", "https://discord.com/api/webhooks/one/token not-a-role"])
def test_invalid_configuration_fails_before_delivery(run_notification, destinations):
    with pytest.raises(SystemExit):
        run_notification(destinations)
    run_notification.sender.assert_not_called()


@pytest.mark.parametrize("error", [
    HTTPError("https://discord.com/api/webhooks/one/SECRET", 500, "SECRET", {}, None),
    URLError("SECRET"),
])
def test_failure_attempts_remaining_destinations_without_leaking_secrets(run_notification, capsys, error):
    run_notification.sender.side_effect = [error, MagicMock()]
    with pytest.raises(SystemExit, match="One or more Discord notifications failed"):
        run_notification("https://discord.com/api/webhooks/one/SECRET\nhttps://discord.com/api/webhooks/two/token")
    assert run_notification.sender.call_count == 2
    output = capsys.readouterr().out
    assert "SECRET" not in output
    assert "destination 1" in output
    assert "destination 2" in output


def test_changelog_truncation_accounts_for_destination_roles(run_notification, monkeypatch):
    Path("CHANGELOG.md").write_text("## 1.2.3\n" + "Release notes " * 500)
    monkeypatch.setenv("CHANGELOG_PATH", "CHANGELOG.md")
    payloads = run_notification("https://discord.com/api/webhooks/one/token 111 222\nhttps://discord.com/api/webhooks/two/token")
    for payload in payloads:
        assert len(payload["content"]) <= 2000
        assert "Changelog\n" in payload["content"]
        assert "..." in payload["content"]
        assert "Commit: `abcdef1`" in payload["content"]


def test_failed_release_omits_changelog(run_notification, monkeypatch):
    Path("CHANGELOG.md").write_text("## 1.2.3\n" + "Release notes " * 500)
    monkeypatch.setenv("CHANGELOG_PATH", "CHANGELOG.md")
    monkeypatch.setenv("RELEASE_SUCCESS", "false")
    payload, = run_notification("https://discord.com/api/webhooks/one/token 111")
    assert "release failed" in payload["content"]
    assert "Changelog" not in payload["content"]
