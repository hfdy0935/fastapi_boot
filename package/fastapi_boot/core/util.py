import inspect


def get_call_filename(layer: int = 1):
    """get filename of file which calls the function which calls get_call_filename"""
    return inspect.stack()[layer + 1].filename.capitalize()
