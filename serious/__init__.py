"""Serious is a Python dataclass model toolkit for serialization, validation, and more.

Core functionality is available for import from `serious`, and is listed here in `serious/__init__`:
models, errors, types and validation.

To provide custom field serialization use `serious.serialization`.

Test utils can be found in `serious.test_utils`.

`More on Read The Docs.`_
`Sources on GitHub.`_

.. _More on Read The Docs.: https://serious.readthedocs.io/en/latest/
.. _Sources on GitHub.: https://github.com/mdrachuk/serious
"""

from .dict import DictModel
from .errors import ModelError, ValidationError, LoadError, DumpError
from .json import JsonModel
from .types import Timestamp, Email, FrozenList, FrozenDict
from .validation import validate

__version__ = '1.2.9'
