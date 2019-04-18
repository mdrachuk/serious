class UnexpectedJson(Exception):
    def __init__(self, extra_message=None):
        super(UnexpectedJson, self).__init__(f'Unexpected JSON document. {extra_message}')