from typing import Generic, TypeVar

from fastapi_boot.core.model import AppNotFoundException, AppRecord, DependencyDuplicatedException

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


# ------------------------------------------------------- store ------------------------------------------------------ #
class DependencyStore(Generic[T]):
    def __init__(self):
        # {type: instance}
        self.type_deps: dict[type[T], T] = {}
        # {name: {type: instance}}
        self.name_deps: dict[type[T], dict[str, T]] = {}

    def add_dep_by_type(self, tp: type[T], ins: T):
        if tp in self.type_deps:
            raise DependencyDuplicatedException(f'Dependency of "{tp.__name__}" is duplicated')
        self.type_deps.update({tp: ins})

    def add_dep_by_name(self, tp: type[T], name: str, ins: T):
        name_dict = self.name_deps.get(tp, {})
        if name in name_dict:
            raise DependencyDuplicatedException(f'Dependency of type "{tp.__name__}" with name "{name}" is duplicated')
        else:
            name_dict.update({name: ins})
            self.name_deps.update({tp: name_dict})

    def add_dep(self, tp: type[T], name: str | None, ins: T):
        if name is None:
            self.add_dep_by_type(tp, ins)
        else:
            self.add_dep_by_name(tp, name, ins)

    def inject_dep(self, tp: type[T], name: str | None):
        if name is None:
            return self.type_deps.get(tp, None)
        else:
            return self.name_deps.get(tp, {}).get(name, None)

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


dep_store = DependencyStore()
app_store = AppStore()
