import requests
from pkg_resources import safe_version

__version__ = '1.0.0.dev17'

__doc__ = """
This module is querying PyPI to check if the current version set to package is already present on PyPI.

Used during PR checks, to ensure that package version is changed. 

Finishes with an VersionExists exception and a non-zero exit code if the version exists on PyPI. 
"""
from dataclasses import dataclass
from typing import Dict, Set, List

from serious.json import JsonModel


@dataclass
class PypiPackage:
    releases: Dict[str, List]

    @property
    def versions(self) -> Set[str]:
        return set(self.releases.keys())

    def contains_version(self, target: str) -> bool:
        target = safe_version(target)

        existing = {safe_version(version) for version in self.versions}
        return target in existing


class VersionExists(Exception):
    def __init__(self, name: str, version: str):
        super().__init__(f'Package "{name}" with version "{version}" already exists on PyPI. '
                         f'You can change the version in "config.py".')


def fetch(name: str):
    model = JsonModel(PypiPackage, allow_unexpected=True, allow_any=True)
    package_json = requests.get(f'https://pypi.org/pypi/{name}/json').text
    return model.load(package_json)


def check_unique(name: str, version: str):
    pypi_pkg = fetch(name)
    if pypi_pkg.contains_version(version):
        raise VersionExists(name, version)
    print(f'OK: {name} {version} is not present on PyPI.')


if __name__ == '__main__':
    check_unique('serious', __version__)
