from typing import Any

import pytest
from typer.testing import CliRunner

from spl_west_deps import main
from spl_west_deps.main import WORKSPACE_DIR_ENV_VAR, app
from spl_west_deps.west_installer import DEFAULT_WORKSPACE_DIR


@pytest.fixture
def workspace_dirs(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record the workspace dir of each install instead of installing anything."""
    recorded: list[str] = []

    def fake_install_dependencies(*_args: Any, workspace_dir: str) -> None:
        recorded.append(workspace_dir)

    monkeypatch.setattr(main, "install_dependencies", fake_install_dependencies)
    # The developer's or the CI's own setting must not leak into the tests.
    monkeypatch.delenv(WORKSPACE_DIR_ENV_VAR, raising=False)
    return recorded


def run_generate(*extra_args: str, env: dict[str, str] | None = None) -> None:
    result = CliRunner().invoke(
        app,
        ["generate", "--project-root-dir", "root", "--variant", "MYVARIANT", "--output-file", "out.cmake", *extra_args],
        env=env,
    )
    assert result.exit_code == 0, result.output


def test_installs_into_the_default_workspace_dir(workspace_dirs: list[str]) -> None:
    run_generate()

    assert workspace_dirs == [DEFAULT_WORKSPACE_DIR]


def test_installs_into_the_workspace_dir_option(workspace_dirs: list[str]) -> None:
    run_generate("--workspace-dir", "custom/path")

    assert workspace_dirs == ["custom/path"]


def test_installs_into_the_workspace_dir_environment_variable(workspace_dirs: list[str]) -> None:
    run_generate(env={WORKSPACE_DIR_ENV_VAR: "from/env"})

    assert workspace_dirs == ["from/env"]


def test_the_option_overrides_the_environment_variable(workspace_dirs: list[str]) -> None:
    run_generate("--workspace-dir", "custom/path", env={WORKSPACE_DIR_ENV_VAR: "from/env"})

    assert workspace_dirs == ["custom/path"]
