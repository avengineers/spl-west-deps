# spl-west-deps

An spl-core build extension that installs the [west](https://docs.zephyrproject.org/latest/develop/west/index.html)
dependencies of a variant.

The dependencies of an SPL are declared in west manifests: one at the project
root for what every variant needs, and one per variant for what that variant
adds or pins differently. The extension resolves both, installs them, and tells
CMake where they landed, so a variant can consume a dependency without any
consumer hard-coding the workspace layout.

![maintained](https://img.shields.io/badge/maintained-yes-success?style=flat-square)
![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)
![pypeline](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/cuinixam/pypeline/main/assets/badge/v0.json)

The install itself is done by [pypeline](https://github.com/cuinixam/pypeline)'s
`WestInstall` step, which already merges several manifests, installs them and
reports where each dependency landed. This extension builds the execution context
that step reads, and turns its result into CMake variables.

## Installation

Install this via pip (or your favorite package manager):

`pip install spl_west_deps`

Then, in the consuming spl-core project's `CMakeLists.txt`, after `spl.cmake` and
**before** the variant parts are included:

```cmake
include(".venv/Lib/site-packages/spl_west_deps/index.cmake")

include(${PROJECT_SOURCE_DIR}/variants/${VARIANT}/parts.cmake)
```

The order matters: `parts.cmake` calls `spl_add_component()` on components whose
sources come from the dependencies, so the dependencies must be installed first.

Remove any west step from the project's own pipeline when you enable this
extension. Two resolvers writing one workspace fight over the checkouts.

## Usage

The extension needs no CMake target and no command of its own. It runs during the
CMake configuration and defines one variable per dependency:

| Dependency name in the manifest | CMake variable |
| --- | --- |
| `brightness-controller` | `MODULE_BRIGHTNESS_CONTROLLER_PATH` |

A manifest project name is not a legal CMake identifier, so every character which
is not a letter or a digit becomes an underscore. A component consumes the
dependency through the variable and hardcodes no path:

```cmake
spl_add_source(${MODULE_BRIGHTNESS_CONTROLLER_PATH}/export/brightness_controller.c)
```

## Manifests

| File | Scope |
| --- | --- |
| `west.yaml` | Every variant |
| `variants/<VARIANT>/west.yaml` | That variant. Overrides the root manifest by project name |

An overlay can add a dependency and override one, but it cannot remove one. That
follows from merging by project name. So keep the root manifest to what every
variant needs.

Every dependency is installed under its revision, so two variants pinning one
dependency at two revisions get two checkouts instead of fighting over one:

```
build/modules/brightness-controller/generated-code-v0.1.0/
build/modules/brightness-controller/generated-code-v0.5.0/
```

## How it works

Unlike the other spl-core extensions, `index.cmake` does **not**
`cmake_language(DEFER ...)` its work to the end of the CMake configuration: the
dependency sources have to exist before the variant parts are processed. So the
file runs `spl_west_deps generate ...` while it is being included, then
`include()`s the generated `${CMAKE_BINARY_DIR}/spl_west_deps.cmake`.

The `generate` command:

1. Creates a pypeline `ExecutionContext` for the project.
2. Registers `variants/<VARIANT>/west.yaml` in the context's data registry, when
   the variant has one. The `WestInstall` step merges the registered manifests
   after the project root manifest, which is what makes the variant override it.
3. Instantiates `WestInstall` with `revision_scoped_paths` and runs it through
   py-app-dev's `Executor`. The step is skipped while the manifests and the
   installed directories are unchanged, so a repeated CMake configuration costs
   nothing.
4. Reads the `ExternalProject` entries the step publishes and writes one
   `set(MODULE_<NAME>_PATH ...)` per dependency.

Step 4 uses the step's `update_execution_context()`, which reads the step's
result file rather than its in-memory state. That is why the variables are
complete even on a run where the install was skipped.

## Start developing

The project is managed with [uv](https://docs.astral.sh/uv/) and orchestrated by
[pypeline](https://github.com/cuinixam/pypeline). Bootstrap the environment and
run the full pipeline (venv, pre-commit, tests) with:

```shell
pypeline run
```

## Committing changes

This repository uses [commitlint](https://github.com/conventional-changelog/commitlint) for checking if the commit message meets the [conventional commit format](https://www.conventionalcommits.org/en). Commit messages drive the automated release.

## Continuous integration & release

CI runs on **GitHub Actions** (`.github/workflows/ci.yml`): lint (pre-commit),
commitlint, a test matrix (Python 3.10/3.13 × Ubuntu/Windows), and a release job.
Releases are automated with [python-semantic-release](https://python-semantic-release.readthedocs.io/):
merging to `main` bumps the version from the conventional-commit history and
publishes to PyPI (trusted publishing) and GitHub Releases.

## Credits

[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-orange.json)](https://github.com/copier-org/copier)

This package was created with
[Copier](https://copier.readthedocs.io/) and the
[browniebroke/pypackage-template](https://github.com/browniebroke/pypackage-template)
project template.
