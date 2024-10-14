from di import Container


class IServiceA:
    def do_something_a(self):
        pass

class ServiceA(IServiceA):
    def do_something_a(self):
        print("Service A do something.")

class IServiceB:
    def do_something_b(self):
        pass

class ServiceB(IServiceB):
    def __init__(self, service_a: IServiceA):
        self.service_a = service_a
    
    def do_something_b(self):
        print("Service B do something.")
        self.service_a.do_something_a()

container = Container()
container.register(IServiceA, ServiceA, lifestyle='singleton')
container.register(IServiceB, ServiceB, lifestyle='singleton')

service_b = container.resolve(IServiceB)
service_b.do_something_b()