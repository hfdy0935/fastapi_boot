from .DI import Bean
from .DI import Inject
from .DI import Inject as Autowired
from .DI import Injectable
from .DI import Injectable as Component
from .DI import Injectable as Repository
from .DI import Injectable as Service
from .helper import ExceptionHandler, OnAppProvided, provide_app, use_dep, use_http_middleware,use_ws_middleware
from .routing import Controller, Delete, Get, Head, Options, Patch, Post, Prefix, Put, Req, Trace
from .routing import WebSocket as Socket

__all__=imported_names = [
    'Bean',
    'Inject',
    'Autowired',  # Inject的别名
    'Injectable',
    'Component',  # Injectable的别名
    'Repository',  # Injectable的别名
    'Service',  # Injectable的别名
    'ExceptionHandler',
    'OnAppProvided',
    'provide_app',
    'use_dep',
    'use_http_middleware',
    'use_ws_middleware',
    'Controller',
    'Delete',
    'Get',
    'Head',
    'Options',
    'Patch',
    'Post',
    'Prefix',
    'Put',
    'Req',
    'Trace',
    'Socket'  # WebSocket的别名
]