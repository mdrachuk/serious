from dataclasses import dataclass
from typing import Dict, Set, List
from urllib import request

from config import config
from serious.json import JsonSchema


@dataclass
class Package:
    releases: Dict[str, List]

    @property
    def versions(self) -> Set[str]:
        return set(self.releases.keys())

    def contains_version(self, target: str) -> bool:
        target = simplify(target)
        existing = {simplify(version) for version in self.versions}
        return target in existing


def simplify(value: str) -> str:
    value = value.replace('.', '')
    value = value.replace('-', '')
    value = value.replace('_', '')
    value = value.replace(' ', '')
    return value


class VersionExists(Exception):
    def __init__(self, pkg_config):
        super().__init__(f'Package "{pkg_config.name}" with version "{pkg_config.version}" already exists on PyPI. '
                         f'You can change the version in "config.py".')


def check_exists(pkg_config):
    package_schema = JsonSchema(Package, allow_unexpected=True, allow_any=True)
    with request.urlopen('https://pypi.org/pypi/serious/json') as pypi:
        package_data = pypi.read()
    package = package_schema.load(package_data)
    if package.contains_version(pkg_config.version):
        raise VersionExists(pkg_config)


if __name__ == '__main__':
    check_exists(config)
