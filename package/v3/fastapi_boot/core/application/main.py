from fastapi import FastAPI


from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.core.var.routes import RoutesVar
from fastapi_boot.core.var.scanner import ScannerVar
from fastapi_boot.model.scan_model import Config, ModPkgItem
from fastapi_boot.utils.get import get_stack_path

from .routes import RoutesApplication
from .scanner import ScannerApplication


class MainApplication(ModPkgItem):
    """主应用"""

    def __init__(self, app: FastAPI, config: Config):
        """
        Args:
            app (FastAPI): FastAPI 实例
            config (Config): 项目配置
        """
        self.app = app
        self.config = config
        # FastApiBoot运行文件路径
        self.setup_file_path = get_stack_path(2)
        # ↑
        super().__init__(self.setup_file_path)
        # 添加到应用列表
        CommonVar.add_app(self)
        # 创建类
        self.sv = ScannerVar(
            self.config.scan_timeout_second,
            [
                self.dot_path,
                *self.config.exclude_scan_path,
            ],  # 需要排除扫描的模块或包的项目路径
            self.config.include_scan_path,
            self.setup_file_path,
        )
        self.rv = RoutesVar(self.sv, self.config.need_pure_api, self.setup_file_path)
        self.sa = ScannerApplication(self.rv, self.sv, self.setup_file_path)
        self.ra = RoutesApplication(self.app, self.rv, self.sv, self.setup_file_path)

        # 开始扫描
        self.sa.scan(self.dir_sys_path, self.dot_path)

    def run(self):
        """run"""
        self.sa.handle_controller_list()
        self.ra.register()
