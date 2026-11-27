"""The command-line entry point and the built wheel."""

import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from sages_mcp import __main__ as entry

ROOT = Path(__file__).resolve().parents[1]


def test_defaults_to_stdio() -> None:
    assert entry.parse_args([]).transport == "stdio"


def test_streamable_http_takes_a_port() -> None:
    args = entry.parse_args(["--transport", "streamable-http", "--port", "9100"])
    assert (args.transport, args.port) == ("streamable-http", 9100)


def test_unknown_transport_is_refused() -> None:
    with pytest.raises(SystemExit):
        entry.parse_args(["--transport", "carrier-pigeon"])


def test_main_runs_the_server_on_the_chosen_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeServer:
        def run(self, transport: str = "stdio", **kwargs: object) -> None:
            calls.append((transport, kwargs))

    monkeypatch.setattr(entry, "build_server", lambda: FakeServer())
    assert entry.main([]) == 0
    assert entry.main(["--transport", "streamable-http", "--port", "9100"]) == 0
    assert calls == [("stdio", {}), ("streamable-http", {"port": 9100})]


def test_main_reports_missing_content_without_a_traceback(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def broken() -> object:
        raise RuntimeError("Sages content not found")

    monkeypatch.setattr(entry, "build_server", broken)
    assert entry.main([]) == 1
    assert "Sages content not found" in capsys.readouterr().err


def test_wheel_bundles_content(tmp_path: Path) -> None:
    if shutil.which("uv") is None:
        pytest.skip("uv is not on PATH")
    built = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert built.returncode == 0, built.stderr
    (wheel,) = tmp_path.glob("sages_mcp-*.whl")
    names = set(zipfile.ZipFile(wheel).namelist())
    for expected in (
        "sages_mcp/_data/skills/epictetus/SKILL.md",
        "sages_mcp/_data/skills/epictetus/passages.jsonl",
        "sages_mcp/_data/skills/sages/roster.json",
        "sages_mcp/_data/sources/laozi/legge-tao-teh-king.txt",
        "sages_mcp/server.py",
    ):
        assert expected in names, expected
    assert not any(name.startswith("sages_mcp/_data/sources/munger") for name in names)
