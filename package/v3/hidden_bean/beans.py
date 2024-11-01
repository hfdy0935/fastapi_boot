from fastapi_boot import Bean


class HiddenBean:
    name = "hiidden-bean"


@Bean
def get_hidden_bean():
    return HiddenBean()
