from abc import ABC, abstractmethod

class BaseLLM(ABC):

    @abstractmethod
    def chat(self, input:dict):
        NotImplementedError()