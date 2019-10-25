import json
import logging
from pathlib import Path
import re
import textwrap
from typing import List, Dict, NamedTuple, Any, Optional, TypeVar

from pipx.Venv import PipxVenvMetadata, Venv


PIPX_INFO_FILENAME = "pipxrc.json"


class JsonEncoderHandlesPath(json.JSONEncoder):
    def default(self, obj):
        # only handles what json.JSONEncoder doesn't understand by default
        if isinstance(obj, Path):
            return {"__type__": "Path", "__Path__": str(obj)}
        return super().default(obj)


def _json_decoder_object_hook(json_dict):
    if json_dict.get("__type__", None) == "Path" and "__Path__" in json_dict:
        return Path(json_dict["__Path__"])
    return json_dict


# Used for consistent types of multiple kinds
Multi = TypeVar("Multi")


class InjectedPackage(NamedTuple):
    pip_args: List[str]
    verbose: bool
    include_apps: bool
    include_dependencies: bool
    force: bool


class InstallOptions(NamedTuple):
    pip_args: Optional[List[str]]
    venv_args: Optional[List[str]]
    include_dependencies: Optional[bool]


# PipxrcInfo members start with the value None to indicate the information is
#   missing. This means either a pipxrc.json file has never been read, or a new
#   PipxrcInfo object was created and the information was not filled in
#   properly.
class PipxrcInfo:
    def __init__(self):
        self.package_or_url: Optional[str] = None
        self.install: InstallOptions = InstallOptions(
            pip_args=None, venv_args=None, include_dependencies=None
        )
        self.venv_metadata: Optional[PipxVenvMetadata] = None
        self.injected_packages: Optional[Dict[str, InjectedPackage]] = None
        self._pipxrc_version: str = "0.1"

    def to_dict(self) -> Dict[str, Any]:
        venv_metadata: Optional[Dict[str, Any]]
        injected_packages: Optional[Dict[str, Dict[str, Any]]]

        if self.venv_metadata is not None:
            venv_metadata = self.venv_metadata._asdict()
        else:
            venv_metadata = None
        if self.injected_packages is not None:
            injected_packages = {
                k: v._asdict() for (k, v) in self.injected_packages.items()
            }
        else:
            injected_packages = None

        return {
            "package_or_url": self.package_or_url,
            "install": self.install._asdict(),
            "venv_metadata": venv_metadata,
            "injected_packages": injected_packages,
            "pipxrc_version": self._pipxrc_version,
        }

    def from_dict(self, pipxrc_info_dict) -> None:
        self.package_or_url = pipxrc_info_dict["package_or_url"]
        self.install = InstallOptions(**pipxrc_info_dict["install"])
        self.venv_metadata = PipxVenvMetadata(**pipxrc_info_dict["venv_metadata"])
        self.injected_packages = {
            k: InjectedPackage(**v)
            for (k, v) in pipxrc_info_dict["injected_packages"].items()
        }


class Pipxrc:
    def __init__(self, venv_dir: Path, read: bool = True):
        self.venv_dir = venv_dir
        self.pipxrc_info = PipxrcInfo()
        if read:
            self.read()

    def reset(self) -> None:
        self.pipxrc_info = PipxrcInfo()

    def _val_or_default(self, value: Optional[Multi], default: Multi) -> Multi:
        if value is not None:
            return value
        else:
            return default

    def get_package_or_url(self, default: str) -> str:
        return self._val_or_default(self.pipxrc_info.package_or_url, default)

    def get_install_pip_args(self, default: List[str]) -> List[str]:
        return self._val_or_default(self.pipxrc_info.install.pip_args, default)

    def get_install_venv_args(self, default: List[str]) -> List[str]:
        return self._val_or_default(self.pipxrc_info.install.venv_args, default)

    def get_install_include_dependencies(self, default: bool) -> bool:
        return self._val_or_default(
            self.pipxrc_info.install.include_dependencies, default
        )

    def get_venv_metadata(self, default: PipxVenvMetadata) -> PipxVenvMetadata:
        return self._val_or_default(self.pipxrc_info.venv_metadata, default)

    def get_injected_packages(
        self, default: Dict[str, InjectedPackage]
    ) -> Dict[str, InjectedPackage]:
        return self._val_or_default(self.pipxrc_info.injected_packages, default)

    def set_package_or_url(self, package_or_url: str) -> None:
        # if package_or_url is a local path, it MUST be an absolute path
        self.pipxrc_info.package_or_url = package_or_url

    def set_venv_metadata(self, venv_metadata: PipxVenvMetadata) -> None:
        self.pipxrc_info.venv_metadata = venv_metadata

    def set_install_options(
        self, pip_args: List[str], venv_args: List[str], include_dependencies: bool
    ) -> None:
        self.pipxrc_info.install = InstallOptions(
            pip_args=pip_args,
            venv_args=venv_args,
            include_dependencies=include_dependencies,
        )

    def add_injected_package(
        self,
        package: str,
        pip_args: List[str],
        verbose: bool,
        include_apps: bool,
        include_dependencies: bool,
        force: bool,
    ) -> None:
        if self.pipxrc_info.injected_packages is None:
            self.pipxrc_info.injected_packages = {}

        self.pipxrc_info.injected_packages[package] = InjectedPackage(
            pip_args=pip_args,
            verbose=verbose,
            include_apps=include_apps,
            include_dependencies=include_dependencies,
            force=force,
        )

    def write(self) -> None:
        # If writing out, make sure injected_packages is not None, so next
        #   successful read of pipxrc does not use default in
        #   get_injected_packages()
        if self.pipxrc_info.injected_packages is None:
            self.pipxrc_info.injected_packages = {}

        try:
            with open(self.venv_dir / PIPX_INFO_FILENAME, "w") as pipxrc_fh:
                json.dump(
                    self.pipxrc_info.to_dict(),
                    pipxrc_fh,
                    indent=4,
                    sort_keys=True,
                    cls=JsonEncoderHandlesPath,
                )
        except IOError:
            logging.warning(
                textwrap.fill(
                    f"Unable to write {PIPX_INFO_FILENAME} to {self.venv_dir}. "
                    f"This may cause future pipx operations involving "
                    f"{self.venv_dir.name} to fail or behave incorrectly.",
                    width=79,
                )
            )
            pass

    def read(self) -> None:
        try:
            with open(self.venv_dir / PIPX_INFO_FILENAME, "r") as pipxrc_fh:
                self.pipxrc_info.from_dict(
                    json.load(pipxrc_fh, object_hook=_json_decoder_object_hook)
                )
        except IOError:  # Reset self.pipxrc_info if problem reading
            logging.warning(
                textwrap.fill(
                    f"Unable to read {PIPX_INFO_FILENAME} in {self.venv_dir}. "
                    f"This may cause this or future pipx operations involving "
                    f"{self.venv_dir.name} to fail or behave incorrectly.",
                    width=79,
                )
            )
            self.reset()
            return


def abs_path_if_local(package_or_url: str, venv: Venv, pip_args: List[str]) -> str:
    """Return the absolute path if package_or_url represents a filepath
    and not a pypi package
    """
    pkg_path = Path(package_or_url)
    if not pkg_path.exists():
        # no existing path, must be pypi package or non-existent
        return package_or_url

    # Editable packages are either local or url, non-url must be local.
    # https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs
    if "--editable" in pip_args and pkg_path.exists():
        return str(pkg_path.resolve())

    # https://www.python.org/dev/peps/pep-0508/#names
    valid_pkg_name = bool(
        re.search(r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", package_or_url, re.I)
    )
    if not valid_pkg_name:
        return str(pkg_path.resolve())

    # If all of the above conditions do not return, we may have used a pypi
    #   package.
    # If we find a pypi package with this name installed, assume we just
    #   installed it.
    pip_search_args: List[str]

    # If user-defined pypi index url, then use it for search
    try:
        arg_i = pip_args.index("--index-url")
    except ValueError:
        pip_search_args = []
    else:
        pip_search_args = pip_args[arg_i : arg_i + 2]

    pip_search_result_str = venv.pip_search(package_or_url, pip_search_args)
    pip_search_results = pip_search_result_str.split("\n")

    # Get package_or_url and following related lines from pip search stdout
    pkg_found = False
    pip_search_found = []
    for pip_search_line in pip_search_results:
        if pkg_found:
            if re.search(r"^\s", pip_search_line):
                pip_search_found.append(pip_search_line)
            else:
                break
        elif pip_search_line.startswith(package_or_url):
            pip_search_found.append(pip_search_line)
            pkg_found = True
    pip_found_str = " ".join(pip_search_found)

    if pip_found_str.startswith(package_or_url) and "INSTALLED" in pip_found_str:
        return package_or_url
    else:
        return str(pkg_path.resolve())
