from dataclasses import dataclass
from typing import Generic, TypeVar

from fastapi import FastAPI

from fastapi_boot.exception import AppNotFoundException, DependencyDuplicatedException
from fastapi_boot.model import FastAPIRecord

T = TypeVar('T')


@dataclass
class TypeDepRecord(Generic[T]):
    tp: type[T]
    value: T


@dataclass
class NamedDepRecord(Generic[T], TypeDepRecord[T]):
    name: str


class DependenciesStore(Generic[T]):
    def __init__(self):
        self.type_deps: dict[type[T], TypeDepRecord[T]] = {}
        self.name_deps: dict[str, NamedDepRecord[T]] = {}

    def add_dep_by_type(self, dep: TypeDepRecord[T]):
        if dep.tp in self.type_deps:
            raise DependencyDuplicatedException(f'Dependency {dep.tp} duplicated')
        self.type_deps.update({dep.tp: dep})

    def add_dep_by_name(self, dep: NamedDepRecord[T]):
        if self.name_deps.get(dep.name):
            raise DependencyDuplicatedException(f'Dependency name {dep.name} duplicated')
        self.name_deps.update({dep.name: dep})

    def inject_by_type(self, tp: type[T]) -> T | None:
        if res := self.type_deps.get(tp):
            return res.value

    def inject_by_name(self, name: str, tp: type[T]) -> T | None:
        if find := self.name_deps.get(name):
            if find.tp==tp:
                return find.value


class AppStore(Generic[T]):
    def __init__(self):
        self.app_dic: dict[str, FastAPIRecord] = {}

    def add(self, path: str, app: FastAPI, scan_timeout: float):
        self.app_dic.update({path: FastAPIRecord(app, scan_timeout)})

    def get(self, path: str) -> FastAPIRecord:
        path = path[0].upper() + path[1:]
        for k, v in self.app_dic.items():
            if path.startswith(k):
                return v
        raise AppNotFoundException(f'Can"t find app of "{path}"')


dep_store = DependenciesStore()
app_store = AppStore()
