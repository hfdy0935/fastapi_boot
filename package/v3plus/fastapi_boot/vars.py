from dataclasses import dataclass
from typing import Generic, TypeVar
import warnings

from fastapi_boot.exception import DependencyDuplicatedException, DependencyNotFoundException

T = TypeVar('T')


@dataclass
class TypeDepRecord(Generic[T]):
    tp: type[T]
    value: T


@dataclass
class NamedDepRecord(Generic[T], TypeDepRecord[T]):
    name: str


class DependenciesRepository(Generic[T]):
    def __init__(self) -> None:
        self.type_deps: dict[type[T], TypeDepRecord[T]] = {}
        self.name_deps: dict[str, NamedDepRecord[T]] = {}

    def add_dep_by_type(self, dep: TypeDepRecord[T]):
        if dep.tp in self.type_deps:
            raise DependencyDuplicatedException(
                f'Dependency {dep.tp} duplicated')
        self.type_deps.update({dep.tp: dep})

    def add_dep_by_name(self, dep: NamedDepRecord[T]):
        if self.name_deps.get(dep.name):
            raise DependencyDuplicatedException(
                f'Dependency name {dep.name} duplicated')
        self.name_deps.update({dep.name: dep})

    def inject_by_type(self, tp: type[T]) -> T:
        if res := self.type_deps.get(tp):
            return res.value
        raise DependencyNotFoundException(
            f'Dependency "{tp}" not found')

    def inject_by_name(self, name: str, tp: type[T]) -> T:
        if find := self.name_deps.get(name):
            if tp != find.tp:
                warnings.warn(
                    f'The type of name "{name}" is {find.tp}, does not match given type: "{tp}"')
            return find.value
        raise DependencyNotFoundException(
            f'Can not find any dependency with type "{tp}" and name "{name}"')


dep_store = DependenciesRepository()
