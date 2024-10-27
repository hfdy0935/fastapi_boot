# -------------------------------------------------------------------------------------------------------------------- #

from fastapi_boot.model.scan_model import Config
from .core.decorator import (
    Controller,
    Bean,
    Injectable,
    FastApiBootApplication,
)
from .core.decorator import (
    Injectable as Service,
    Injectable as Repository,
    Injectable as Component,
)

from .core.helper import Inject, Prefix
from .core.helper import Inject as Autowired
from .core.hook import usedep
from .core.mapping.func import (
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

# -------------------------------------------------------------------------------------------------------------------- #

from .enums import RequestMethodEnum as RequestMethod

# -------------------------------------------------------------------------------------------------------------------- #
