import datetime
import hashlib
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path
from shutil import which
from typing import List, Optional, Union

try:
    from importlib.metadata import Distribution, EntryPoint
except ImportError:
    from importlib_metadata import Distribution, EntryPoint  # type: ignore

from pipx import constants
from pipx.commands.common import package_name_from_spec
from pipx.constants import TEMP_VENV_EXPIRATION_THRESHOLD_DAYS
from pipx.emojies import hazard
from pipx.util import (
    WINDOWS,
    PipxError,
    exec_app,
    get_pypackage_bin_path,
    get_site_packages,
    pipx_wrap,
    rmdir,
    run_pypackage_bin,
)
from pipx.venv import Venv

logger = logging.getLogger(__name__)


VENV_EXPIRED_FILENAME = "pipx_expired_venv"


def run(
    app: str,
    package_or_url: str,
    app_args: List[str],
    python: str,
    pip_args: List[str],
    venv_args: List[str],
    pypackages: bool,
    verbose: bool,
    use_cache: bool,
) -> None:
    """Installs venv to temporary dir (or reuses cache), then runs app from
    package
    """

    if urllib.parse.urlparse(app).scheme:
        if not app.endswith(".py"):
            raise PipxError(
                """
                pipx will only execute apps from the internet directly if they
                end with '.py'. To run from an SVN, try pipx --spec URL BINARY
                """
            )
        logger.info("Detected url. Downloading and executing as a Python file.")

        content = _http_get_request(app)
        # This never returns
        exec_app([str(python), "-c", content])

    elif which(app):
        logger.warning(
            pipx_wrap(
                f"""
                {hazard}  {app} is already on your PATH and installed at
                {which(app)}. Downloading and running anyway.
                """,
                subsequent_indent=" " * 4,
            )
        )

    pypackage_bin_path = get_pypackage_bin_path(app)
    if pypackage_bin_path.exists():
        logger.info(
            f"Using app in local __pypackages__ directory at {str(pypackage_bin_path)}"
        )
        # This never returns
        run_pypackage_bin(pypackage_bin_path, app_args)
    if pypackages:
        raise PipxError(
            f"""
            '--pypackages' flag was passed, but {str(pypackage_bin_path)!r} was
            not found. See https://github.com/cs01/pythonloc to learn how to
            install here, or omit the flag.
            """
        )

    venv_dir = _get_temporary_venv_path(package_or_url, python, pip_args, venv_args)

    venv = Venv(venv_dir)
    bin_path = venv.bin_path / app
    _prepare_venv_cache(venv, bin_path, use_cache)

    entry_point = _find_entry_point(venv, app)
    if entry_point is not None:
        logger.info(f"Reusing cached venv {venv_dir}")
        # This never returns
        venv.run_entry_point(entry_point, app_args)

    if bin_path.exists():
        logger.info(f"Reusing cached venv {venv_dir}")
        # This never returns
        venv.run_app(app, app_args)

    logger.info(f"venv location is {venv_dir}")
    # This never returns
    _download_and_run(
        Path(venv_dir),
        package_or_url,
        app,
        app_args,
        python,
        pip_args,
        venv_args,
        use_cache,
        verbose,
    )


def _find_entry_point(venv: Venv, app: str) -> Optional[EntryPoint]:
    if not venv.python_path.exists():
        return None
    site_packages = get_site_packages(venv.python_path)
    for dist in Distribution.discover(path=[str(site_packages)]):
        for ep in dist.entry_points:
            if ep.group == "pipx.run" and ep.name == app:
                return ep
    return None


def _resolve_command(
    venv: Venv,
    package_or_url: str,
    app: str,
) -> Union[EntryPoint, str]:
    entry_point = _find_entry_point(venv, app)
    if entry_point is not None:
        return entry_point

    if WINDOWS and not app.endswith(".exe"):
        app = f"{app}.exe"
        logger.info(f"Assuming app is {app!r} (Windows only)")

    if not (venv.bin_path / app).exists():
        apps = venv.pipx_metadata.main_package.apps
        raise PipxError(
            f"""
            '{app}' executable script not found in package '{package_or_url}'.
            Available executable scripts: {', '.join(b for b in apps)}
            """
        )

    return app


def _download_and_run(
    venv_dir: Path,
    package_or_url: str,
    app: str,
    app_args: List[str],
    python: str,
    pip_args: List[str],
    venv_args: List[str],
    use_cache: bool,
    verbose: bool,
) -> None:
    venv = Venv(venv_dir, python=python, verbose=verbose)
    venv.create_venv(venv_args, pip_args)

    if venv.pipx_metadata.main_package.package is not None:
        package = venv.pipx_metadata.main_package.package
    else:
        package = package_name_from_spec(
            package_or_url, python, pip_args=pip_args, verbose=verbose
        )

    venv.install_package(
        package=package,
        package_or_url=package_or_url,
        pip_args=pip_args,
        include_dependencies=False,
        include_apps=True,
        is_main_package=True,
    )

    command = _resolve_command(venv, package_or_url, app)

    if not use_cache:
        # Let future _remove_all_expired_venvs know to remove this
        (venv_dir / VENV_EXPIRED_FILENAME).touch()

    # These never return
    if isinstance(command, EntryPoint):
        venv.run_entry_point(command, app_args)
    else:
        venv.run_app(app, app_args)


def _get_temporary_venv_path(
    package_or_url: str, python: str, pip_args: List[str], venv_args: List[str]
) -> Path:
    """Computes deterministic path using hashing function on arguments relevant
    to virtual environment's end state. Arguments used should result in idempotent
    virtual environment. (i.e. args passed to app aren't relevant, but args
    passed to venv creation are.)
    """
    m = hashlib.sha256()
    m.update(package_or_url.encode())
    m.update(python.encode())
    m.update("".join(pip_args).encode())
    m.update("".join(venv_args).encode())
    venv_folder_name = m.hexdigest()[0:15]  # 15 chosen arbitrarily
    return Path(constants.PIPX_VENV_CACHEDIR) / venv_folder_name


def _is_temporary_venv_expired(venv_dir: Path) -> bool:
    created_time_sec = venv_dir.stat().st_ctime
    current_time_sec = time.mktime(datetime.datetime.now().timetuple())
    age = current_time_sec - created_time_sec
    expiration_threshold_sec = 60 * 60 * 24 * TEMP_VENV_EXPIRATION_THRESHOLD_DAYS
    return age > expiration_threshold_sec or (venv_dir / VENV_EXPIRED_FILENAME).exists()


def _prepare_venv_cache(venv: Venv, bin_path: Path, use_cache: bool) -> None:
    venv_dir = venv.root
    if not use_cache and bin_path.exists():
        logger.info(f"Removing cached venv {str(venv_dir)}")
        rmdir(venv_dir)
    _remove_all_expired_venvs()


def _remove_all_expired_venvs() -> None:
    for venv_dir in Path(constants.PIPX_VENV_CACHEDIR).iterdir():
        if _is_temporary_venv_expired(venv_dir):
            logger.info(f"Removing expired venv {str(venv_dir)}")
            rmdir(venv_dir)


def _http_get_request(url: str) -> str:
    try:
        res = urllib.request.urlopen(url)
        charset = res.headers.get_content_charset() or "utf-8"  # type: ignore
        return res.read().decode(charset)
    except Exception as e:
        logger.debug("Uncaught Exception:", exc_info=True)
        raise PipxError(str(e))
