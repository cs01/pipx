#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os
from pathlib import Path
from pipx.animate import animate
from pipx.colors import red, bold
import requests
import shlex
import shutil
from shutil import which
import subprocess
import sys
import tempfile
from typing import List, Optional, Union, Sequence
import textwrap
import urllib

try:
    WindowsError
except NameError:
    WINDOWS = False
    stars = "✨ 🌟 ✨"
    hazard = "⚠️"
    sleep = "😴"
else:
    WINDOWS = True
    stars = ""
    hazard = ""
    sleep = ""

DEFAULT_PYTHON = sys.executable
DEFAULT_PIPX_HOME = Path.home() / ".local/pipx/venvs"
DEFAULT_PIPX_BIN_DIR = Path.home() / ".local/bin"
pipx_local_venvs = Path(os.environ.get("PIPX_HOME", DEFAULT_PIPX_HOME)).resolve()
local_bin_dir = Path(os.environ.get("PIPX_BIN_DIR", DEFAULT_PIPX_BIN_DIR)).resolve()
INSTALL_PIPX_URL = "git+https://github.com/cs01/pipx.git"
INSTALL_PIPX_CMD = (
    "curl https://raw.githubusercontent.com/cs01/pipx/master/get-pipx.py | python3"
)
SPEC_HELP = (
    "Specify the exact installation source instead of using PyPI and the package name. "
    "Runs `pip install -U SPEC` instead of `pip install -U PACKAGE`. "
    "For example `--spec {}` or `--spec mypackage==2.0.0.`".format(INSTALL_PIPX_URL)
)
PIPX_DESCRIPTION = textwrap.dedent(
    """
Execute binaries from Python packages.

Binaries can either be run directly or installed globally into isolated venvs.

venv location is {}.
Symlinks to binaries are placed in {}.
These locations can be overridden with the environment variables
PIPX_HOME and PIPX_BIN_DIR, respectively.
""".format(pipx_local_venvs, local_bin_dir)
)
PIPX_USAGE = """
    %(prog)s [--spec SPEC] [--python PYTHON] BINARY [BINARY-ARGS]
    %(prog)s {install, upgrade, upgrade-all, uninstall, uninstall-all, reinstall-all, list} [--help]"""


class PipxError(Exception):
    pass


class Venv:
    def __init__(
        self, path: Path, *, verbose: bool = False, python: str = DEFAULT_PYTHON
    ) -> None:
        self.root = path
        self._python = python
        self.bin_path = path / "bin" if not WINDOWS else path / "Scripts"
        self.python_path = self.bin_path / ("python" if not WINDOWS else "python.exe")
        self.verbose = verbose
        self.do_animation = not verbose

    def create_venv(self) -> None:
        with animate("creating virtual environment", self.do_animation):
            _run([self._python, "-m", "venv", self.root])
            self.upgrade_package("pip")

    def remove_venv(self) -> None:
        rmdir(self.root)

    def install_package(self, package_or_url: str) -> None:
        with animate("installing package '{}'".format(package_or_url), self.do_animation):
            self._run_pip(["install", package_or_url])

    def get_package_dependencies(self, package: str) -> List[str]:
        get_version_script = textwrap.dedent(
            """
        import pkg_resources
        for r in pkg_resources.get_distribution("{}").requires():
            print(r)
        """.format(package)
        )
        return (
            subprocess.run(
                [str(self.python_path), "-c", get_version_script],
                stdout=subprocess.PIPE,
            )
            .stdout.decode()
            .split()
        )

    def get_package_version(self, package: str) -> Optional[str]:
        get_version_script = textwrap.dedent(
            """
        try:
            import pkg_resources
            print(pkg_resources.get_distribution("{}").version)
        except:
            pass
        """.format(package)
        )
        version = (
            subprocess.run(
                [str(self.python_path), "-c", get_version_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            .stdout.decode()
            .strip()
        )
        if version:
            return version
        else:
            return None

    def get_package_binary_paths(self, package: str) -> List[Path]:
        get_binaries_script = textwrap.dedent(
            """
            import pkg_resources
            import sys
            import os
            from pathlib import Path

            dist = pkg_resources.get_distribution("{}")

            bin_path = Path(r"{}")
            binaries = set()
            for section in ['console_scripts', 'gui_scripts']:
                for name in pkg_resources.get_entry_map(dist).get(section, []):
                    binaries.add(name)

            if dist.has_metadata("RECORD"):
                for line in dist.get_metadata_lines("RECORD"):
                    entry = line.split(',')[0]
                    path = (Path(dist.location) / entry).resolve()
                    try:
                        if path.parent.samefile(bin_path):
                            binaries.add(Path(entry).name)
                    except FileNotFoundError:
                        pass

            if dist.has_metadata("installed-files.txt"):
                for line in dist.get_metadata_lines("installed-files.txt"):
                    entry = line.split(',')[0]
                    path = (Path(dist.egg_info) / entry).resolve()
                    try:
                        if path.parent.samefile(bin_path):
                            binaries.add(Path(entry).name)
                    except FileNotFoundError:
                        pass

            [print(b) for b in sorted(binaries)]

        """.format(package, self.bin_path)
        )
        if not Path(self.python_path).exists():
            return []
        binaries = (
            subprocess.run(
                [str(self.python_path), "-c", get_binaries_script],
                stdout=subprocess.PIPE,
            )
            .stdout.decode()
            .split()
        )
        binary_paths = {self.bin_path / b for b in binaries}
        if WINDOWS:
            for binary in binary_paths:
                # windows has additional files staring with the same name that are required
                # to run the binary
                for win_exec in binary.parent.glob(binary.name + "*"):
                    binary_paths.add(win_exec)

        valid_binary_paths = list(filter(lambda p: p.exists(), binary_paths))
        return valid_binary_paths

    def run_binary(self, binary: str, binary_args: List[str]):
        cmd = [str(self.bin_path / binary)] + binary_args
        try:
            return _run(cmd, check=False)
        except KeyboardInterrupt:
            pass

    def upgrade_package(self, package_or_url: str):
        self._run_pip(["install", "--upgrade", package_or_url])

    def _run_pip(self, cmd):
        cmd = [self.python_path, "-m", "pip"] + cmd
        if not self.verbose:
            cmd.append("-q")
        return _run(cmd)


def _run(cmd: Sequence[Union[str, Path]], check=True) -> int:
    cmd_str = " ".join(str(c) for c in cmd)
    logging.info("running %s", cmd_str)
    # windows cannot take Path objects, only strings
    cmd_str_list = [str(c) for c in cmd]
    returncode = subprocess.run(cmd_str_list).returncode
    if check and returncode:
        raise PipxError("'{}' failed".format(cmd_str))
    return returncode


def rmdir(path: Path):
    logging.info("removing directory %s", path)
    if WINDOWS:
        os.system('rmdir /S /Q "{}"'.format(path))
    else:
        shutil.rmtree(str(path))


def mkdir(path: Path) -> None:
    if path.is_dir():
        return
    logging.info("creating directory %s", path)
    path.mkdir(parents=True, exist_ok=True)


def download_and_run(
    venv_dir: Path,
    package: str,
    binary: str,
    binary_args: List[str],
    python: str,
    verbose: bool,
):
    venv = Venv(venv_dir, python=python, verbose=verbose)
    venv.create_venv()
    venv.install_package(package)
    if not (venv.bin_path / binary).exists():
        binaries = venv.get_package_binary_paths(package)
        raise PipxError(
            "{} not found in package {}. Available binaries: {}".format(binary, package, ', '.join(b.name for b in binaries))
        )
    return venv.run_binary(binary, binary_args)


def expose_binaries_globally(
    local_bin_dir: Path, binary_paths: List[Path], package: str
):
    if WINDOWS:
        _copy_package_binaries(local_bin_dir, binary_paths, package)
    else:
        _symlink_package_binaries(local_bin_dir, binary_paths, package)


def _copy_package_binaries(local_bin_dir: Path, binary_paths: List[Path], package: str):
    for src_unresolved in binary_paths:
        src = src_unresolved.resolve()
        binary = src.name
        dest = Path(local_bin_dir / binary)
        if not dest.parent.is_dir():
            mkdir(dest.parent)
        if dest.exists():
            logging.warning("%s  Overwriting file %s with %s", hazard, dest, src)
            dest.unlink()
        shutil.copy(src, dest)


def _symlink_package_binaries(
    local_bin_dir: Path, binary_paths: List[Path], package: str
):
    for b in binary_paths:
        binary = b.name
        symlink_path = Path(local_bin_dir / binary)
        if not symlink_path.parent.is_dir():
            mkdir(symlink_path.parent)

        if symlink_path.exists():
            if symlink_path.samefile(b):
                pass
            else:
                logging.warning(
                    "%s  File exists at %s and points to %s. Not creating.",
                    hazard, symlink_path, symlink_path.resolve()
                )
        else:
            shadow = which(binary)
            symlink_path.symlink_to(b)
            pass
            if shadow:
                logging.warning(
                    "%s  Note: %s was already on your PATH at %s",
                    hazard, binary, shadow
                )


def _list_installed_package(path: Path, *, new_install: bool = False) -> None:
    venv = Venv(path)
    python_path = venv.python_path.resolve()
    package = path.name

    version = venv.get_package_version(package)
    if version is None:
        print("{} is not installed in the venv {}".format(package, path))
        return

    package_binary_paths = venv.get_package_binary_paths(package)
    package_binary_names = [b.name for b in package_binary_paths]

    exposed_binary_paths = get_exposed_binary_paths_for_package(
        venv.bin_path, package_binary_paths, local_bin_dir
    )
    exposed_binary_names = sorted(p.name for p in exposed_binary_paths)
    unavailable_binary_names = sorted(
        set(package_binary_names) - set(exposed_binary_names)
    )

    print(
        "  {} package {}, {}".format('installed' if new_install else '', bold(shlex.quote(package)), version)
    )
    logging.info("    python: %s", python_path)
    if not python_path.exists():
        logging.error("    associated python path %s does not exist!", python_path)

    if new_install and exposed_binary_names:
        print("  These binaries are now globally available")
    for name in exposed_binary_names:
        print("    - {}".format(name))
    for name in unavailable_binary_names:
        print("    - {} (symlink not installed)".format(red(name)))


def list_packages(pipx_local_venvs: Path):
    dirs = list(sorted(pipx_local_venvs.iterdir()))
    if not dirs:
        print("nothing has been installed with pipx {}".format(sleep))
        return

    print("venvs are in {}".format(bold(str(pipx_local_venvs))))
    print("symlinks to binaries are in {}".format(bold(str(local_bin_dir))))
    for d in dirs:
        _list_installed_package(d)


def get_exposed_binary_paths_for_package(
    bin_path: Path, package_binary_paths: List[Path], local_bin_dir: Path
):
    bin_symlinks = set()
    package_binary_names = {p.name for p in package_binary_paths}
    for b in local_bin_dir.iterdir():
        try:
            # sometimes symlinks can resolve to a file of a different name
            # (in the case of ansible for example) so checking the resolved paths
            # is not a reliable way to determine if the symlink exists.
            # windows doesn't use symlinks, so the check is less strict.

            if b.name in package_binary_names:
                if WINDOWS:
                    is_same_file = True
                else:
                    is_same_file = b.resolve().parent.samefile(bin_path)

                if is_same_file:
                    bin_symlinks.add(b)
        except FileNotFoundError:
            pass
    return bin_symlinks


def upgrade(venv_dir: Path, package: str, package_or_url: str, verbose: bool):
    if not venv_dir.is_dir():
        raise PipxError(
            "Package is not installed. Expected to find {}, but it does not exist.".format(venv_dir)
        )
    venv = Venv(venv_dir, verbose=verbose)
    old_version = venv.get_package_version(package)
    venv.upgrade_package(package_or_url)
    new_version = venv.get_package_version(package)
    if old_version == new_version:
        print(
            "{} is already at latest version {} (location: {})".format(package, old_version, venv_dir)
        )
        return

    binary_paths = venv.get_package_binary_paths(package)
    expose_binaries_globally(local_bin_dir, binary_paths, package)

    print(
        "upgraded package {} from {} to {} (location: {})".format(package, old_version, new_version, venv_dir)
    )


def upgrade_all(pipx_local_venvs: Path, verbose: bool):
    for venv_dir in pipx_local_venvs.iterdir():
        package = venv_dir.name
        if package == "pipx":
            package_or_url = INSTALL_PIPX_URL
        else:
            package_or_url = package
        upgrade(venv_dir, package, package_or_url, verbose)


def install(
    venv_dir: Path,
    package: str,
    package_or_url: str,
    local_bin_dir: Path,
    python: str,
    verbose: bool,
):
    venv = Venv(venv_dir, python=python, verbose=verbose)
    if venv_dir.exists():
        pass
    else:
        venv.create_venv()
    try:
        venv.install_package(package_or_url)
    except PipxError:
        venv.remove_venv()
        raise

    if venv.get_package_version(package) is None:
        venv.remove_venv()
        raise PipxError("Could not find package {}. Is the name correct?".format(package))

    binary_paths = venv.get_package_binary_paths(package)
    if not binary_paths:
        for dependent_package in venv.get_package_dependencies(package):
            dependent_binaries = venv.get_package_binary_paths(dependent_package)
            if dependent_binaries:
                print(
                    "Note: Dependent package '{}' contains {} binaries".format(dependent_package, len(dependent_binaries))
                )
            for b in dependent_binaries:
                print("  - {}".format(b.name))
        venv.remove_venv()
        raise PipxError("No binaries associated with package {}.".format(package))

    expose_binaries_globally(local_bin_dir, binary_paths, package)
    _list_installed_package(venv_dir, new_install=True)
    print("done! {}".format(stars))


def uninstall(venv_dir: Path, package: str, local_bin_dir: Path, verbose: bool):
    if not venv_dir.exists():
        print("Nothing to uninstall for {} {}".format(package, sleep))
        binary = which(package)
        if binary:
            print(
                "{}  Note: '{}' still exists on your system and is on your PATH".format(hazard, binary)
            )
        return

    venv = Venv(venv_dir, verbose=verbose)

    package_binary_paths = venv.get_package_binary_paths(package)
    for file in local_bin_dir.iterdir():
        if WINDOWS:
            for b in package_binary_paths:
                if file.name == b.name:
                    file.unlink()
        else:
            symlink = file
            for b in package_binary_paths:
                if symlink.exists() and b.exists() and symlink.samefile(b):
                    logging.info("removing symlink %s", symlink)
                    symlink.unlink()

    rmdir(venv_dir)
    print("uninstalled {}! {}".format(package, stars))


def uninstall_all(pipx_local_venvs: Path, local_bin_dir: Path, verbose: bool):
    for venv_dir in pipx_local_venvs.iterdir():
        package = venv_dir.name
        uninstall(venv_dir, package, local_bin_dir, verbose)


def reinstall_all(
    pipx_local_venvs: Path, local_bin_dir: Path, python: str, verbose: bool
):
    for venv_dir in pipx_local_venvs.iterdir():
        package = venv_dir.name
        uninstall(venv_dir, package, local_bin_dir, verbose)

        package_or_url = package
        install(venv_dir, package, package_or_url, local_bin_dir, python, verbose)


def get_fs_package_name(package: str) -> str:
    illegal = ["+", "#", "/", ":"]
    ret = ""
    for x in package:
        if x in illegal:
            ret += "_"
        else:
            ret += x
    return ret


def print_version() -> None:
    print("0.9.3")


def run_pipx_command(args):
    setup(args)
    verbose = args.verbose
    if "package" in args:
        package = args.package
        if urllib.parse.urlparse(package).scheme:
            raise PipxError("Package cannot be a url")
        if package == "pipx":
            logging.warning("using url %s for pipx installation", INSTALL_PIPX_URL)
            args.spec = INSTALL_PIPX_URL
        if "spec" in args and args.spec is not None:
            if urllib.parse.urlparse(args.spec).scheme:
                if "#egg=" not in args.spec:
                    args.spec = "{}#egg={}".format(args.spec, package)

        venv_dir = pipx_local_venvs / package
        logging.info("virtualenv location is %s", venv_dir)

    if args.command == "install":
        package_or_url = (
            args.spec if ("spec" in args and args.spec is not None) else package
        )
        install(venv_dir, package, package_or_url, local_bin_dir, args.python, verbose)
    elif args.command == "upgrade":
        package_or_url = (
            args.spec if ("spec" in args and args.spec is not None) else package
        )
        upgrade(venv_dir, package, package_or_url, verbose)
    elif args.command == "list":
        list_packages(pipx_local_venvs)
    elif args.command == "uninstall":
        uninstall(venv_dir, package, local_bin_dir, verbose)
    elif args.command == "uninstall-all":
        uninstall_all(pipx_local_venvs, local_bin_dir, verbose)
        print("To reinstall pipx, run '{}'".format(INSTALL_PIPX_CMD))
    elif args.command == "upgrade-all":
        upgrade_all(pipx_local_venvs, verbose)
    elif args.command == "reinstall-all":
        reinstall_all(pipx_local_venvs, local_bin_dir, args.python, verbose)
    else:
        raise PipxError("Unknown command {}".format(args.command))


def run_ephemeral_binary(args, binary_args):
    if not args.binary:
        get_command_parser().print_help()
        exit(1)
    binary = args.binary[0]
    package_or_url = args.spec if args.spec else binary
    if package_or_url == "pipx":
        logging.warning("using url %s for pipx installation", INSTALL_PIPX_URL)
        package_or_url = INSTALL_PIPX_URL
    verbose = args.verbose

    if urllib.parse.urlparse(binary).scheme:
        if not binary.endswith(".py"):
            exit(
                "pipx will only execute binaries from the internet directly if "
                "they end with '.py'. To run from an SVN, try pipx --spec URL BINARY"
            )
        logging.info("Detected url. Downloading and executing as a Python file.")
        # download and run directly
        r = requests.get(binary)
        try:
            exit(subprocess.run([str(args.python), "-c", r.content]).returncode)
        except KeyboardInterrupt:
            pass
        exit(0)
    elif which(binary):
        logging.warning(
            "%s  %s is already on your PATH and installed at %s."
            " Downloading and running anyway.", hazard, binary, which(binary)
        )

    if WINDOWS and not binary.endswith(".exe"):
        binary = binary + ".exe"
        logging.warning("Assuming binary is '%s' (Windows only)", binary)

    with tempfile.TemporaryDirectory(
        prefix=get_fs_package_name(package_or_url) + "_"
    ) as venv_dir:
        logging.info("virtualenv is temporary, its location is {}".format(venv_dir))
        return download_and_run(
            Path(venv_dir), package_or_url, binary, binary_args, args.python, verbose
        )


def get_binary_parser(add_help: bool):
    parser = argparse.ArgumentParser(
        add_help=add_help,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage=PIPX_USAGE,
        description=PIPX_DESCRIPTION,
    )

    if not add_help:
        parser.add_argument("--help", "-h", action="store_true")
    parser.add_argument(
        "binary",
        help="A Python package's binary to run or the pipx command to run. If binary,"
        "the PyPI package is assumed to have the same name.",
        nargs="*",
        type=str,
    )

    parser.add_argument("--spec", help=SPEC_HELP)
    parser.add_argument(
        "--python",
        default=DEFAULT_PYTHON,
        help="The Python binary to associate the CLI binary with. Must be v3.3+.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Log additional output to the console",
    )
    parser.add_argument("--version", action="store_true", help="Show version")
    return parser


def get_command_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter, description=PIPX_DESCRIPTION
    )

    subparsers = parser.add_subparsers(
        dest="command", description="Get help for commands with pipx COMMAND --help"
    )
    p = subparsers.add_parser(
        "binary", help=("Run a binary with the given name from an ephemeral virtualenv")
    )
    p.add_argument("--spec", help=SPEC_HELP)
    p.add_argument("--verbose", action="store_true")
    p.add_argument(
        "--python",
        default=DEFAULT_PYTHON,
        help="The Python binary to associate the CLI binary with. Must be v3.3+.",
    )

    p = subparsers.add_parser("install", help="Install a package")
    p.add_argument("package", help="package name")
    p.add_argument("--spec", help=SPEC_HELP)
    p.add_argument("--verbose", action="store_true")
    p.add_argument(
        "--python",
        default=DEFAULT_PYTHON,
        help="The Python binary to associate the CLI binary with. Must be v3.3+.",
    )

    p = subparsers.add_parser("upgrade", help="Upgrade a package")
    p.add_argument("package")
    p.add_argument("--spec", help=SPEC_HELP)
    p.add_argument("--verbose", action="store_true")

    p = subparsers.add_parser(
        "upgrade-all",
        help="Upgrade all packages. "
        "Runs `pip install -U <pkgname>` for each package.",
    )
    p.add_argument("--verbose", action="store_true")

    p = subparsers.add_parser("uninstall", help="Uninstall a package")
    p.add_argument("package")
    p.add_argument("--verbose", action="store_true")

    p = subparsers.add_parser(
        "uninstall-all", help="Uninstall all packages, including pipx"
    )
    p.add_argument("--verbose", action="store_true")

    p = subparsers.add_parser(
        "reinstall-all",
        help="Reinstall all packages with a different Python executable",
    )
    p.add_argument("python")
    p.add_argument("--verbose", action="store_true")

    p = subparsers.add_parser("list", help="List installed packages")
    p.add_argument("--verbose", action="store_true")

    return parser


def separate_pipx_and_binary_args(argv, pipx_commands):
    args = get_binary_parser(add_help=False).parse_known_args()[0]
    if not args.binary and args.version:
        print_version()
        exit(0)
    if args.binary:
        index = argv.index(args.binary[0])
        pipx_args = argv[1 : index + 1]
        binary_args = argv[index + 1 :]
    else:
        # there was no binary, so all args are for pipx
        pipx_args = argv[1:]
        binary_args = []
    return (pipx_args, binary_args)


def args_have_command(pipx_commands: Sequence[str]):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("command", nargs="*")
    args = parser.parse_known_args()
    if args[0].command:
        return args[0].command[0] in pipx_commands
    else:
        return False


def setup(args):
    if "version" in args and args.version:
        print_version()
        exit(0)

    if "verbose" in args and args.verbose:
        logging.basicConfig(
            level=logging.DEBUG, format="pipx (%(funcName)s:%(lineno)d): %(message)s"
        )
    else:
        logging.basicConfig(level=logging.WARNING, format="%(message)s")

    mkdir(pipx_local_venvs)
    mkdir(local_bin_dir)


def cli():
    """Entry point from command line"""
    pipx_commands = [
        "install",
        "upgrade",
        "upgrade-all",
        "uninstall",
        "uninstall-all",
        "reinstall-all",
        "list",
    ]

    try:
        if args_have_command(pipx_commands):
            args = get_command_parser().parse_args()
            setup(args)
            run_pipx_command(args)
        else:
            pipx_args, binary_args = separate_pipx_and_binary_args(
                sys.argv, pipx_commands
            )
            args = get_binary_parser(add_help=True).parse_args(pipx_args)
            setup(args)
            exit(run_ephemeral_binary(args, binary_args))
    except PipxError as e:
        exit(e)


if __name__ == "__main__":
    cli()
