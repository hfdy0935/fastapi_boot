from concurrent.futures import Future, ThreadPoolExecutor
import concurrent.futures
import os
from typing import Final, Generic, TypeVar
import concurrent

from fastapi_boot.exception import InjectFailException
from fastapi_boot.model.scan import InjectItem, ModPkgItem

T = TypeVar("T")


def scan_task(idx: int, ls: list, dot_path: str):
    """扫描"""
    print("\r" + " " * 120, end="")
    print(
        f"\r正在扫描：{(idx + 1) * 100 / len(ls):.2f}% {dot_path}",
        end="",
    )
    try:
        __import__(dot_path)
    except Exception as e:
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
        setup_stack_path: str,
    ):
        self.application = app
        # 扫描超时时间
        self.scan_timeout_second = scan_timeout_second
        # 需要排除的包/模块在项目中的路径
        self.exclude_path_list = exclude_path_list
        # 需要额外扫描的包/模块在项目中的路径
        self.include_path_list = include_path_list
        # 扫描最大线程数
        self.max_workers = max_workers

        # 项目下所有模块列表
        self.__mod_list: Final[list[ModPkgItem]] = []
        # 可注入的组件列表
        self.__inject_bean_list: Final[list[InjectItem]] = []

    # -------------------------------------------------------- 依赖 -------------------------------------------------------- #

    def get_inject_list(self):
        return self.__inject_bean_list

    def add_inject(self, inject: InjectItem):
        self.get_inject_list().append(inject)

    # ----------------------------------------------------- 遍历获取模块类列表 ---------------------------------------------------- #

    def _walk_module_path_list(self, scan_path: str):
        """遍历扫描路径，获得项目下所有模块的路径类列表

        Args:
            scan_path (str): 扫描路径
        """
        for i in os.walk(scan_path):
            # dirpath: 包在系统的绝对路径
            dirpath, _, filenames = i
            # 包中的所有模块
            for filename in filenames:
                # 只扫描.py文件
                if not filename.endswith(".py"):
                    continue
                mod_item = ModPkgItem(os.path.join(dirpath, filename))
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
        """初始化项目中所有bean"""
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

        # 任务队列
        # queue = Queue()
        # for idx, mod in enumerate((ls := self.__mod_list)):
        #     queue.put(scan_task(idx, ls, mod.file_dot_path))
        # threads: list[Thread] = []

        # def worker(queue: Queue):
        #     while True:
        #         try:
        #             task = queue.get()
        #             if task is None:
        #                 break
        #             task[0](task[1])
        #         finally:
        #             queue.task_done()

        # for _ in range(self.max_workers):
        #     t = Thread(target=worker, args=(queue,))
        #     t.start()
        #     threads.append(t)
        # for _ in range(self.max_workers):
        #     queue.put(None)
        # for t in threads:
        #     t.join()

        # 线程
        # tasks: list[Thread] = []
        # for idx, mod in enumerate((ls := self.__mod_list)):
        #     t = Thread(
        #         target=scan_task,
        #         args=(
        #             idx,
        #             ls,
        #             mod.file_dot_path,
        #         ),
        #     )
        #     t.start()
        #     tasks.append(t)
        # for t in tasks:
        #     t.join()
        print(f"\n\n> >   {self.application.file_dot_path} 扫描完成\n")

    # ----------------------------------------------------- 注入依赖 ---------------------------------------------------- #

    def _handle_inject_result(self, find_list: list[InjectItem[T]], raise_msg: str) -> T | None:
        """处理注入结果"""
        # 如果没找到
        l = len(find_list)
        if l == 0:
            return None
        # 如果找到多个
        if l > 1:
            raise_pos = "\n".join([f"\t{idx}. {i.symbol.pos}" for idx, i in enumerate(find_list, start=1)])
            raise InjectFailException(f"找到{l}个依赖，注入失败，{raise_msg}，位置：\n{raise_pos}")
        # 只有一个
        return find_list[0].value

    def inject_by_type(self, DepType: type[T]) -> T | None:
        """根据类型注入依赖"""
        res: list[InjectItem[T]] = []
        for b in self.get_inject_list():
            # 考虑到Bean返回字符串，类型后定义的情况
            if b.constructor == DepType or b.constructor == DepType.__name__:
                res.append(b)
        return self._handle_inject_result(res, f"确保类型{DepType.__name__}只对应一个依赖，或使用命名依赖")

    def inject_by_name(self, name: str) -> T | None:
        """根据名称注入依赖"""
        res: list[InjectItem[T]] = []
        for b in self.get_inject_list():
            if b.name == name:
                res.append(b)
        return self._handle_inject_result(res, f"确保依赖名{name}唯一")

    def inject_by_type_name(self, type_name) -> T | None:
        """根据类型名注入，考虑到使用 '类型' 的方式写类型，得到的是个 typing.ForwardRef 实例，用 __forward_arg__ 取出字符串/类型名"""
        res: list[InjectItem[T]] = []
        for b in self.get_inject_list():
            # ForwardRef的情况
            if isinstance(b.constructor, str):
                if b.constructor == type_name:
                    res.append(b)
            # 其他情况
            elif b.constructor.__name__ == type_name:

                res.append(b)
        return self._handle_inject_result(res, f"确保类型{type_name}只对应一个依赖，或使用命名依赖")

    def scan(self, scan_path: str):
        """
        Args:
            scan_path (str): 扫描路径
        """
        self._walk_module_path_list(scan_path)
        self._init_inject_list()
