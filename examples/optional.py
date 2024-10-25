from abc import ABC, abstractmethod

from injex import Container


class IOptionalService(ABC):
    @abstractmethod
    def do_something(self): ...


class OptionalService(IOptionalService):
    def do_something(self):
        print("Optional service is doing something.")


class MainService:
    def __init__(self, optional_service: IOptionalService | None = None):
        self.optional_service = optional_service

    def perform_action(self):
        if self.optional_service:
            self.optional_service.do_something()
        else:
            print("Optional service is not available.")


container = Container()

container.register(MainService)

main_service = container.resolve(MainService)
main_service.perform_action()

container.register(IOptionalService, OptionalService)

main_service_with_optional = container.resolve(MainService)
main_service_with_optional.perform_action()
