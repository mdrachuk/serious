from dataclasses import dataclass
from typing import Dict, Set, List
from urllib import request

from config import config
from serious.json import JsonSerializer


@dataclass
class Package:
    releases: Dict[str, List]

    @property
    def versions(self) -> Set[str]:
        return set(self.releases.keys())


class VersionExists(Exception):
    def __init__(self, pkg_config):
        super().__init__(f'Package "{pkg_config.name}" with version "{pkg_config.version}" already exists on PyPI. '
                         f'You can change the version in "config.py".')


def check_exists(pkg_config):
    package_schema = JsonSerializer(Package, allow_unexpected=True)
    with request.urlopen('https://pypi.org/pypi/serious/json') as pypi:
        package_data = pypi.read()
    package = package_schema.load(package_data)
    if pkg_config.version in package.versions:
        raise VersionExists(pkg_config)


if __name__ == '__main__':
    check_exists(config)
