class InjectFailException(Exception):
    """inject fail"""


class DependencyNotFoundException(Exception):
    """dependency not found"""


class DependencyDuplicatedException(Exception):
    """dependency duplicated"""


class InValidControllerException(Exception):
    """invalid controller, does not have router"""
