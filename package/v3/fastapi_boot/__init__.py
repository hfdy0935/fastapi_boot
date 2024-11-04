from fastapi_boot.model.scan import Config
from .core.decorator import Controller, Bean, Injectable, Prefix
from .fastapiboot import FastApiBootApplication
from .core.decorator import (
    Injectable as Service,
    Injectable as Repository,
    Injectable as Component,
)

from .core.decorator.inject import Inject
from .core.decorator.inject import Inject as Autowired
from .core.hook import usedep, use_router
from .core.decorator.mapping import (
    Req,
    Get,
    Post,
    Put,
    Delete,
    Options,
    Head,
    Patch,
    Trace,
    WebSocket as Socket,
)

from .enums import RequestMethodEnum as RequestMethod
