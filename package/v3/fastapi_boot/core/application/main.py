from fastapi import FastAPI
from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.model.scan import Config, ModPkgItem, MountedTask
from fastapi_boot.utils import get_stack_path

from .scan import ScanApplication


class MainApplication(ModPkgItem):
    """主应用"""

    def __init__(self, app: FastAPI, config: Config):
        """
        Args:
            app (FastAPI): FastAPI 实例
            config (Config): 项目配置
        """
        self.app = app
        # 任务列表，用来存储暂时依赖不全不能初始化或执行的依赖或Bean
        self.task_list: list[MountedTask] = []
        # 任务列表
        self.is_running_task = False
        # FastApiBoot运行文件路径
        self.setup_file_path = get_stack_path(2)
        # ↑
        super().__init__(self.setup_file_path)
        # 添加到全局应用列表
        GlobalVar.add_app(self)

        # 创建类
        self.__sa = ScanApplication(
            self,
            config.scan_timeout_second,
            [
                self.file_dot_path,  # 排除启动文件路径
                *config.exclude_scan_paths,
            ],  # 需要排除扫描的模块或包的项目路径
            config.include_scan_paths,
            max(min(config.max_scan_workers, 100), 1),
            self.setup_file_path,
        )
        # 开始扫描
        self.__sa.scan(self.dir_sys_path)
        # 扫描之后执行任务
        self.run_tasks()
        # 处理是否需要删除swagger的api页面
        if config.need_pure_api:
            for _ in range(4):
                app.routes.pop(0)

    @property
    def sa(self):
        return self.__sa

    def add_task(self, *task: MountedTask):
        """添加一个或多个任务到任务列表后面"""
        self.task_list.extend(task)

    def run_tasks(self):
        """执行注册到扫描之后的任务"""
        for task in self.task_list:
            if task.done:
                continue
            res = task.run()
            if not res:
                # 如果运行不成功，改为未运行，以便下次能运行
                task.undo()
