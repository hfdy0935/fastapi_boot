from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from fastapi import FastAPI

from fastapi_boot.model import AppNotFoundException, AppRecord, DependencyDuplicatedException

T = TypeVar('T')

# ---------------------------------------------------- constant ---------------------------------------------------- #
# use_dep placeholder
REQ_DEP_PLACEHOLDER = "fastapi_boot___dependency_placeholder"


# route record's key in controller
CONTROLLER_ROUTE_RECORD = "fastapi_boot___controller_route_record"

# prefix of use_dep params in endpoint
USE_DEP_PREFIX_IN_ENDPOINT = 'fastapi_boot__use_dep_prefix'


# use_middleware placeholder
USE_MIDDLEWARE_FIELD_PLACEHOLDER = 'fastapi_boot__use_middleware_field_placeholder'


class BlankPlaceholder: ...


# PRIORITY OF EXCEPTION_HANDLER
EXCEPTION_HANDLER_PRIORITY = 1


# ------------------------------------------------------- store ------------------------------------------------------ #
class DependencyStore(Generic[T]):
    def __init__(self):
        # {type: instance}
        self.type_deps: dict[int, T] = {}
        # {name: {type: instance}}
        self.name_deps: dict[int, dict[str,T]] = {}

    def add_dep_by_type(self, tp:type[T],ins:T):
        tp_id=id(tp)
        if tp_id in self.type_deps:
            raise DependencyDuplicatedException(f'Dependency {tp} duplicated')
        self.type_deps.update({tp_id: ins})

    def add_dep_by_name(self, name:str,tp:type[T],ins:T):
        tp_id=id(tp)
        name_dict=self.name_deps.get(tp_id)
        if name_dict is None:
            self.name_deps.update({tp_id:{name:ins}})
        else:
            curr_ins=name_dict.get(name)
            if curr_ins:
                raise DependencyDuplicatedException(f'Dependency name {name} duplicated')
            else:
                name_dict.update({name:ins})
                self.name_deps.update({tp_id:name_dict})

    def inject_by_type(self, tp: type[T]) -> T | None:
        return self.type_deps.get(id(tp),None)

    def inject_by_name(self, name: str, tp: type[T]) -> T | None:
        return self.name_deps.get(id(tp),{}).get(name,None)

    def clear(self):
        self.type_deps.clear()
        self.name_deps.clear()


class AppStore(Generic[T]):
    def __init__(self):
        self.app_dic: dict[str, AppRecord] = {}

    def add(self, path: str, app_record: AppRecord):
        self.app_dic.update({path: app_record})

    def get(self, path: str) -> AppRecord:
        path = path[0].upper() + path[1:]
        for k, v in self.app_dic.items():
            if path.startswith(k):
                return v
        raise AppNotFoundException(f'Can"t find app of "{path}"')

    def clear(self):
        self.app_dic.clear()


class TaskStore:
    def __init__(self):
        # will be called after the app becomes available
        self.late_tasks: dict[str, list[tuple[Callable[[FastAPI], None], int]]] = {}

    def add_late_task(self, path: str, task: Callable[[FastAPI], None], priority: int):
        if curr_tasks := self.late_tasks.get(path):
            self.late_tasks.update({path: [*curr_tasks, (task, priority)]})
        else:
            self.late_tasks.update({path: [(task, priority)]})
            

    def run_late_tasks(self):
        for path, late_tasks in self.late_tasks.items():
            app = app_store.get(path).app
            late_tasks.sort(key=lambda x: x[1], reverse=True)
            for record in late_tasks:
                record[0](app)

    def clear(self):
        self.late_tasks.clear()


dep_store = DependencyStore()
app_store = AppStore()
task_store = TaskStore()
