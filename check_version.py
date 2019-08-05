import requests

__doc__ = """
This module is querying PyPI to check if the current version set to package is already present on PyPI.

Used during PR checks, to ensure that package version is changed. 

Finishes with an VersionExists exception and a non-zero exit code if the version exists on PyPI. 
"""
from dataclasses import dataclass
from typing import Dict, Set, List

from config import Config
from serious.json import JsonModel


@dataclass
class PypiPackage:
    releases: Dict[str, List]

    @property
    def versions(self) -> Set[str]:
        return set(self.releases.keys())

    def contains_version(self, target: str) -> bool:
        target = simplify(target)
        existing = {simplify(version) for version in self.versions}
        return target in existing


def simplify(value: str) -> str:
    """
    PyPI simplifies the package version to be uniformly formatted.
    It does that without any notice.
    This emulates such an operation.
    """
    value = value.replace('.', '')
    value = value.replace('-', '')
    value = value.replace('_', '')
    value = value.replace(' ', '')
    return value


class VersionExists(Exception):
    def __init__(self, pkg_config):
        super().__init__(f'Package "{pkg_config.name}" with version "{pkg_config.version}" already exists on PyPI. '
                         f'You can change the version in "config.py".')


def fetch_package(package_name: str):
    model = JsonModel(PypiPackage, allow_unexpected=True, allow_any=True)
    package_json = requests.get(f'https://pypi.org/pypi/{package_name}/json').text
    return model.load(package_json)


def check_unique(pkg: Config):
    remote = fetch_package(pkg.name)
    if remote.contains_version(pkg.version):
        raise VersionExists(pkg)
    print(f'OK: {pkg.name} {pkg.version} is not present on PyPI.')


if __name__ == '__main__':
    from config import config

    check_unique(config)
