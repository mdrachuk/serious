from collections import namedtuple
from typing import Callable

from serious.utils import snake_to_camel, camel_to_snake

Ex = namedtuple('Example', ['snake', 'camel'])


class TestCases:

    def setup_class(self):
        self.examples = [
            Ex('_http_response', 'httpResponse'),
            Ex('name__space', 'httpResponse'),
            Ex('some_str_3_one_two_three_234', 'someStr3AbcOneTwoThree234'),
            Ex('some32_cows', 'some32Cows'),
        ]

    def each_example(self, test: Callable[[Ex], None]):
        for example in self.examples:
            test(example)

    def test_snake_to_camel(self):
        self.each_example(lambda ex: snake_to_camel(ex.snake) == ex.camel)

    def test_camel_to_snake(self):
        self.each_example(lambda ex: camel_to_snake(ex.camel) == ex.snake)

    def check_symmetry(self):
        self.each_example(lambda ex: snake_to_camel(camel_to_snake(ex.camel)) == ex.camel)
        self.each_example(lambda ex: camel_to_snake(snake_to_camel(ex.snake)) == ex.snake)
