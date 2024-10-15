import os
from pathlib import Path
from typing import Final
from fastapi import FastAPI

from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.core.var.routes import RoutesVar
from fastapi_boot.core.var.scanner import ScannerVar
from fastapi_boot.model.scan_model import Config
from fastapi_boot.utils.generator import get_stack_path

from .routes import RoutesApplication
from .scanner import ScannerApplication


class MainApplication:
    """main application"""

    def __init__(self, app: FastAPI, config: Config):
        """

        Args:
            app (FastAPI): FastAPI instance
            config (Config): config of project
        """

        # project setup file path
        self.setup_file_path = get_stack_path(2)
        # ↑ it's dirname
        self.setup_dir_path = os.path.dirname(self.setup_file_path)
        # project's path in root project(if exists), separated by dot
        self.dot_prefix = ".".join(
            Path(self.setup_dir_path.replace(os.getcwd(), "")).parts[1:]
        )
        # exclude scan path/file
        exclude_setupfile_dot_proj_path='.'.join(Path(self.setup_file_path.replace(os.getcwd(), "")[:-3]).parts[1:])
        self.sv: Final[ScannerVar] = ScannerVar(
            config.scan_timeout_second, [exclude_setupfile_dot_proj_path]+config.exclude_scan_path,config.include_scan_path
        )
        self.rv: Final[RoutesVar] = RoutesVar(self.sv, config.need_pure_api)
        self.sa: Final[ScannerApplication] = ScannerApplication(self.rv, self.sv)
        self.ra: Final[RoutesApplication] = RoutesApplication(app, self.rv, self.sv)

        # add application
        CommonVar.set_application_info(os.path.dirname(self.setup_file_path), self)
        # 1. scan
        self.sa.scan(self.setup_dir_path, self.dot_prefix)

    def get_sv(self) -> ScannerVar:
        return self.sv

    def get_sa(self) -> ScannerApplication:
        return self.sa

    def get_rv(self) -> RoutesVar:
        return self.rv

    def get_ra(self) -> RoutesApplication:
        return self.ra

    def run(self):
        """run"""
        self.sa.handle_controller_list()
        self.ra.register()
