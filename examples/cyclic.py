from di import Container, CyclicDependencyException


class ServiceA:
    def __init__(self, service_b: "ServiceB"):
        self.service_b = service_b


class ServiceB:
    def __init__(self, service_a: "ServiceA"):
        self.service_a = service_a


container = Container()

container.register(ServiceA)
container.register(ServiceB)

try:
    service_a = container.resolve(ServiceA)
except CyclicDependencyException as e:
    print(f"Cyclic dependency detected: {e}")


class NewServiceB:
    def __init__(self):
        pass

    def do_something(self):
        print("New Service B is doing something.")


class NewServiceA:
    def __init__(self, service_b: NewServiceB):
        self.service_b = service_b

    def perform_action(self):
        print("New Service A is performing an action.")
        self.service_b.do_something()


container.register(NewServiceA)
container.register(NewServiceB)

new_service_a = container.resolve(NewServiceA)
new_service_a.perform_action()
