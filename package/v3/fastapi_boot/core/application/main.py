from fastapi import FastAPI
from fastapi_boot.globalvar import GlobalVar
from fastapi_boot.model.scan import Config, ModRecord, MountedTask

from .scan import ScanApplication


class MainApplication:
    """主应用"""

    def __init__(self, app: FastAPI, config: Config, stack_path: str):
        """
        Args:
            app (FastAPI): FastAPI 实例
            config (Config): 项目配置
            stack_path (str): 启动文件
        """
        self.app = app
        self.config = config
        self.stack_path = stack_path
        # 任务列表，用来存储暂时依赖不全不能初始化或执行的依赖或Bean
        self.task_list: list[MountedTask] = []
        # 顺序一定不能乱
        self.mod = ModRecord(self.stack_path)
        # 创建类
        self.sa = ScanApplication(
            self,
            config.scan_timeout_second,
            [
                self.mod.file_dot_path,  # 排除启动文件路径
                *config.exclude_scan_paths,
            ],  # 需要排除扫描的模块或包的项目路径
            config.include_scan_paths,
            max(min(config.max_scan_workers, 100), 1),
        )
        # 添加到全局应用列表
        GlobalVar.add_app(self)

        # 开始扫描
        if config.scan:
            self.sa.scan(self.mod.dir_sys_path)
        # 扫描之后执行任务
        self.run_tasks()
        GlobalVar.run_app_task(self)
        # 每个app创建完，更新一次依赖所属关系，防止错误
        GlobalVar.change_error_dep_pos()
        # 处理是否需要删除swagger的api页面
        if config.need_pure_api:
            for _ in range(4):
                app.routes.pop(0)

    def add_task(self, *task: MountedTask):
        """添加一个或多个任务到任务列表"""
        self.task_list.extend(task)

    def run_tasks(self):
        """执行app的任务"""
        for task in self.task_list:
            if task.done:
                continue
            res = task.run()
            if not res:
                task.undo()
        GlobalVar.add_no_app_dep_to_app(self.stack_path)
