import sys
from pathlib import Path

import typer
from py_app_dev.core.logging import logger

from spl_west_deps.west_installer import install_dependencies

package_name = "spl_west_deps"

app = typer.Typer(name=package_name, help="An spl-core extension to install the west dependencies of a variant", add_completion=False)


@app.callback(invoke_without_command=True)
def version(version: bool = typer.Option(None, "--version", "-v", is_eager=True, help="Show version and exit.")) -> None:
    """Print package version and exit when --version supplied."""
    if version:
        from spl_west_deps import __version__

        typer.echo(__version__)
        raise typer.Exit()


@app.command()
def generate(
    project_root_dir: Path = typer.Option(..., "--project-root-dir", help="The project root directory."),  # noqa: B008
    variant: str = typer.Option(..., "--variant", help="The variant of the project."),
    output_file: Path = typer.Option(..., "--output-file", help="The CMake file to generate."),  # noqa: B008
) -> None:
    """Install the west dependencies of this variant and generate the CMake file."""
    logger.info("[CLI] generate command invoked")
    try:
        install_dependencies(project_root_dir, variant, output_file)
        logger.info("[CLI] generate command completed successfully")
    except Exception as e:
        logger.error(f"[CLI] generate command failed: {e}")
        typer.echo(f"Error installing west dependencies: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    app()
