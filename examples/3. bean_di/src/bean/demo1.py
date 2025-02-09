from typing import Annotated
from fastapi_boot.core import Bean, Inject, Autowired

from src.model import Animal, Biology, Config, Plant


# single bean, collect by type
@Bean
def _() -> Config:  # if the return value's type can be inferred rightly, return annotation can be omitted
    return Config(field1='field1', field2=1)


# multi instance, add name as identity
@Bean('animal1')
def _():
    return Animal(id=0, name='cat', age=1, address=[])


@Bean('animal2')
def _():
    return Animal(id=1, name='dog', age=2, address=[])


@Bean('animal3')
def _():
    return Animal(id=2, name='bird', age=0.3, address=[])


@Bean
# need mark return annotation, otherwise will be collected as type `list`
def _(a1: Annotated[Animal, 'animal1'], c: Config) -> list[Animal]:
    a2 = Inject.Qualifier('animal2')@Animal
    a3 = Animal@Inject.Qualifier('animal3')
    # or
    a11 = Inject(Animal, 'animal1')
    # Autowired is an alias for Inject
    a12 = Autowired(Animal, 'animal2')
    assert a1 == a11 and a2 == a12
    return [a1, a2, a3]


@Bean
# need mark return annotation, otherwise will be collected as type `Biology[Any]`
def _() -> Biology[Plant]:
    return Biology(bio=Plant(id=0, name='tree', age=100, height=20))
