from abc import ABC, abstractmethod
from di import Container

class ILogger(ABC):
    @abstractmethod
    def log(self, message: str): ...

class ConsoleLogger(ILogger):
    def log(self, message: str):
        print(f"Console Logger: {message}")

class FileLogger(ILogger):
    def log(self, message: str):
        with open('log.txt', 'a') as f:
            f.write(f"File Logger: {message}\n")

container = Container()

container.register(ILogger, ConsoleLogger, name='console')
container.register(ILogger, FileLogger, name='file')

console_logger = container.resolve(ILogger, name='console')
console_logger.log("This is a message to the console.")

file_logger = container.resolve(ILogger, name='file')
file_logger.log("This is a message to the file.")