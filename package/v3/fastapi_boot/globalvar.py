from typing import Generic, TypeVar

from fastapi_boot.exception import AppNotFoundException, InjectFailException
from fastapi_boot.model.scan import DepRecord, ModRecord, MountedTask, NoAppDepRecord

T = TypeVar('T')


class GlobalVar(Generic[T]):
    # -------------------------------------------------------- 子应用 ------------------------------------------------------- #
    # 子应用列表
    __app_list: list = []
    # 根据stack_path判断运行的子应用任务列表，还没创建，等后面创建之后会运行
    __app_stack_path_task_list: list[MountedTask] = []

    @staticmethod
    def get_app(path: str):
        """根据路径获取app，在子应用内部的能获取成，外部的依赖就抛出异常

        Args:
            path (str): 路径

        Returns:
            MainApplication | None: 主应用，可能找不到
        """
        if len(res := [app for app in GlobalVar.__app_list if app.mod.is_super_of_stack_path(path)]) > 0:
            return res[0]
        raise AppNotFoundException(AppNotFoundException.msg + f'，位置：{path}')

    @staticmethod
    def get_all_apps():
        return GlobalVar.__app_list

    @staticmethod
    def add_app(app):
        """添加一个application"""
        GlobalVar.__app_list.append(app)

    # ------------------------------------------------------ 子应用的任务，适用于还没初始化时暂存在全局 ------------------------------------------------------ #
    @staticmethod
    def add_app_stack_path_task(task: MountedTask):
        """添加子应用的任务，这时子应用还未创建，只知道任务，等该子应用创建完毕获取任务后执行"""
        GlobalVar.__app_stack_path_task_list.append(task)

    @staticmethod
    def run_app_stack_path_task(app):
        """运行子应用的任务；
        用于先include_router其他应用的路由且其他路由还未创建时
        """
        for task in GlobalVar.__app_stack_path_task_list:
            if app.mod.is_super_of_stack_path(task.symbol.stack_path):
                task.run()

    # -------------------------------------------------------------------------------------------------------------------- #
    # ------------------------------------------------------- 无app模块的依赖 ------------------------------------------------------- #
    # 不用手动扫描，导入的时候就扫描了；子应用中扫描是为了找出控制器，而控制器中也导入了一次，所以导入了两次，但因为缓存，第二次没算
    # 没有app的模块的依赖列表
    no_app_dep_list: list[NoAppDepRecord] = []
    # 任务列表
    no_app_task_list: list[MountedTask] = []
    # 全局扫描超时时间
    no_app_scan_timeout_second = 10

    @staticmethod
    def add_dep(item: NoAppDepRecord):
        """无app模块依赖列表中添加依赖"""
        GlobalVar.no_app_dep_list.append(item)

    @staticmethod
    def _handle_inject_result(find_list: list[DepRecord[T]] | list[NoAppDepRecord[T]], raise_msg: str) -> T | None:
        """处理注入结果"""
        # 如果没找到
        l = len(find_list)
        if l == 0:
            return None
        # 如果找到多个
        if l > 1:
            raise_pos = '\n'.join([f'\t{idx}. {i.symbol.pos}' for idx, i in enumerate(find_list, start=1)])
            raise InjectFailException(f'找到{l}个依赖，注入失败，{raise_msg}，位置：\n{raise_pos}')
        # 只有一个
        return find_list[0].value

    @staticmethod
    def inject_by_type(DepType: type[T]) -> T | None:
        """根据类型注入依赖"""
        res: list[NoAppDepRecord[T]] = []
        for b in GlobalVar.no_app_dep_list:
            # 考虑到Bean返回字符串，类型后定义的情况
            if b.constructor == DepType or b.constructor == DepType.__name__:
                res.append(b)
        return GlobalVar._handle_inject_result(res, f'确保类型{DepType.__name__}只对应一个依赖，或使用命名依赖')

    @staticmethod
    def inject_by_name(name: str, DepType: type[T]) -> T | None:
        """根据名称注入依赖"""
        res: list[NoAppDepRecord[T]] = []
        for b in GlobalVar.no_app_dep_list:
            if b.name == name and b.constructor == DepType:
                res.append(b)
        return GlobalVar._handle_inject_result(res, f'确保依赖名{name}唯一')

    @staticmethod
    def inject_by_type_name(type_name) -> T | None:
        """根据类型名注入，考虑到使用 '类型' 的方式写类型，得到的是个 typing.ForwardRef 实例，用 __forward_arg__ 取出字符串/类型名"""
        res: list[NoAppDepRecord[T]] = []
        for b in GlobalVar.no_app_dep_list:
            # ForwardRef的情况
            if isinstance(b.constructor, str):
                if b.constructor == type_name:
                    res.append(b)
            # 其他情况
            elif b.constructor.__name__ == type_name:
                res.append(b)
        return GlobalVar._handle_inject_result(res, f'确保类型{type_name}只对应一个依赖，或使用命名依赖')

    @staticmethod
    def add_no_app_task(task: MountedTask):
        """添加无app模块的任务"""
        GlobalVar.no_app_task_list.append(task)

    @staticmethod
    def run_no_app_tasks():
        """运行无app模块的任务"""
        for task in GlobalVar.no_app_task_list:
            if task.done:
                continue
            res = task.run()
            if not res:
                task.undo()

    @staticmethod
    def add_no_app_dep_to_app(stack_path: str):
        """把无app的依赖加到app上作为全局依赖"""
        # 把不属于任何子应用且被该子应用扫描的依赖添加给该子应用
        app = GlobalVar.get_app(stack_path)
        exclude_scan_paths = app.config.exclude_scan_paths
        include_scan_paths = app.config.include_scan_paths
        for dep in GlobalVar.no_app_dep_list:
            # 如果该app已经添加过该依赖，就跳过
            if app.stack_path in dep.added_apps:
                continue
            # 默认不注入，只有在额外扫描路径中写了才能注入
            can_add = False
            dep.added_apps.append(app.stack_path)
            item = ModRecord(dep.symbol.stack_path)
            for path in exclude_scan_paths:
                if item.is_child_of_dot_path(path):
                    can_add = False
                    break
            for path in include_scan_paths:
                if item.is_child_of_dot_path(path):
                    can_add = True
                    break
            if can_add:
                app.sa.add_dep(dep)

    @staticmethod
    def change_error_dep_pos(app):
        """修改判断错误的dep_pos
        - 比如app1挂载了app2的Controller，app1先扫描，这时app2没开始扫描，导入Controller中__init__的依赖就会找不到app而添加到到no app上；
        - 静态属性和参数不受影响（因为在静态阶段依赖在npo app上，他俩导入的no app的依赖），而__init__内注入的语句运行时app2已经扫描完毕，再注入会去app2上找，就找不到了；
        - 静态注入的不用管了；
        """
        send_deps = [dep for dep in GlobalVar.no_app_dep_list if app.mod.is_super_of_stack_path(dep.symbol.stack_path)]
        if len(send_deps) == 0:
            return
        # 添加给具体的app
        app.sa.add_dep(*send_deps)
        # 从原来的里面删除
        GlobalVar.no_app_dep_list = [dep for dep in GlobalVar.no_app_dep_list if dep not in send_deps]
