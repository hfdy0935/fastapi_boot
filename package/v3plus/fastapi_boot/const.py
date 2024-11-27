import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

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
USE_MIDDLEWARE_PLACEHOLDER = 'fastapi_boot__use_middleware_placeholder'


# ------------------------------------------------------- store ------------------------------------------------------ #


@dataclass
class TypeDepRecord(Generic[T]):
    tp: type[T]
    value: T


@dataclass
class NameDepRecord(Generic[T], TypeDepRecord[T]):
    name: str


class DependencyStore(Generic[T]):
    def __init__(self):
        self.type_deps: dict[type[T], TypeDepRecord[T]] = {}
        self.name_deps: dict[str, NameDepRecord[T]] = {}

    def add_dep_by_type(self, dep: TypeDepRecord[T]):
        if dep.tp in self.type_deps:
            raise DependencyDuplicatedException(f'Dependency {dep.tp} duplicated')
        self.type_deps.update({dep.tp: dep})

    def add_dep_by_name(self, dep: NameDepRecord[T]):
        if self.name_deps.get(dep.name):
            raise DependencyDuplicatedException(f'Dependency name {dep.name} duplicated')
        self.name_deps.update({dep.name: dep})

    def inject_by_type(self, tp: type[T]) -> T | None:
        if res := self.type_deps.get(tp):
            return res.value

    def inject_by_name(self, name: str, tp: type[T]) -> T | None:
        if find := self.name_deps.get(name):
            if find.tp == tp:
                return find.value


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


class TasStore:
    def __init__(self):
        # will be called after the app becomes available
        self.late_tasks: dict[str, list[tuple[Callable, int]]] = {}

    def add_late_task(self, path: str, task: Callable, priority: int):
        if curr_tasks := self.late_tasks.get(path):
            self.late_tasks.update({path: [*curr_tasks, (task, priority)]})
        else:
            self.late_tasks.update({path: [(task, priority)]})

    def run_late_tasks(self):
        for path, late_tasks in self.late_tasks.items():
            app = app_store.get(path).app
            late_tasks.sort(key=lambda x: x[1], reverse=True)
            for record in late_tasks:
                task = record[0]
                if len(inspect.signature(task).parameters) > 0:
                    task(app)
                else:
                    task()


dep_store = DependencyStore()
app_store = AppStore()
task_store = TasStore()
