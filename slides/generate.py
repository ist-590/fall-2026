#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "click",
# ]
# ///
from pathlib import Path
import subprocess
from typing import Optional
import click
from click import ClickException

_DEFAULT_TEMPLATE_DIR = "../../common/pandoc-reveal.js/"
_CONFIG_FILE = "slides.config"


def _get_default_source() -> str:
    """
    Priority order:
    1. `_CONFIG_FILE`
    2. Single .md file in current directory
    """
    # 1. Read from `_CONFIG_FILE`
    config_path = Path(_CONFIG_FILE)
    if config_path.exists():
        source = config_path.read_text().strip()
        if source:
            click.echo(f"Using source from {_CONFIG_FILE}: {source}")
            return source

    # 2. Auto-detect single markdown file
    md_files = list(Path.cwd().glob("*.md"))
    if len(md_files) == 1:
        click.echo(f"Auto-detected: {md_files[0].name}")
        return str(md_files[0])
    elif len(md_files) > 1:
        raise ClickException(
            f"Multiple markdown files found: {[f.name for f in md_files]}. "
            f"Create a {_CONFIG_FILE} file or use --source"
        )


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "-s",
    "--source",
    help=f"Source [default: {_CONFIG_FILE} or the .md file]",
    type=click.Path(file_okay=True, exists=True, path_type=Path),
    default=_get_default_source,
)
@click.option(
    "-t",
    "--template-dir",
    help="Template directory",
    show_default=True,
    type=click.Path(dir_okay=True, exists=True, path_type=Path),
    default=_DEFAULT_TEMPLATE_DIR,
)
@click.option("-o", "--overwrite", is_flag=True, default=False, help="Overwrite output")
@click.option(
    "--output", type=click.Path(dir_okay=False, path_type=Path), help="Output file"
)
@click.option(
    "--archive",
    is_flag=True,
    default=False,
    help="Archives the slides (removes speaker notes)",
)
def slides(
    source: Path,
    template_dir: Path,
    overwrite: bool,
    output: Optional[Path],
    archive: bool,
) -> None:
    """
    Generate html (reveal.js) slides from a markdown source.
    """
    # Determine output path
    if not output:
        output = source.parent / f"{source.stem}.html"

    template = template_dir / "template.md"
    code_filter = template_dir / "revealjs-codeblock.lua"

    if not template.exists():
        raise ClickException(f"Template not found: {template}")
    if not code_filter.exists():
        raise ClickException(f"Code filter not found: {code_filter}")
    if output.exists() and not overwrite:
        raise ClickException(f"Unable to overwrite {output}. Use --overwrite flag.")

    # Build command
    cmd = [
        "pandoc",
        "-t",
        "revealjs",
        "-s",
        "--slide-level=0",
        "-L",
        str(code_filter),
        "--template",
        str(template),
        "-o",
        str(output),
        str(source),
    ]

    # Handle archive mode
    if archive:
        prompt = "The archived slides will NOT include any notes. Continue?"
        click.confirm(prompt, default=False, abort=True)

        remove_note_filter = template_dir / "remove-notes.lua"
        if not remove_note_filter.exists():
            raise ClickException(f"Remove notes filter not found: {remove_note_filter}")

        cmd.extend(["-L", str(remove_note_filter)])
        click.echo("Archive mode: Notes will be removed")

    # Run pandoc
    try:
        subprocess.run(cmd, check=True)
        click.echo(f"✓ Successfully generated: {output}")
    except subprocess.CalledProcessError as e:
        raise ClickException(f"Pandoc failed with exit code {e.returncode}")
    except FileNotFoundError:
        raise ClickException("Pandoc not found. Please install pandoc.")


@cli.command()
@click.option(
    "-s",
    "--source",
    help=f"Source [default: {_CONFIG_FILE} or the .md file]",
    type=click.Path(file_okay=True, exists=True, path_type=Path),
    default=_get_default_source,
)
@click.option(
    "-t",
    "--template-dir",
    help="Template directory",
    show_default=True,
    type=click.Path(dir_okay=True, exists=True, path_type=Path),
    default=_DEFAULT_TEMPLATE_DIR,
)
@click.option("--overwrite", is_flag=True, default=False)
@click.option("-o", "--output", type=click.Path(dir_okay=False, path_type=Path))
def notes(
    source: Path, template_dir: Path, overwrite: bool, output: Optional[Path]
) -> None:
    """
    Extract notes from the slides
    """
    # Determine output path
    if not output:
        output = source.parent / f"notes-{source.stem}.md"

    extract_filter = template_dir / "extract-notes-filter.lua"

    # Validate paths
    if not extract_filter.exists():
        raise ClickException(f"Filter not found: {extract_filter}")
    if output.exists() and not overwrite:
        raise ClickException(f"Unable to overwrite {output}. Use --overwrite flag.")

    # Build and run command
    cmd = [
        "pandoc",
        "--lua-filter",
        str(extract_filter),
        "-o",
        str(output),
        str(source),
    ]

    try:
        subprocess.run(cmd, check=True)
        click.echo(f"✓ Successfully extracted notes: {output}")
    except subprocess.CalledProcessError as e:
        raise ClickException(f"Pandoc failed with exit code {e.returncode}")
    except FileNotFoundError:
        raise ClickException("Pandoc not found. Please install pandoc.")


if __name__ == "__main__":
    cli()
