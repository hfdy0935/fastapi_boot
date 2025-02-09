from enum import IntEnum


class GenderEnum(IntEnum):
    MALE = 1
    FEMALE = 0

    @classmethod
    def from_int(cls, n: int):
        return cls.MALE if n == 1 else cls.FEMALE
