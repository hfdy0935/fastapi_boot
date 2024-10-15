from typing import no_type_check
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.model.routes.route_export import Route


@no_type_check
def useRoute() -> Route:
    """declared as a class variable, hook the class's route info to context
    """
    return CommonVar.ROUTE_PLACEHOLDER
