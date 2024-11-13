from fastapi_boot.model.scan import Config

from .core.decorator import Bean, Controller
from .core.decorator import Injectable
from .core.decorator import Injectable as Component
from .core.decorator import Injectable as Repository
from .core.decorator import Injectable as Service
from .core.decorator import Prefix, RpcClient
from .core.decorator.inject import Inject
from .core.decorator.inject import Inject as Autowired
from .core.decorator.mapping import Delete, Get, Head, Options, Patch, Post, Put, Req, Trace
from .core.decorator.mapping import WebSocket as Socket
from .core.hook import use_router, usedep
from .enums import RequestMethodEnum as RequestMethod
from .fastapiboot import FastApiBootApplication
