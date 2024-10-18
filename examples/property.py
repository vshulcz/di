from di import Container, inject


class DependencyA:
    def do_work(self):
        print("Dependency A is working.")


class DependencyB:
    def do_work(self):
        print("Dependency B is working.")


class PropertyInjectedService:
    @inject
    def dependency_a(self) -> DependencyA: ...

    @inject
    def dependency_b(self) -> DependencyB: ...

    def perform_action(self):
        self.dependency_a.do_work()
        self.dependency_b.do_work()


container = Container()

container.register(DependencyA)
container.register(DependencyB)
container.register(PropertyInjectedService)

service = container.resolve(PropertyInjectedService)
service.perform_action()
