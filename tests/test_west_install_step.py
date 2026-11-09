from pathlib import Path

from spl_west_deps.west_installer import MANIFEST_FILE_NAME, create_execution_context, create_west_install_step

MANIFEST_CONTENT = """\
manifest:
  remotes:
    - name: my_remote
      url-base: https://my.server/scm/my_project
  projects:
    - name: my-dependency
      remote: my_remote
      path: my-dependency
      revision: v1.0.0
"""


def create_variant_manifest(project_root_dir: Path, variant: str) -> None:
    manifest = project_root_dir / "variants" / variant / MANIFEST_FILE_NAME
    manifest.parent.mkdir(parents=True)
    manifest.write_text(MANIFEST_CONTENT)


def test_puts_the_workspace_dir_into_the_step_config(tmp_path: Path) -> None:
    """The Executor compares the step config, so a changed workspace dir installs again instead of being skipped."""
    step = create_west_install_step(create_execution_context(tmp_path, "MYVARIANT"), "MYVARIANT", "custom/path")

    assert step.get_config() == {"workspace_dir": "custom/path", "revision_scoped_paths": "True"}


def test_resolves_a_relative_workspace_dir_against_the_project_root(tmp_path: Path) -> None:
    # While nothing is installed yet, the step lists the workspace dir as its output.
    create_variant_manifest(tmp_path, "MYVARIANT")

    step = create_west_install_step(create_execution_context(tmp_path, "MYVARIANT"), "MYVARIANT", "custom/path")

    assert tmp_path / "custom" / "path" in step.get_outputs()


def test_uses_an_absolute_workspace_dir_as_is(tmp_path: Path) -> None:
    """A workspace outside the project, for example one shared by several builds."""
    project_root_dir = tmp_path / "project"
    workspace_dir = tmp_path / "shared" / "west"
    create_variant_manifest(project_root_dir, "MYVARIANT")

    step = create_west_install_step(create_execution_context(project_root_dir, "MYVARIANT"), "MYVARIANT", workspace_dir.as_posix())

    assert workspace_dir in step.get_outputs()
