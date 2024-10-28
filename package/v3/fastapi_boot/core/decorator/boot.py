from fastapi import FastAPI

from fastapi_boot.core.application.main import MainApplication
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.model.scan_model import Config


class FastApiBootApplication:
    num = 0
    """启动类"""

    def __init__(self, app: FastAPI, config: Config = Config()):
        self.app = MainApplication(app, config)
        # 挂载完毕，执行任务
        CommonVar.run_task(self.app.dir_sys_path)

    def run(self):
        self.app.run()

    @staticmethod
    def run_app(app: FastAPI, config: Config = Config()):
        FastApiBootApplication.num += 1
        application = MainApplication(app, config)
        CommonVar.run_task(application.dir_sys_path)
        application.run()
