from enum import Enum


class RouteStatus(Enum):
    """status of route
    - un_controlled, not been decorated by @Controller
    - deactivate, need `run` method in MainApplication
    - activate, can use
    """
    UN_CONTROLLED = 'un_controlled'
    DEACTIVATE = 'deactivate'
    ACTIVATE = 'activate'


class RouteType(Enum):
    """type of route
    - CBV: class_basic_view
    - FBV：function_basic_view
    - ENDPOINT：endpoint
    - INNER_CBV：inner_cbv
    """
    CBV = 'CBV'
    FBV = 'FBV'
    ENDPOINT = 'ENDPOINT'
    INNER_CBV = 'INNER_CBV'
