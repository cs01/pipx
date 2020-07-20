# Valid package specifiers for pipx:
#   git+<URL>
#   <URL>
#   <pypi_package_name>
#   <pypi_package_name><version_specifier>

from pathlib import Path
from packaging.requirements import Requirement, InvalidRequirement
from packaging.utils import canonicalize_name
from typing import Optional

from pipx.util import PipxError


def parse_specifier(package_spec: str) -> str:
    """Return package_or_url suitable for pipx metadata

    Specifically:
    * Strip any version specifiers (e.g. package == 1.5.4)
    * Strip any markers (e.g. python_version > 3.4)
    * Convert local paths to absolute paths
    """
    # NOTE: If package_spec to valid pypi name, pip will always treat it as a
    #       pypi package, not checking for local path.
    #       We replicate pypi precedence here (only non-valid-pypi names
    #       initiate check for local path, e.g. './package-name')

    valid_pep508 = False
    valid_url = False
    valid_local_path = False
    package_or_url = ""

    try:
        package_req = Requirement(package_spec)
    except InvalidRequirement:
        # not a valid PEP508 package specification
        valid_pep508 = False
    else:
        # valid PEP508 package specification
        valid_pep508 = True
        if package_req.url:
            package_or_url = package_req.url
        else:
            if package_req.extras:
                package_or_url = canonicalize_name(
                    package_req.name + "[" + ",".join(package_req.extras) + "]"
                )
            else:
                package_or_url = canonicalize_name(package_req.name)

    if not valid_pep508:
        try:
            package_req = Requirement("notapackagename @ " + package_spec)
        except InvalidRequirement:
            valid_url = False
        else:
            valid_url = True
            package_or_url = package_spec

    if not valid_pep508 and not valid_url:
        package_path = Path(package_spec)
        if package_path.exists():
            valid_local_path = True
            package_or_url = str(package_path.resolve())

    if not valid_pep508 and not valid_url and not valid_local_path:
        raise PipxError(f"Unable to parse package spec: {package_spec}")

    return package_or_url


def valid_pypi_name(package_spec: str) -> Optional[str]:
    try:
        package_req = Requirement(package_spec)
    except InvalidRequirement:
        # not a valid PEP508 package specification
        return None

    return package_req.name