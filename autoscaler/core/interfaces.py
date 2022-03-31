from abc import ABC, abstractmethod


class Strategy(ABC):

    @abstractmethod
    def validate(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def process(self) -> None:
        raise NotImplementedError
