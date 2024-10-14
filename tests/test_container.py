from abc import ABC, abstractmethod
import unittest

from di import (
    Container,
    DIException, 
    LifeStyle,
    InvalidLifestyleException, 
    ServiceNotRegisteredException,
    CyclicDependencyException,
    MissingTypeAnnotationException,
    inject,
)

class IServiceA:
    def do_something(self):
        pass

class ServiceA(IServiceA):
    def do_something(self):
        return "Service A is doing something."

class IServiceB:
    def do_something(self):
        pass

class ServiceB(IServiceB):
    def __init__(self, service_a: IServiceA):
        self.service_a = service_a
    
    def do_something(self):
        return f"Service B is doing something. {self.service_a.do_something()}"

class ServiceC:
    def __init__(self, service_d: 'ServiceD'):
        self.service_d = service_d

class ServiceD:
    def __init__(self, service_c: ServiceC):
        self.service_c = service_c

class ServiceE:
    def __init__(self, missing_annotation):
        self.missing_annotation = missing_annotation

class ServiceA_cyclic:
    def __init__(self, service_b: 'ServiceB_cyclic'):
        self.service_b = service_b

class ServiceB_cyclic:
    def __init__(self, service_c: 'ServiceC_cyclic'):
        self.service_c = service_c

class ServiceC_cyclic:
    def __init__(self, service_a: ServiceA_cyclic):
        self.service_a = service_a

class ServiceA_prop_inj:
    @inject
    def service_b(self) -> 'ServiceB_prop_inj':
        pass

class ServiceB_prop_inj:
    @inject
    def service_a(self) -> ServiceA_prop_inj:
        pass

class ServiceD_order:
    def __init__(self, service_e: 'ServiceE_order'):
        self.service_e = service_e

class ServiceE_order:
    def __init__(self):
        self.value = "Service E"

class DependencyUnregistered(ABC):
    @abstractmethod
    def do_something(self):
        pass


class TestContainer(unittest.TestCase):
    def setUp(self):
        self.container = Container()
    
    def test_successful_resolution(self):
        self.container.register(IServiceA, ServiceA)
        self.container.register(IServiceB, ServiceB)
        service_b = self.container.resolve(IServiceB)
        result = service_b.do_something()
        expected = "Service B is doing something. Service A is doing something."
        self.assertEqual(result, expected)

    def test_service_not_registered_exception(self):
        with self.assertRaises(ServiceNotRegisteredException) as context:
            self.container.resolve('UnregisteredService')
        self.assertIn(
            "Service for interface 'UnregisteredService' is not registered.",
            str(context.exception)
        )

    def test_cyclic_dependency_exception(self):
        self.container.register(ServiceC)
        self.container.register(ServiceD)
        with self.assertRaises(CyclicDependencyException) as context:
            self.container.resolve(ServiceC)
        self.assertIn("Cyclic dependency detected", str(context.exception))

    def test_missing_type_annotation_exception(self):
        self.container.register(ServiceE)
        with self.assertRaises(MissingTypeAnnotationException) as context:
            self.container.resolve(ServiceE)
        self.assertIn(
            "Missing type annotation for parameter 'missing_annotation' in class 'ServiceE'.",
            str(context.exception)
        )

    def test_singleton_lifestyle(self):
        self.container.register(IServiceA, ServiceA, lifestyle=LifeStyle.SINGLETON)
        service_a1 = self.container.resolve(IServiceA)
        service_a2 = self.container.resolve(IServiceA)
        self.assertIs(service_a1, service_a2)

    def test_transient_lifestyle(self):
        self.container.register(IServiceA, ServiceA, lifestyle=LifeStyle.TRANSIENT)
        service_a1 = self.container.resolve(IServiceA)
        service_a2 = self.container.resolve(IServiceA)
        self.assertIsNot(service_a1, service_a2)

    def test_invalid_lifestyle_exception(self):
        with self.assertRaises(InvalidLifestyleException) as context:
            self.container.register(IServiceA, ServiceA, lifestyle='invalid')
        self.assertIn("Invalid lifestyle 'invalid'.", str(context.exception))

    def test_service_with_no_dependencies(self):
        class SimpleService:
            def do_something(self):
                return "SimpleService is doing something."
        
        self.container.register(SimpleService)
        service = self.container.resolve(SimpleService)
        result = service.do_something()
        self.assertEqual(result, "SimpleService is doing something.")
    
    def test_named_registrations(self):
        class ILogger(ABC):
            @abstractmethod
            def log(self, message: str): ...

        class ConsoleLogger(ILogger):
            def log(self, message: str):
                return f"Console Logger: {message}"

        class FileLogger(ILogger):
            def log(self, message: str):
                return f"File Logger: {message}"

        self.container.register(ILogger, ConsoleLogger, name='console')
        self.container.register(ILogger, FileLogger, name='file')

        console_logger = self.container.resolve(ILogger, name='console')
        file_logger = self.container.resolve(ILogger, name='file')

        self.assertIsInstance(console_logger, ConsoleLogger)
        self.assertIsInstance(file_logger, FileLogger)
        self.assertNotEqual(console_logger.log("Test"), file_logger.log("Test"))
    
    def test_factory_registration(self):
        class IService(ABC):
            @abstractmethod
            def do_work(self): ...

        class Service(IService):
            def __init__(self, value: int):
                self.value = value

            def do_work(self):
                return f"Value is {self.value}"

        def factory(container):
            return Service(42)

        self.container.register_factory(IService, factory)

        service = self.container.resolve(IService)
        result = service.do_work()
        self.assertEqual(result, "Value is 42")

    def test_optional_dependencies(self):
        class IOptionalService(ABC):
            @abstractmethod
            def do_something(self): ...

        class OptionalService(IOptionalService):
            def do_something(self):
                return "Optional service is doing something."

        class MainService:
            def __init__(self, optional_service: IOptionalService | None = None):
                self.optional_service = optional_service

            def perform_action(self):
                if self.optional_service:
                    return self.optional_service.do_something()
                else:
                    return "Optional service is not available."

        self.container.register(MainService)

        main_service = self.container.resolve(MainService)
        result = main_service.perform_action()
        self.assertEqual(result, "Optional service is not available.")

        self.container.register(IOptionalService, OptionalService)

        main_service_with_optional = self.container.resolve(MainService)
        result = main_service_with_optional.perform_action()
        self.assertEqual(result, "Optional service is doing something.")

    def test_property_injection(self):
        class DependencyA:
            def work(self):
                return "Dependency A is working."

        class DependencyB:
            def work(self):
                return "Dependency B is working."

        class ServiceWithPropertyInjection:
            @inject
            def dependency_a(self) -> DependencyA: ...

            @inject
            def dependency_b(self) -> DependencyB: ...

            def perform_action(self):
                return f"{self.dependency_a.work()} and {self.dependency_b.work()}"

        self.container.register(DependencyA)
        self.container.register(DependencyB)
        self.container.register(ServiceWithPropertyInjection)

        service = self.container.resolve(ServiceWithPropertyInjection)
        result = service.perform_action()
        expected = "Dependency A is working. and Dependency B is working."
        self.assertEqual(result, expected)

    def test_scoped_lifecycle(self):
        class IService(ABC):
            @abstractmethod
            def get_id(self): ...

        class Service(IService):
            def __init__(self):
                self.id = id(self)

            def get_id(self):
                return self.id

        self.container.register(IService, Service, lifestyle=LifeStyle.SCOPED)

        scope1 = self.container.create_scope()
        service1_a = scope1.resolve(IService)
        service1_b = scope1.resolve(IService)
        self.assertIs(service1_a, service1_b)

        scope2 = self.container.create_scope()
        service2_a = scope2.resolve(IService)
        self.assertIsNot(service1_a, service2_a)

    def test_multiple_implementations(self):
        class IService(ABC):
            @abstractmethod
            def process(self): ...

        class ImplOne(IService):
            def process(self):
                return "Implementation One"

        class ImplTwo(IService):
            def process(self):
                return "Implementation Two"

        self.container.register(IService, ImplOne, name='one')
        self.container.register(IService, ImplTwo, name='two')

        service_one = self.container.resolve(IService, name='one')
        service_two = self.container.resolve(IService, name='two')

        self.assertEqual(service_one.process(), "Implementation One")
        self.assertEqual(service_two.process(), "Implementation Two")

    def test_unregistered_optional_dependency(self):
        class IService(ABC): ...

        class ConsumerService:
            def __init__(self, service: IService | None = None):
                self.service = service

        self.container.register(ConsumerService)

        consumer = self.container.resolve(ConsumerService)
        self.assertIsNone(consumer.service)

    def test_complex_cyclic_dependency(self):
        self.container.register(ServiceA_cyclic)
        self.container.register(ServiceB_cyclic)
        self.container.register(ServiceC_cyclic)

        with self.assertRaises(CyclicDependencyException) as context:
            self.container.resolve(ServiceA_cyclic)
        self.assertIn("Cyclic dependency detected", str(context.exception))

    def test_singleton_and_scoped_lifecycles(self):
        class IServiceSingleton:
            def __init__(self):
                self.id = id(self)

        class IServiceScoped:
            def __init__(self):
                self.id = id(self)

        class ConsumerService:
            def __init__(self, singleton_service: IServiceSingleton, scoped_service: IServiceScoped):
                self.singleton_service = singleton_service
                self.scoped_service = scoped_service

        self.container.register(IServiceSingleton, lifestyle=LifeStyle.SINGLETON)
        self.container.register(IServiceScoped, lifestyle=LifeStyle.SCOPED)
        self.container.register(ConsumerService)

        scope1 = self.container.create_scope()
        consumer1 = scope1.resolve(ConsumerService)
        singleton_id_1 = consumer1.singleton_service.id
        scoped_id_1 = consumer1.scoped_service.id

        scope2 = self.container.create_scope()
        consumer2 = scope2.resolve(ConsumerService)
        singleton_id_2 = consumer2.singleton_service.id
        scoped_id_2 = consumer2.scoped_service.id

        self.assertEqual(singleton_id_1, singleton_id_2)
        self.assertNotEqual(scoped_id_1, scoped_id_2)

    def test_resolution_order(self):
        self.container.register(ServiceE_order)
        self.container.register(ServiceD_order)

        service_d = self.container.resolve(ServiceD_order)
        self.assertEqual(service_d.service_e.value, "Service E")

    def test_factory_with_dependencies(self):
        class IDependency(ABC):
            @abstractmethod
            def get_value(self): ...

        class Dependency(IDependency):
            def get_value(self):
                return 99

        class IService(ABC):
            @abstractmethod
            def get_combined_value(self): ...

        def factory(container):
            dependency = container.resolve(IDependency)

            class Service(IService):
                def get_combined_value(self):
                    return f"Combined value is {dependency.get_value() + 1}"

            return Service()

        self.container.register(IDependency, Dependency)
        self.container.register_factory(IService, factory)

        service = self.container.resolve(IService)
        result = service.get_combined_value()
        self.assertEqual(result, "Combined value is 100")

    def test_exception_on_invalid_factory(self):
        with self.assertRaises(ValueError) as context:
            self.container.register_factory('SomeInterface', 'NotACallable')
        self.assertIn("Factory must be callable", str(context.exception))

    def test_optional_dependency_not_registered(self):
        class IService(ABC): ...

        class Consumer:
            def __init__(self, service: IService | None = None):
                self.service = service

        self.container.register(Consumer)
        consumer = self.container.resolve(Consumer)
        self.assertIsNone(consumer.service)

    def test_property_injection_with_unregistered_dependency(self):
        class Consumer:
            @inject
            def dependency(self) -> DependencyUnregistered: ...

        self.container.register(Consumer)

        with self.assertRaises(ServiceNotRegisteredException) as context:
            self.container.resolve(Consumer)
        self.assertIn("Service for interface '<class '__main__.DependencyUnregistered'> with name 'None'' is not registered.", str(context.exception))

    def test_cyclic_dependency_with_property_injection(self):
        self.container.register(ServiceA_prop_inj)
        self.container.register(ServiceB_prop_inj)

        with self.assertRaises(CyclicDependencyException) as context:
            self.container.resolve(ServiceA_prop_inj)
        self.assertIn("Cyclic dependency detected", str(context.exception))

    def test_custom_exception_handling(self):
        class CustomException(DIException): ...

        class FaultyService:
            def __init__(self):
                raise CustomException("Custom error occurred.")

        self.container.register(FaultyService)

        with self.assertRaises(CustomException) as context:
            self.container.resolve(FaultyService)
        self.assertIn("Custom error occurred.", str(context.exception))

if __name__ == '__main__':
    unittest.main()
