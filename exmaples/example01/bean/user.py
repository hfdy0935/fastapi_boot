from typing import Annotated

from fastapi_boot import Autowired, Bean

from model.user import User


@Bean('a')
def _():
    return User(name='a', age=20)


@Bean('b')
def _():
    return User(name='b', age=21, friends=[Autowired(User, 'a')])


@Bean('c')
def _(u1: Annotated[User, 'a']):
    u2 = Autowired.Qualifier('b') @ User
    return User(name='c', age=22, friends=[u1, u2])
