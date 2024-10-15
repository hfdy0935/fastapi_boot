from typing import Any, Callable, Dict, List

from fastapi import FastAPI

from fastapi_boot.core.application.main import MainApplication
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.model.routes.route_export import RouteLayerItem
from fastapi_boot.model.routes.route_record import (
    RouteRecordItem,
    SimpleRouteRecordItem,
)
from fastapi_boot.model.scan.config import Config


class FastApiBootApplication:
    """FastApiBootApplication, help you build the project, but you should start project by yourself, such as uvicorn.
    ## Example

    ```python
    # 1. get some information of application
    app=FastAPI()
    application.FastApiBootApplication(app[, Config(...)])
    with open('./proj_1.json', 'w', encoding = 'utf-8') as f:
        json.dump(application.serialized_routes_layers, f, indent = 4, ensure_ascii = False)
    application.run()
    ...

    # 2. just run
    app=FastAPI()
    @FastApiBootApplication(app[, Config(...)])
    def main():
        ...
    if __name__ == '__main__':
        main()

    # 3. just run with staticmethod
    FastApiBootApplication.run_app(app,[, Config(...)])
    ...
    ```
    """

    def __init__(self, app: FastAPI, config: Config = Config()):
        self.app = MainApplication(app, config)
        for task in CommonVar.get_todo_list_by_app_pos(self.app.dot_prefix):
            task()
        CommonVar.clear_todo_list_by_app_pos(self.app.dot_prefix)

    def run(self):
        self.app.run()

    def __call__(self, fn: Callable) -> Callable[..., Any]:
        self.app.run()

        def w(*args, **kwargs):
            return fn(*args, **kwargs)

        return w

    @staticmethod
    def run_app(app: FastAPI, config: Config = Config()):
        application = MainApplication(app, config)
        for task in CommonVar.get_todo_list_by_app_pos(application.dot_prefix):
            task()
        CommonVar.clear_todo_list_by_app_pos(application.dot_prefix)
        application.run()

    @property
    def routes_records(self) -> List[RouteRecordItem]:
        return self.app.route_record_list

    @property
    def simple_routes_records(self) -> List[SimpleRouteRecordItem]:
        return self.app.simple_route_record_list

    @property
    def serialized_simple_routes_records(self) -> List[Dict]:
        res = []
        for i in self.simple_routes_records:
            dic = i.dict()
            assert i.route_status
            dic.update(dict(route_status=i.route_status.value))
            res.append(dic)
        return res

    @property
    def routes_layers(self) -> List[RouteLayerItem]:
        return self.app.route_layer_list

    @property
    def serialized_routes_layers(self) -> List[Dict]:
        return [i.dict() for i in self.app.route_layer_list]
