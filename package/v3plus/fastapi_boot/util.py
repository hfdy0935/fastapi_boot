import inspect


def get_call_filename(layer: int = 1):
    """get filename of file which calls the function which calls get_call_filename"""
    filename = inspect.stack()[layer + 1].filename
    return filename[0].upper() + filename[1:]
