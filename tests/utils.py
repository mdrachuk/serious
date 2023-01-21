import inspect
from itertools import product
from typing import Tuple, Sequence, Type

import pytest


def with_(*collections: Tuple[Sequence], cartesian_product=True):
    def _wrapped(f):
        signature = inspect.signature(f)
        func_params = list(signature.parameters)
        if len(func_params) and func_params[0] == 'self':
            func_params.pop(0)
        pytest_keys = ','.join(func_params)
        if len(collections) > 1:
            if cartesian_product:
                pytest_values = list(product(*collections))
            else:
                if len(set(map(len, collections))) != 1:
                    raise Exception('Parameters must be of equal length')
                pytest_values = list(zip(*collections))
        else:
            pytest_values = collections[0]
        return pytest.mark.parametrize(pytest_keys, pytest_values)(f)

    return _wrapped
