class GlobalVar:
    # 应用列表
    __application_list: list = []
    # -------------------------------------------------------- app ------------------------------------------------------- #

    @staticmethod
    def get_app(path: str):
        """根据路径获取application

        Args:
            path (str): 路径

        Returns:
            MainApplication|None: 主应用，可能找不到
        """
        return [app for app in GlobalVar.__application_list if app.is_super_of_stack_path(path)][0]

    @staticmethod
    def get_all_apps():
        """获取所有application

        Returns:
            list[MainApplication]: 主应用列表
        """
        return GlobalVar.__application_list

    @staticmethod
    def add_app(application):
        """添加一个application"""
        GlobalVar.__application_list.append(application)
