import concurrent
import concurrent.futures
import os
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Final, Generic, TypeVar

from fastapi_boot.exception import InjectFailException
from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.model.scan import DepRecord, ModRecord

T = TypeVar('T')


def scan_task(idx: int, ls: list, dot_path: str):
    """扫描一个模块

    Args:
        idx (int): 索引，用于计算进度
        ls (list): 总数，用于计算进度
        dot_path (str): 导入路径

    Raises:
        e: InjectFailException
    """
    print('\r' + ' ' * 120, end="")
    print(
        f'\r正在扫描：{(idx + 1) * 100 / len(ls):.2f}% {dot_path}',
        end="",
    )
    try:
        __import__(dot_path)
    except InjectFailException as e:
        raise e


class ScanApplication(Generic[T]):
    """扫描应用"""

    def __init__(
        self,
        app,
        scan_timeout_second: int | float,
        exclude_path_list: list[str],
        include_path_list: list[str],
        max_workers: int,
    ):
        self.app = app
        # 扫描超时时间
        self.scan_timeout_second = scan_timeout_second
        # 需要排除的包/模块在项目中的路径
        self.exclude_path_list = exclude_path_list
        # 需要额外扫描的包/模块在项目中的路径
        self.include_path_list = include_path_list
        # 扫描最大线程数
        self.max_workers = max_workers

        # 项目下所有模块列表
        self.__mod_list: Final[list[ModRecord]] = []
        # 可注入的组件列表
        self.__dep_list: Final[list[DepRecord]] = []

    # -------------------------------------------------------- 依赖 -------------------------------------------------------- #

    def get_dep_list(self):
        return self.__dep_list

    def add_dep(self, *inject: DepRecord):
        self.__dep_list.extend(inject)

    # ----------------------------------------------------- 遍历获取模块类列表 ---------------------------------------------------- #
    def get_mod_list(self):
        return self.__mod_list

    def _walk_module_path_list(self, scan_path: str):
        """遍历扫描路径，获得项目下所有模块

        Args:
            scan_path (str): 扫描路径
        """
        for i in os.walk(scan_path):
            # dirpath: 包在系统的绝对路径
            dirpath, _, filenames = i
            # 包中的所有模块
            for filename in filenames:
                # 只扫描.py文件
                if not filename.endswith('.py'):
                    continue
                mod_item = ModRecord(os.path.join(dirpath, filename))
                should_add = True  # 是否可以添加到扫描路径
                # 是否在排除路径列表中
                for j in self.exclude_path_list:
                    if mod_item.is_child_of_dot_path(j):
                        should_add = False
                        break
                # 是否在额外扫描路径列表中
                for k in self.include_path_list:
                    if mod_item.is_child_of_dot_path(k):
                        should_add = True
                        break
                if should_add:
                    self.__mod_list.append(mod_item)

    # -------------------------------------------------- 导包，让装饰器静态阶段生效 ------------------------------------------------- #

    def _init_inject_list(self):
        """导入模块，开始收集和注入依赖"""
        # 线程池
        futures: list[Future] = []
        with ThreadPoolExecutor(self.max_workers) as executor:
            for idx, mod in enumerate((ls := self.__mod_list)):
                future = executor.submit(scan_task, idx, ls, mod.file_dot_path)
                futures.append(future)
            concurrent.futures.wait(futures)
            # 执行结果
            for future in futures:
                future.result()
        print(f'\n\n> >   {self.app.mod.file_dot_path} 扫描完成\n')

    # ----------------------------------------------------- 注入依赖 ---------------------------------------------------- #

    def inject_by_type(self, DepType: type[T]) -> T | None:
        """根据类型注入依赖

        Args:
            DepType (type[T]): 依赖类型

        Returns:
            T | None: 结果 | None
        """
        res: list[DepRecord[T]] = []
        for b in [*self.get_dep_list(), *self.app.ra.get_dep_list()]:
            # 考虑到Bean返回字符串，类型后定义的情况
            if b.constructor == DepType or b.constructor == DepType.__name__:
                res.append(b)
        return GlobalVar._handle_inject_result(res, f'确保类型{DepType.__name__}只对应一个依赖，或使用命名依赖')

    def inject_by_name(self, name: str, DepType: type[T]) -> T | None:
        """根据依赖名注入依赖

        Args:
            name (str): 依赖名
            DepType (type[T]): 依赖类型，只有依赖名和类型都对应才算找到

        Returns:
            T | None: 结果 | None
        """
        res: list[DepRecord[T]] = []
        for b in self.get_dep_list():
            if b.name == name and b.constructor == DepType:
                res.append(b)
        return GlobalVar._handle_inject_result(res, f'确保依赖名{name}唯一')

    def inject_by_type_name(self, type_name) -> T | None:
        """根据类型名注入，考虑到使用 '类型' 的方式写类型，得到的是个 typing.ForwardRef 实例，用 __forward_arg__ 取出字符串（类型名）

        Args:
            type_name (_type_): 类型名

        Returns:
            T | None: 结果 | None
        """
        res: list[DepRecord[T]] = []
        for b in self.get_dep_list():
            # ForwardRef的情况
            if isinstance(b.constructor, str):
                if b.constructor == type_name:
                    res.append(b)
            # 其他情况
            elif b.constructor.__name__ == type_name:

                res.append(b)
        return GlobalVar._handle_inject_result(res, f'确保类型{type_name}只对应一个依赖，或使用命名依赖')

    def scan(self, scan_path: str):
        """开始扫描

        Args:
            scan_path (str): 扫描根路径（系统绝对路径）
        """
        self._walk_module_path_list(scan_path)
        self._init_inject_list()
