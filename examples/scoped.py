from abc import ABC, abstractmethod

from di import Container, LifeStyle


class IRequestHandler(ABC):
    @abstractmethod
    def handle(self): ...


class RequestHandler(IRequestHandler):
    def __init__(self):
        self.id = id(self)

    def handle(self):
        print(f"Handling request with handler ID: {self.id}")


container = Container()

container.register(IRequestHandler, RequestHandler, lifestyle=LifeStyle.SCOPED)


def handle():
    scope = container.create_scope()
    handler = scope.resolve(IRequestHandler)
    handler.handle()
    another_handler = scope.resolve(IRequestHandler)
    print(f"Same handler in scope: {handler is another_handler}")


print("Handling first request:")
handle()

print("\nHandling second request:")
handle()
