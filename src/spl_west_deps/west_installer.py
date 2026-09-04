"""Install the west dependencies of a variant and publish their locations to CMake.

The install itself is done by pypeline's ``WestInstall`` step, which already
merges several manifests, installs them and reports where each dependency
landed. This module only builds the execution context that step reads, and
turns its result into CMake variables.
"""

import re
from pathlib import Path

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger
from py_app_dev.core.runnable import Executor
from pypeline.domain.execution_context import ExecutionContext
from pypeline.domain.external_project import ExternalProject
from pypeline.steps.west_install import WestInstall, WestManifestFile

#: Manifest file name, both at the project root and inside a variant directory.
MANIFEST_FILE_NAME = "west.yaml"
#: Directory holding the variant directories, relative to the project root.
VARIANTS_DIR_NAME = "variants"
#: Workspace the dependencies are installed into, relative to the project root.
#: Every variant shares it. Two variants pinning one dependency at two revisions
#: do not collide, because the revision is part of each install path.
WORKSPACE_DIR = "build/modules"
#: Name this package registers its data under, shown as the provider in the registry.
PROVIDER_NAME = "spl_west_deps"


def install_dependencies(project_root_dir: Path, variant: str, output_file: Path) -> None:
    """Install the west dependencies of the variant and write the CMake file."""
    logger.info(f"Installing the west dependencies of variant {variant}")
    execution_context = create_execution_context(project_root_dir, variant)

    # The step collects its manifests in __init__, so the variant manifest must
    # already be in the data registry by now.
    step = WestInstall(
        execution_context,
        group_name=variant,
        config={"workspace_dir": WORKSPACE_DIR, "revision_scoped_paths": True},
    )

    # The Executor skips the west calls while the manifests and the installed
    # directories are unchanged. Without it every CMake configuration would
    # fetch again, and CMake configures often.
    exit_code = Executor(cache_dir=step.output_dir).execute(step)
    if exit_code:
        raise UserNotificationException(f"The WestInstall step failed with exit code {exit_code}.")

    # Publishes one ExternalProject per dependency. It reads the step's result
    # file, so the list is complete even when the step itself was skipped.
    step.update_execution_context()

    write_cmake_file(output_file, execution_context.data_registry.find_data(ExternalProject))


def create_execution_context(project_root_dir: Path, variant: str) -> ExecutionContext:
    """Create the execution context the WestInstall step runs in."""
    execution_context = ExecutionContext(project_root_dir=project_root_dir)

    variant_manifest = project_root_dir / VARIANTS_DIR_NAME / variant / MANIFEST_FILE_NAME
    if variant_manifest.is_file():
        logger.info(f"Found variant west manifest: {variant_manifest}")
        # The step merges the project root manifest first and the registered
        # manifests after it, so this one overrides the root by project name.
        execution_context.data_registry.insert(WestManifestFile.from_file(variant_manifest), provider=PROVIDER_NAME)
    else:
        logger.info(f"Variant {variant} has no {MANIFEST_FILE_NAME}. Only the project root manifest is used.")

    return execution_context


def cmake_variable_name(project_name: str) -> str:
    """Return the CMake variable holding a dependency's install path.

    A manifest project name is not a legal CMake identifier (``-`` is the common
    case), so every character which is not a letter or a digit becomes an
    underscore: ``brightness-controller`` -> ``MODULE_BRIGHTNESS_CONTROLLER_PATH``.
    """
    return f"MODULE_{re.sub(r'[^A-Z0-9]+', '_', project_name.upper())}_PATH"


def write_cmake_file(output_file: Path, projects: list[ExternalProject]) -> None:
    """Write the CMake file that ``index.cmake`` includes."""
    lines = ["# West Dependencies Extension CMake Variables"]
    for project in projects:
        variable = cmake_variable_name(project.name)
        logger.info(f"{variable} = {project.path}")
        lines.append(f"set({variable} {project.path.as_posix()})")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines) + "\n")
    logger.info(f"Generated CMake file at {output_file}")
