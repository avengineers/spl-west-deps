from pathlib import Path

from pypeline.domain.external_project import ExternalProject
from pypeline.steps.west_install import WestManifestFile

from spl_west_deps.west_installer import (
    MANIFEST_FILE_NAME,
    create_execution_context,
    write_cmake_file,
)

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


def create_variant_manifest(project_root_dir: Path, variant: str) -> Path:
    manifest = project_root_dir / "variants" / variant / MANIFEST_FILE_NAME
    manifest.parent.mkdir(parents=True)
    manifest.write_text(MANIFEST_CONTENT)
    return manifest


def test_registers_the_variant_manifest(tmp_path: Path) -> None:
    """The step reads the registered manifests after the project root one, so this overrides it."""
    create_variant_manifest(tmp_path, "MYVARIANT")

    execution_context = create_execution_context(tmp_path, "MYVARIANT")

    manifests = execution_context.data_registry.find_data(WestManifestFile)
    assert len(manifests) == 1
    assert [project.name for project in manifests[0].payload.projects] == ["my-dependency"]


def test_registers_nothing_when_the_variant_has_no_manifest(tmp_path: Path) -> None:
    """A variant without a manifest uses the project root manifest alone."""
    execution_context = create_execution_context(tmp_path, "MYVARIANT")

    assert execution_context.data_registry.find_data(WestManifestFile) == []


def test_creates_a_cmake_variable_per_dependency(tmp_path: Path) -> None:
    """A project name is not a legal CMake identifier, so it is sanitized."""
    output_file = tmp_path / "build" / "spl_west_deps.cmake"
    projects = [
        ExternalProject(name="brightness-controller", revision="v0.5.0", path=tmp_path / "brightness-controller" / "v0.5.0"),
        ExternalProject(name="my_dependency", revision="v1.0.0", path=tmp_path / "my_dependency" / "v1.0.0"),
    ]

    write_cmake_file(output_file, projects)

    content = output_file.read_text()
    assert f"set(MODULE_BRIGHTNESS_CONTROLLER_PATH {(tmp_path / 'brightness-controller' / 'v0.5.0').as_posix()})" in content
    assert f"set(MODULE_MY_DEPENDENCY_PATH {(tmp_path / 'my_dependency' / 'v1.0.0').as_posix()})" in content


def test_creates_an_empty_cmake_file_without_dependencies(tmp_path: Path) -> None:
    """A project with no dependencies at all must still produce an includable file."""
    output_file = tmp_path / "build" / "spl_west_deps.cmake"

    write_cmake_file(output_file, [])

    assert output_file.exists()
    assert "set(" not in output_file.read_text()
