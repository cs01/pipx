import json
import logging
import os
import pkgutil
import subprocess
from pathlib import Path
from typing import Dict, List, NamedTuple, Sequence, Union

from pipx.animate import animate
from pipx.constants import DEFAULT_PYTHON, PIPX_SHARED_LIBS, PIPX_SHARED_PTH
from pipx.util import WINDOWS, PipxError, rmdir, get_venv_paths


class SharedLibs:
    def __init__(self):
        self.root = PIPX_SHARED_LIBS
        self.bin_path, self.python_path = get_venv_paths(self.root)
        self._site_packages = None
        self.has_been_updated_this_run = False

    @property
    def site_packages(self) -> Path:
        if self._site_packages is None:
            self._site_packages = _get_site_packages(self.python_path)

        return self._site_packages

    def create(self, pip_args: List[str], verbose: bool = False):
        if not self.root.exists():
            with animate("creating shared libraries", not verbose):
                _run([DEFAULT_PYTHON, "-m", "venv", self.root])
                self.upgrade(pip_args, verbose)

    def upgrade(self, pip_args: List[str], verbose: bool = False):
        # Don't try to upgrade multiple times per run
        if self.has_been_updated_this_run:
            return

        ignored_args = ["--editable"]
        _pip_args = [arg for arg in pip_args if arg not in ignored_args]
        if not verbose:
            _pip_args.append("-q")
        try:
            with animate("upgrading shared libraries", not verbose):
                _run(
                    [
                        self.python_path,
                        "-m",
                        "pip",
                        "--disable-pip-version-check",
                        "install",
                        *_pip_args,
                        "--upgrade",
                        "pip",
                        "setuptools",
                        "wheel",
                    ]
                )
                self.has_been_updated_this_run = True
        except Exception:
            logging.error("Failed to upgrade pip", exc_info=True)


shared_libs = SharedLibs()


class PipxVenvMetadata(NamedTuple):
    binaries: List[str]
    binary_paths: List[Path]
    binaries_of_dependencies: List[str]
    binary_paths_of_dependencies: Dict[str, List[Path]]
    package_version: str
    python_version: str


venv_metadata_inspector_raw = pkgutil.get_data("pipx", "venv_metadata_inspector.py")
assert venv_metadata_inspector_raw is not None, (
    "pipx could not find required file venv_metadata_inspector.py. "
    "Please report this error at https://github.com/pipxproject/pipx. Exiting."
)
VENV_METADATA_INSPECTOR = venv_metadata_inspector_raw.decode("utf-8")


class Venv:
    """Abstraction for a virtual environment with various useful methods for pipx"""

    def __init__(
        self, path: Path, *, verbose: bool = False, python: str = DEFAULT_PYTHON
    ) -> None:
        self.root = path
        self._python = python
        self.bin_path, self.python_path = get_venv_paths(self.root)
        self.verbose = verbose
        self.do_animation = not verbose
        try:
            self._existing = self.root.exists() and next(self.root.iterdir())
        except StopIteration:
            self._existing = False

    @property
    def uses_shared_libs(self):
        if self._existing:
            pth_files = self.root.glob("**/" + PIPX_SHARED_PTH)
            return next(pth_files, None) is not None
        else:
            # always use shared libs when creating a new venv
            return True

    def create_venv(self, venv_args: List[str], pip_args: List[str]) -> None:
        with animate("creating virtual environment", self.do_animation):
            cmd = [self._python, "-m", "venv", "--without-pip"]
            _run(cmd + venv_args + [str(self.root)])
            shared_libs.create(pip_args, self.verbose)
            pipx_pth = _get_site_packages(self.python_path) / PIPX_SHARED_PTH
            pipx_pth.write_text(str(shared_libs.site_packages), encoding="utf-8")

    def safe_to_remove(self) -> bool:
        return not self._existing

    def remove_venv(self) -> None:
        if self.safe_to_remove():
            rmdir(self.root)
        else:
            logging.warning(
                f"Not removing existing venv {self.root} because "
                "it was not created in this session"
            )

    def upgrade_packaging_libraries(self, pip_args: List[str]) -> None:
        if self.uses_shared_libs:
            shared_libs.upgrade(pip_args, self.verbose)
        else:
            # TODO: setuptools and wheel? Original code didn't bother
            # but shared libs code does.
            self.upgrade_package("pip", pip_args)

    def install_package(self, package_or_url: str, pip_args: List[str]) -> None:
        with animate(f"installing package {package_or_url!r}", self.do_animation):
            if pip_args is None:
                pip_args = []
            cmd = ["install"] + pip_args + [package_or_url]
            self._run_pip(cmd)

    def get_venv_metadata_for_package(self, package: str) -> PipxVenvMetadata:

        data = json.loads(
            _get_script_output(
                self.python_path, VENV_METADATA_INSPECTOR, package, str(self.bin_path)
            )
        )
        data["binary_paths"] = [Path(p) for p in data["binary_paths"]]

        data["binaries_of_dependencies"] = []
        for dep, raw_paths in data["binary_paths_of_dependencies"].items():
            paths = [Path(raw_path) for raw_path in raw_paths]
            data["binary_paths_of_dependencies"][dep] = paths
            data["binaries_of_dependencies"] += [path.name for path in paths]

        if WINDOWS:
            windows_bin_paths = set()
            for binary in data["binary_paths"]:
                # windows has additional files staring with the same name that are required
                # to run the binary
                for win_exec in binary.parent.glob(f"{binary.name}*"):
                    windows_bin_paths.add(win_exec)
            data["binary_paths"] = list(windows_bin_paths)
        return PipxVenvMetadata(**data)

    def get_python_version(self) -> str:
        return (
            subprocess.run([str(self.python_path), "--version"], stdout=subprocess.PIPE)
            .stdout.decode()
            .strip()
        )

    def run_binary(self, binary: str, binary_args: List[str]):
        cmd = [str(self.bin_path / binary)] + binary_args
        try:
            return _run(cmd, check=False)
        except KeyboardInterrupt:
            pass

    def upgrade_package(self, package_or_url: str, pip_args: List[str]):
        self._run_pip(["install"] + pip_args + ["--upgrade", package_or_url])

    def _run_pip(self, cmd):
        cmd = [self.python_path, "-m", "pip"] + cmd
        if not self.verbose:
            cmd.append("-q")
        return _run(cmd)


def _run(cmd: Sequence[Union[str, Path]], check=True) -> int:
    """Run arbitrary command as subprocess"""

    cmd_str = " ".join(str(c) for c in cmd)
    logging.info(f"running {cmd_str}")
    # windows cannot take Path objects, only strings
    cmd_str_list = [str(c) for c in cmd]
    returncode = subprocess.run(cmd_str_list).returncode
    if check and returncode:
        raise PipxError(f"{cmd_str!r} failed")
    return returncode


def _get_script_output(interpreter: Path, script: str, *args) -> str:
    # Make sure that Python writes output in UTF-8
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    output = subprocess.run(
        [str(interpreter), "-c", script, *args], stdout=subprocess.PIPE, env=env
    ).stdout.decode(encoding="utf-8")
    return output


def _get_site_packages(python: Path) -> Path:
    output = _get_script_output(
        python, "import sysconfig; print(sysconfig.get_path('purelib'))"
    )
    return Path(output.strip())
