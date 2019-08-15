"""Errors specific to JSON model."""


class UnexpectedJson(Exception):
    """Invalid JSON provided to JSON model."""

    def __init__(self, extra_message=None):
        super().__init__(f'Unexpected JSON document. {extra_message}')
