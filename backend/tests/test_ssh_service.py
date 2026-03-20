import pytest

from app.services.ssh_service import SSHClient


class _FakeRunResult:
    def __init__(self, exit_status=0, stdout="", stderr=""):
        self.exit_status = exit_status
        self.stdout = stdout
        self.stderr = stderr


class _FakeConnection:
    def __init__(self):
        self.closed = False
        self.commands = []

    async def run(self, command: str):
        self.commands.append(command)
        return _FakeRunResult(exit_status=0, stdout="ok", stderr="")

    def close(self):
        self.closed = True

    async def wait_closed(self):
        return None


@pytest.mark.asyncio
async def test_ssh_client_connect_uses_asyncssh_connect(monkeypatch):
    calls = {}
    fake_conn = _FakeConnection()

    async def fake_connect(**kwargs):
        calls.update(kwargs)
        return fake_conn

    monkeypatch.setattr("app.services.ssh_service.asyncssh.connect", fake_connect)

    client = SSHClient(
        host="10.0.0.2",
        port=22,
        username="root",
        password="secret",
        key_path="~/.ssh/id_rsa",
    )

    ok = await client.connect()
    assert ok is True
    assert calls["host"] == "10.0.0.2"
    assert calls["port"] == 22
    assert calls["username"] == "root"
    assert calls["password"] == "secret"
    assert calls["known_hosts"] is None
    assert calls["client_keys"][0].endswith(".ssh/id_rsa")

    await client.close()
    assert fake_conn.closed is True


@pytest.mark.asyncio
async def test_execute_command_auto_connects(monkeypatch):
    fake_conn = _FakeConnection()

    async def fake_connect(**_kwargs):
        return fake_conn

    monkeypatch.setattr("app.services.ssh_service.asyncssh.connect", fake_connect)

    client = SSHClient(host="10.0.0.3", port=22, username="ubuntu", password="pw")

    # Should automatically connect internally before running the command
    exit_code, stdout, stderr = await client.execute_command("echo hello")

    assert exit_code == 0
    assert stdout == "ok"
    assert stderr == ""
    assert fake_conn.commands == ["echo hello"]
