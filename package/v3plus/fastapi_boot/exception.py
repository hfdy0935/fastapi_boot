class InjectFailException(Exception):
    """inject fail"""


class DependencyNotFoundException(Exception):
    """dependency not found"""


class DependencyDuplicatedException(Exception):
    """dependency duplicated"""


class AppNotFoundException(Exception):
    """app not found"""
