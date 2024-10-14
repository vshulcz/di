import unittest
from di import Container, InvalidLifestyleException, LifeStyle
from di import (
    ServiceNotRegisteredException,
    CyclicDependencyException,
    MissingTypeAnnotationException,
)

class IServiceA:
    def do_something(self):
        pass

class ServiceA(IServiceA):
    def do_something(self):
        return "ServiceA is doing something."

class IServiceB:
    def do_something(self):
        pass

class ServiceB(IServiceB):
    def __init__(self, service_a: IServiceA):
        self.service_a = service_a
    
    def do_something(self):
        return f"ServiceB is doing something. {self.service_a.do_something()}"

class ServiceC:
    def __init__(self, service_d: 'ServiceD'):
        self.service_d = service_d

class ServiceD:
    def __init__(self, service_c: ServiceC):
        self.service_c = service_c

class ServiceE:
    def __init__(self, missing_annotation):
        self.missing_annotation = missing_annotation

class TestContainer(unittest.TestCase):
    def setUp(self):
        self.container = Container()
    
    def test_successful_resolution(self):
        """Test successful resolution of services with dependencies."""
        self.container.register(IServiceA, ServiceA)
        self.container.register(IServiceB, ServiceB)
        service_b = self.container.resolve(IServiceB)
        result = service_b.do_something()
        expected = "ServiceB is doing something. ServiceA is doing something."
        self.assertEqual(result, expected)

    def test_service_not_registered_exception(self):
        """Test that resolving an unregistered service raises an exception."""
        with self.assertRaises(ServiceNotRegisteredException) as context:
            self.container.resolve('UnregisteredService')
        self.assertIn("Service for interface 'UnregisteredService' is not registered.", str(context.exception))

    def test_cyclic_dependency_exception(self):
        """Test that resolving services with cyclic dependencies raises an exception."""
        self.container.register(ServiceC)
        self.container.register(ServiceD)
        with self.assertRaises(CyclicDependencyException) as context:
            self.container.resolve(ServiceC)
        self.assertIn("Cyclic dependency detected", str(context.exception))

    def test_missing_type_annotation_exception(self):
        """Test that missing type annotations in constructor raises an exception."""
        self.container.register(ServiceE)
        with self.assertRaises(MissingTypeAnnotationException) as context:
            self.container.resolve(ServiceE)
        self.assertIn("Missing type annotation for parameter 'missing_annotation' in class 'ServiceE'.", str(context.exception))

    def test_singleton_lifestyle(self):
        """Test that singleton services return the same instance."""
        self.container.register(IServiceA, ServiceA, lifestyle=LifeStyle.SINGLETON)
        service_a1 = self.container.resolve(IServiceA)
        service_a2 = self.container.resolve(IServiceA)
        self.assertIs(service_a1, service_a2)

    def test_transient_lifestyle(self):
        """Test that transient services return different instances."""
        self.container.register(IServiceA, ServiceA, lifestyle=LifeStyle.TRANSIENT)
        service_a1 = self.container.resolve(IServiceA)
        service_a2 = self.container.resolve(IServiceA)
        self.assertIsNot(service_a1, service_a2)

    def test_invalid_lifestyle_exception(self):
        """Test that registering a service with an invalid lifestyle raises an exception."""
        with self.assertRaises(InvalidLifestyleException) as context:
            self.container.register(IServiceA, ServiceA, lifestyle='invalid')
        self.assertIn("Invalid lifestyle 'invalid'.", str(context.exception))

    def test_service_with_no_dependencies(self):
        """Test resolving a service with no dependencies."""
        class SimpleService:
            def do_something(self):
                return "SimpleService is doing something."
        
        self.container.register(SimpleService)
        service = self.container.resolve(SimpleService)
        result = service.do_something()
        self.assertEqual(result, "SimpleService is doing something.")

if __name__ == '__main__':
    unittest.main()
