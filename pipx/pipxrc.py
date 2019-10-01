import json
from pathlib import Path
from typing import List, Dict, Union, NamedTuple

from pipx.Venv import PipxVenvMetadata


class JsonEncoderPipx(json.JSONEncoder):
    def default(self, obj):
        # only handles what json.JSONEncoder doesn't understand by default
        if isinstance(obj, Path):
            return {"__type__": "Path", "__Path__": str(obj)}
        return super().default(obj)


def _json_decoder_object_hook(json_dict):
    if json_dict.get("__type__", None) == "Path" and "__Path__" in json_dict:
        return Path(json_dict["__Path__"])
    return json_dict


class InjPkg(NamedTuple):
    pip_args: List[str]
    verbose: bool
    include_apps: bool
    include_dependencies: bool
    force: bool


class InstallOpts(NamedTuple):
    pip_args: Union[List[str], None]
    venv_args: Union[List[str], None]
    include_dependencies: Union[bool, None]


class PipxrcInfo:
    def __init__(self):
        self.package_or_url: Union[str, None] = None
        self.install: InstallOpts = InstallOpts(
            pip_args=None, venv_args=None, include_dependencies=None
        )
        self.venv_metadata: Union[PipxVenvMetadata, None] = None
        self.injected_packages: Union[Dict[str, InjPkg], None] = None
        self._pipxrc_version: str = "0.1"

    def to_dict(self):
        return {
            "package_or_url": self.package_or_url,
            "install": self.install._asdict(),
            "venv_metadata": self.venv_metadata._asdict(),
            "injected_packages": {
                k: v._asdict() for (k, v) in self.injected_packages.items()
            },
            "pipxrc_version": self._pipxrc_version,
        }

    def from_dict(self, pipxrc_info_dict):
        self.package_or_url = pipxrc_info_dict["package_or_url"]
        self.install = InstallOpts(**pipxrc_info_dict["install"])
        self.venv_metadata = PipxVenvMetadata(**pipxrc_info_dict["venv_metadata"])
        self.injected_packages = {
            k: InjPkg(**v) for (k, v) in pipxrc_info_dict["injected_packages"].items()
        }


class Pipxrc:
    def __init__(self, venv_dir: Path, read: bool = True):
        self.venv_dir = venv_dir
        self.pipxrc_info = PipxrcInfo()
        if read:
            self.read()

    def reset(self):
        self.pipxrc_info = PipxrcInfo()

    def get_package_or_url(self, default: str) -> str:
        if self.pipxrc_info.package_or_url is not None:
            return self.pipxrc_info.package_or_url
        else:
            return default

    def get_install_pip_args(self, default: List[str]) -> List[str]:
        if self.pipxrc_info.install.pip_args is not None:
            return self.pipxrc_info.install.pip_args
        else:
            return default

    def get_install_venv_args(self, default: List[str]) -> List[str]:
        if self.pipxrc_info.install.venv_args is not None:
            return self.pipxrc_info.install.venv_args
        else:
            return default

    def get_install_include_dependencies(self, default: bool) -> bool:
        if self.pipxrc_info.install.include_dependencies is not None:
            return self.pipxrc_info.install.include_dependencies
        else:
            return default

    def get_venv_metadata(self, default: PipxVenvMetadata) -> PipxVenvMetadata:
        if self.pipxrc_info.venv_metadata is not None:
            return self.pipxrc_info.venv_metadata
        else:
            return default

    def get_injected_packages(self, default: List) -> List:
        if self.pipxrc_info.injected_packages is not None:
            injected_packages = []
            for package in self.pipxrc_info.injected_packages:
                package_info = {"package": package}
                package_info.update(
                    self.pipxrc_info.injected_packages[package]._asdict()
                )
                injected_packages.append(package_info)
            return injected_packages
        else:
            return default

    def set_package_or_url(self, package_or_url: str):
        # TODO 20190923: if package_or_url is a local path, we need to make it
        #   an absolute path
        self.pipxrc_info.package_or_url = package_or_url

    def set_venv_metadata(self, venv_metadata: PipxVenvMetadata):
        self.pipxrc_info.venv_metadata = venv_metadata

    def set_install_options(
        self, pip_args: List, venv_args: List, include_dependencies: bool
    ):
        self.pipxrc_info.install = InstallOpts(
            pip_args=pip_args,
            venv_args=venv_args,
            include_dependencies=include_dependencies,
        )

    def add_injected_package(
        self,
        package: str,
        pip_args: List,
        verbose: bool,
        include_apps: bool,
        include_dependencies: bool,
        force: bool,
    ):
        if self.pipxrc_info.injected_packages is None:
            self.pipxrc_info.injected_packages = {}

        self.pipxrc_info.injected_packages[package] = InjPkg(
            pip_args=pip_args,
            verbose=verbose,
            include_apps=include_apps,
            include_dependencies=include_dependencies,
            force=force,
        )

    def write(self):
        # If writing out, make sure injected_packages is not None, so next
        #   successful read of pipxrc does not use default in
        #   get_injected_packages()
        if self.pipxrc_info.injected_packages is None:
            self.pipxrc_info.injected_packages = {}

        # TODO 20190919: raise exception on failure?
        with open(self.venv_dir / "pipxrc", "w") as pipxrc_fh:
            json.dump(
                self.pipxrc_info.to_dict(),
                pipxrc_fh,
                indent=4,
                sort_keys=True,
                cls=JsonEncoderPipx,
            )

    def read(self):
        try:
            with open(self.venv_dir / "pipxrc", "r") as pipxrc_fh:
                self.pipxrc_info.from_dict(
                    json.load(pipxrc_fh, object_hook=_json_decoder_object_hook)
                )
        except IOError:  # Reset self.pipxrc_info if problem reading
            self.reset()
            return
