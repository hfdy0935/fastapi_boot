from collections.abc import Callable
from dataclasses import dataclass
import inspect
from typing import Generic, TypeVar
from fastapi import FastAPI

from fastapi_boot.exception import AppNotFoundException, DependencyDuplicatedException
from fastapi_boot.model import AppRecord

T = TypeVar('T')

@dataclass
class TypeDepRecord(Generic[T]):
    tp: type[T]
    value: T


@dataclass
class NameDepRecord(Generic[T], TypeDepRecord[T]):
    name: str


class DependenciesStore(Generic[T]):
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
        self.late_tasks: dict[str, list[tuple[Callable[[FastAPI], None],int]]] = {}

    def add_late_task(self, path: str, task: Callable[[FastAPI], None],priority:int):
        if curr_tasks := self.late_tasks.get(path):
            l=[*curr_tasks, (task,priority)]
            l.sort(key=lambda x:x[1], reverse=True)
            self.late_tasks.update({path: l})
        else:
            self.late_tasks.update({path: [(task,priority)]})

    def run_late_tasks(self):
        for path, late_tasks in self.late_tasks.items():
            app = app_store.get(path).app
            for record in late_tasks:
                task=record[0]
                if len(inspect.signature(task).parameters)>0:
                    task(app)
                else:
                    task()


dep_store = DependenciesStore()
app_store = AppStore()
task_store = TasStore()
