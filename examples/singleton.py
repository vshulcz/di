from di import Container, LifeStyle


class IService:
    def do_something(self):
        pass

class ServiceImplementation(IService):
    def do_something(self):
        print("Do something.")

container = Container()
container.register(IService, ServiceImplementation, lifestyle=LifeStyle.SINGLETON)

service1 = container.resolve(IService)
service2 = container.resolve(IService)

print(service1 is service2)