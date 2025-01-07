import hashlib

from fastapi_boot.core import Component


@Component
class MD5Util:
    def encrypt(self, data: str):
        md5_hash = hashlib.md5()
        md5_hash.update(data.encode('utf-8'))
        return md5_hash.hexdigest()

    def verify(self, data: str, hashed_value: str):
        return self.encrypt(data) == hashed_value
