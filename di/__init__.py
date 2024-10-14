import inspect
import typing


class DIException(Exception):
    """Base exception class for dependency injection errors."""

class ServiceNotRegisteredException(DIException):
    def __init__(self, interface):
        message = f"Service for interface '{interface}' is not registered."
        super().__init__(message)

class CyclicDependencyException(DIException):
    def __init__(self, cls):
        message = f"Cyclic dependency detected: {cls}."
        super().__init__(message)

class MissingTypeAnnotationException(DIException):
    def __init__(self, param_name, cls):
        message = f"Missing type annotation for parameter '{param_name}' in class '{cls.__name__}'."
        super().__init__(message)

class InvalidLifestyleException(DIException):
    def __init__(self, lifestyle):
        message = f"Invalid lifestyle '{lifestyle}'. Valid options are 'transient' or 'singleton'."
        super().__init__(message)


class LifeStyle:
    TRANSIENT = 'transient'
    SINGLETON = 'singleton'


class Container:
    def __init__(self):
        self._services = {}
        self._singletons = {}
        self._resolving = set()
    
    def register(self, interface, implementation=None, lifestyle=LifeStyle.TRANSIENT):
        if lifestyle not in (LifeStyle.TRANSIENT, LifeStyle.SINGLETON):
            raise InvalidLifestyleException(lifestyle)
        if implementation is None:
            implementation = interface
        self._services[interface] = {'implementation': implementation, 'lifestyle': lifestyle}
    
    def resolve(self, interface):
        service = self._services.get(interface)
        if not service:
            raise ServiceNotRegisteredException(interface)
        
        implementation = service['implementation']
        lifestyle = service['lifestyle']
        
        if lifestyle == LifeStyle.SINGLETON:
            if interface not in self._singletons:
                self._singletons[interface] = self._create_instance(implementation)
            return self._singletons[interface]
        else:
            return self._create_instance(implementation)
    
    def _create_instance(self, cls):
        if cls in self._resolving:
            raise CyclicDependencyException(cls)
        
        self._resolving.add(cls)
        try:
            constructor = cls.__init__
            if constructor is object.__init__:
                instance = cls()
            else:
                type_hints = typing.get_type_hints(constructor)
                params = inspect.signature(constructor).parameters
                args = []
                for name, param in params.items():
                    if name == 'self':
                        continue
                    param_annotation = type_hints.get(name, param.annotation)
                    if param_annotation == inspect.Parameter.empty:
                        raise MissingTypeAnnotationException(name, cls)
                    dependency = self.resolve(param_annotation)
                    args.append(dependency)
                instance = cls(*args)
            return instance
        finally:
            self._resolving.remove(cls)