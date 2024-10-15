import inspect
from typing import Annotated, Callable, Type, Union

from pydantic import BaseModel, Field


class Symbol(BaseModel):
    """
    - 路由的唯一标识
    """
    file_path: Annotated[str, Field(description='文件在系统的的绝对路径')]
    context_path: Annotated[str, Field(description='该对象的上下文路径')]

    def equals(self, other: 'Symbol') -> bool:
        """
        - 判断两个Symbol实例是否相等，即对应的两个路由是否路径是否相同
        """
        return self.file_path == other.file_path and self.context_path == other.context_path

    def contains(self, other: 'Symbol') -> bool:
        """
        - 判断是否是other的后代路由
        - 用于在扫描类时使其下所有路由受控
        """
        return self.file_path == other.file_path and other.context_path in self.context_path

    def is_child(self, other: 'Symbol') -> bool:
        """
        - 判断是否是other的子路由
        """
        return self.contains(other) and not self.equals(other) and len(self.context_path.split('.'))-1 == len(other.context_path.split('.'))

    @staticmethod
    def from_obj(obj: Union[Type, Callable]) -> 'Symbol':
        """根据类/类的方法获取唯一symbol

        Args:
            obj (Callable): 要获取路径信息的对象（这里是类或函数）

        Returns:
            Symbol: symbol类实例，{文件绝对路径, 该对象在文件的引用路径}
        """
        file_path = inspect.getfile(obj)
        file_path = file_path[0].upper()+file_path[1:]
        context_path = obj.__qualname__
        return Symbol(file_path=file_path, context_path=context_path)

    @property
    def pos(self) -> str:
        return f'{self.file_path}  {self.context_path}'
