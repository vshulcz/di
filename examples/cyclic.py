from di import Container


class ServiceC:
    def __init__(self, service_d: 'ServiceD'):
        self.service_d = service_d

class ServiceD:
    def __init__(self, service_c: ServiceC):
        self.service_c = service_c

container = Container()

container.register(ServiceC)
container.register(ServiceD)

service_c = container.resolve(ServiceC)
