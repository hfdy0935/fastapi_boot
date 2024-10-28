from collections.abc import Callable
from copy import deepcopy
from threading import Thread
from fastapi_boot.model.scan_model import MountedTask
from fastapi_boot.utils.judger import is_ancestor


class CommonVar:
    # 应用列表
    __application_list: list = []
    # 挂载之后要运行的任务，key是应用在项目中的路径，value是任务列表
    __mounted_task_list: list[MountedTask] = []
    __new_task_list: list[MountedTask] = []  # 执行任务过程中产生的新任务

    # -------------------------------------------------------- app ------------------------------------------------------- #

    @staticmethod
    def get_app(path: str):
        """根据路径获取application

        Args:
            path (str): 路径

        Returns:
            MainApplication|None: 主应用，可能找不到
        """
        for app in CommonVar.__application_list:
            if app.isin(path):
                return app

    @staticmethod
    def get_all_apps():
        """获取所有application

        Returns:
            list[MainApplication]: 主应用列表
        """
        return CommonVar.__application_list

    @staticmethod
    def add_app(application):
        """添加一个application"""
        CommonVar.__application_list.append(application)

    # ------------------------------------------------------- task ------------------------------------------------------- #

    @staticmethod
    def add_task(task: MountedTask):
        """添加任务"""
        CommonVar.__mounted_task_list.append(task)

    @staticmethod
    def run_task(app_path: str):
        """根据app所在位置，运行该位置下所有task"""
        ls: list[Thread] = []
        i = 0
        while i < len(CommonVar.__mounted_task_list):
            mounted_task = CommonVar.__mounted_task_list[i]
            if is_ancestor(app_path, mounted_task.path):
                t = Thread(target=mounted_task.run)
                # 启动之前把对应位置的任务删除，因为这里已经完成了，线程里面有可能还要run_task
                CommonVar.__mounted_task_list.pop(i)
                t.start()
                ls.append(t)
                # i不变，长度-1，之前的下一位就到i这了
            else:
                i += 1
        for t in ls:
            t.join()

    @staticmethod
    def get_all_tasks():
        return CommonVar.__mounted_task_list

    @staticmethod
    def get_all_tasks_paths():
        return [i.path for i in CommonVar.__mounted_task_list]
