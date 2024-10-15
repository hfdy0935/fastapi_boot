from pathlib import Path
from typing import Any, Callable, Dict, Final, List, Type


class RoutesPlaceholder: ...


class RouterPlaceholder: ...


class _DepsPlaceholder: ...


class CommonVar:
    """存放公共的变量"""

    # 常量
    # 自动装配占位符，扫描完毕需要替换
    AUTO_WIRED_PLACEHOLDER: Final[str] = "auto_wired_placeholder"
    # route info field
    ROUTE_INFO: Final[str] = "route_info"
    # route type field
    ROUTE_TYPE: Final[str] = "route_type"
    # route field placeholder, will be replaced by some value finally
    ROUTES_PLACEHOLDER: Final[Type[RoutesPlaceholder]] = RoutesPlaceholder
    # router placeholder
    ROUTER_PLACEHOLDER: Final[Type[RouterPlaceholder]] = RouterPlaceholder
    # original obj
    ORI_OBJ: Final[str] = "original_obj"
    # decorated obj
    DEC_OBJ: Final[str] = "decorated_obj"
    # depends field placeholder, will be replaced by some value finally.
    DEP_PLACEHOLDER: Final[str] = "dependency_placeholder"
    DepsPlaceholder: Final[Type[_DepsPlaceholder]] = _DepsPlaceholder

    # key = application's position in project, separated by dot; value = application instance
    _application_dict: Dict[str, Any] = {}
    # todo list after app initialized
    _todo_list: Dict[str, List[Callable]] = {}

    @staticmethod
    def get_application(pos: str) -> Any:
        """根据路径获取所在的应用，传来的时调用时的系统绝对路径，找到属于哪个应用
        - 不能只用startswith，考虑到ex1,ex12这种情况可能会误判
        """
        pos = pos[0].upper() + pos[1:]
        for k, v in CommonVar._application_dict.items():
            contain=[1 for i,j in zip(Path(k).parts, Path(pos).parts) if i==j]
            if len(contain) == len(
                Path(k).parts
            ):
                return v

    @staticmethod
    def get_all_application() -> Any:
        return CommonVar._application_dict

    @staticmethod
    def set_application_info(pos: str, application: Any):
        """添加应用信息

        Args:
            pos (str): 启动文件所在项目在系统中的绝对路径
            app (Any): MainApplication实例
        """
        CommonVar._application_dict.update({pos: application})

    @staticmethod
    def get_todo_list_by_app_pos(pos: str) -> List[Callable]:
        """Get todo list by application position.

        Args:
            pos (str): application position

        Returns:
            List[Callable]: todo list
        """
        res = []
        for k, v in CommonVar._todo_list.items():
            if len([i for i in Path(pos).parts if i in Path(k).parts]) == len(
                Path(pos).parts
            ):
                res.extend(v)
        return res

    @staticmethod
    def clear_todo_list_by_app_pos(pos: str):
        for k, v in CommonVar._todo_list.items():
            if len([i for i in Path(pos).parts if i in Path(k).parts]) == len(
                Path(pos).parts
            ):
                CommonVar._todo_list.update({k: []})

    @staticmethod
    def add_todo_list_by_task_pos(pos: str, task: Callable):
        """Add a task to todo list.

        Args:
            pos (str): task position in project, separated by dot
            task (Callable): task
        """
        if v := CommonVar._todo_list.get(pos, None):
            v.append(task)
        else:
            CommonVar._todo_list.update({pos: [task]})
