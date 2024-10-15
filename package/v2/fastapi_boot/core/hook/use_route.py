from typing import List, no_type_check

from fastapi import APIRouter
from starlette.routing import BaseRoute
from fastapi_boot.core.var.common import CommonVar


@no_type_check
def useRoutes() -> List[BaseRoute]:
    """declared as a class variable, hook the class's route info to context"""
    return CommonVar.ROUTES_PLACEHOLDER


@no_type_check
def useRouter() -> APIRouter:
    """
    - get APIRouter instance
    """
    return CommonVar.ROUTER_PLACEHOLDER
