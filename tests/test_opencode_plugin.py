"""The opencode shim registers the skills folder, once."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / ".opencode" / "plugins" / "sages.js"
DRIVER = """
import * as mod from %(plugin)s;
const plugins = Object.values(mod).filter((value) => typeof value === "function");
const hooks = plugins.length === 1 ? await plugins[0]({}) : null;
const config = { skills: { paths: ["/already/there"] } };
await hooks?.config?.(config);
await hooks?.config?.(config);
console.log(JSON.stringify({
  exportCount: plugins.length,
  hasConfigHook: typeof hooks?.config === "function",
  skillsPaths: config.skills?.paths ?? [],
}));
"""


def run_driver() -> dict[str, object]:
    if shutil.which("node") is None:
        pytest.skip("node is not on PATH")
    driver = DRIVER % {"plugin": json.dumps(PLUGIN.as_uri())}
    result = subprocess.run(
        ["node", "--input-type=module", "-e", driver], capture_output=True, text=True, cwd=ROOT
    )
    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert isinstance(data, dict)
    return data


def test_exports_one_plugin_function_with_a_config_hook() -> None:
    result = run_driver()
    assert result["exportCount"] == 1 and result["hasConfigHook"] is True


def test_adds_the_skills_path_once_and_keeps_existing_paths() -> None:
    assert run_driver()["skillsPaths"] == ["/already/there", str(ROOT / "skills")]
