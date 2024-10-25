from abc import ABC, abstractmethod

from injex import Container


class IService(ABC):
    @abstractmethod
    def perform_action(self): ...


class Service(IService):
    def __init__(self, config_value: str):
        self.config_value = config_value

    def perform_action(self):
        print(f"Service is performing an action with config: {self.config_value}")


container = Container()


def service_factory():
    config_value = "CustomConfigValue"
    return Service(config_value)


container.register_factory(IService, service_factory)

service = container.resolve(IService)
service.perform_action()
