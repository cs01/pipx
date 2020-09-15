from pathlib import Path
from typing import List, Optional

from pipx import constants
from pipx.commands.common import package_name_from_spec, run_post_install_actions
from pipx.venv import Venv, VenvContainer


def install(
    venv_dir: Optional[Path],
    package_spec: str,
    local_bin_dir: Path,
    python: str,
    pip_args: List[str],
    venv_args: List[str],
    verbose: bool,
    *,
    force: bool,
    include_dependencies: bool,
    suffix: Optional[str] = None,
):
    """ TODO: Description:
                Create venv_name of package_name+suffix
                Install package_name using spec package_or_url
    """
    # package_spec is anything pip-installable, including package_name, vcs spec,
    #   zip file, or tar.gz file.

    package_name = package_name_from_spec(
        package_spec, python, pip_args=pip_args, verbose=verbose
    )
    if venv_dir is None:
        venv_container = VenvContainer(constants.PIPX_LOCAL_VENVS)
        venv_dir = venv_container.get_venv_dir(package_name)
        if suffix is not None:
            venv_dir = venv_dir.parent / f"{venv_dir.stem}{suffix}"

    venv_name = venv_dir.name

    try:
        exists = venv_dir.exists() and next(venv_dir.iterdir())
    except StopIteration:
        exists = False

    if exists:
        if force:
            print(f"Installing to existing directory {str(venv_dir)!r}")
        else:
            print(
                f"{venv_name!r} already seems to be installed. "
                f"Not modifying existing installation in {str(venv_dir)!r}. "
                "Pass '--force' to force installation."
            )
            return

    venv = Venv(venv_dir, python=python, verbose=verbose)
    try:
        venv.create_venv(venv_args, pip_args)
        venv.install_package(
            package=package_name,
            package_or_url=package_spec,
            pip_args=pip_args,
            include_dependencies=include_dependencies,
            include_apps=True,
            is_main_package=True,
            suffix=suffix or "",
        )
        run_post_install_actions(
            venv,
            package_name,
            local_bin_dir,
            venv_dir,
            include_dependencies,
            force=force,
        )
    except (Exception, KeyboardInterrupt):
        print("")
        venv.remove_venv()
        raise
