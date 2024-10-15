
import inspect


def get_stack_path(n: int) -> str:
    """Gets the path to the file called in the call stack

    Args:
        n (int): Index in the stack to find

    Returns:
        str: result
    """
    # n + 1, Considering that this function occupies one position
    caller_frame = inspect.stack()[n+1]
    name = caller_frame.frame.f_code.co_filename
    return name[0].upper()+name[1:]
