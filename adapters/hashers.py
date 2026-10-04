from abc import ABC, abstractmethod
from passlib.hash import sha256_crypt


class AbstractPasswordHasher(ABC):

    @abstractmethod
    def hash(self, password: str) -> str:
        raise NotImplementedError()

    @abstractmethod
    def verify(self, password: str, hashed_password: str) -> bool:
        raise NotImplementedError()


class PassLibPasswordHasher(AbstractPasswordHasher):

    def hash(self, password: str) -> str:
        return sha256_crypt.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        return sha256_crypt.verify(password, hashed_password)