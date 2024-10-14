import inspect
import types
import typing


class DIException(Exception):
    """Base exception class for dependency injection errors."""

class ServiceNotRegisteredException(DIException):
    def __init__(self, interface_description: str):
        message = f"Service for interface '{interface_description}' is not registered."
        super().__init__(message)

class CyclicDependencyException(DIException):
    def __init__(self, cls: typing.Type):
        message = f"Cyclic dependency detected: {cls}."
        super().__init__(message)

class MissingTypeAnnotationException(DIException):
    def __init__(self, param_name: str, cls: typing.Type):
        message = f"Missing type annotation for parameter '{param_name}' in class '{cls.__name__}'."
        super().__init__(message)

class InvalidLifestyleException(DIException):
    def __init__(self, lifestyle: str):
        message = f"Invalid lifestyle '{lifestyle}'. Valid options are 'transient' or 'singleton'."
        super().__init__(message)


def inject(func: typing.Callable) -> typing.Callable:
    func._inject = True
    return func


class LifeStyle:
    TRANSIENT = 'transient'
    SINGLETON = 'singleton'
    SCOPED = 'scoped'


class Scope:
    def __init__(self, container: "Container"):
        self.container = container
        self._scoped_instances: dict[tuple[typing.Type, str | None], typing.Any] = {}

    def resolve(self, interface: typing.Type, name: str | None = None) -> typing.Any:
        key = (interface, name)
        if key in self._scoped_instances:
            return self._scoped_instances[key]
        instance = self.container._resolve_in_scope(interface, self, name)
        return instance


class Container:
    def __init__(self):
        self._services: dict[tuple[typing.Type, str | None], dict[str, typing.Any]] = {}
        self._factories: dict[tuple[typing.Type, str | None], dict[str, typing.Any]] = {}
        self._singletons: dict[tuple[typing.Type, str | None], typing.Any] = {}
        self._resolving: set[typing.Type] = set()
    
    def register(self, interface: typing.Type, implementation: typing.Type | None = None, lifestyle: str = LifeStyle.TRANSIENT, name: str | None = None) -> None:
        if lifestyle not in (LifeStyle.TRANSIENT, LifeStyle.SINGLETON, LifeStyle.SCOPED):
            raise InvalidLifestyleException(lifestyle)
        if implementation is None:
            implementation = interface
        key = (interface, name)
        self._services[key] = {'implementation': implementation, 'lifestyle': lifestyle}

    
    def register_factory(self, interface: typing.Type, factory: typing.Callable[["Container"], typing.Any], lifestyle: str = LifeStyle.TRANSIENT, name: str | None = None) -> None:
        if not callable(factory):
            raise ValueError("Factory must be callable")
        if lifestyle not in (LifeStyle.TRANSIENT, LifeStyle.SINGLETON, LifeStyle.SCOPED):
            raise InvalidLifestyleException(lifestyle)
        key = (interface, name)
        self._factories[key] = {'factory': factory, 'lifestyle': lifestyle}

    def resolve(self, interface: typing.Type, name: str | None = None) -> typing.Any:
        key = (interface, name)
        if key in self._singletons:
            return self._singletons[key]

        if key in self._services or key in self._factories:
            scope = Scope(self)
            return self._resolve_in_scope(interface, scope, name)
        else:
            interface_name = f"{interface}"
            if name is not None:
                interface_name += f" with name '{name}'"
            raise ServiceNotRegisteredException(interface_name)
        
    def create_scope(self) -> Scope:
        return Scope(self)
        
    def _resolve_in_scope(self, interface: typing.Type, scope: Scope, name: str | None = None) -> typing.Any:
        key = (interface, name)
        if key in self._singletons:
            return self._singletons[key]

        if key in scope._scoped_instances:
            return scope._scoped_instances[key]

        if key in self._services:
            service = self._services[key]
            implementation = service['implementation']
            lifestyle = service['lifestyle']
            instance = self._create_instance(implementation, scope)
        elif key in self._factories:
            service = self._factories[key]
            factory = service['factory']
            lifestyle = service['lifestyle']
            instance = factory(self)
        else:
            raise ServiceNotRegisteredException(f"{interface} with name '{name}'")

        if lifestyle == LifeStyle.SINGLETON:
            self._singletons[key] = instance
        elif lifestyle == LifeStyle.SCOPED:
            scope._scoped_instances[key] = instance

        return instance
    
    def _inject_properties(self, instance: object, scope: Scope) -> None:
        for name in dir(instance):
            attr = getattr(instance, name)
            if callable(attr) and getattr(attr, '_inject', False):
                type_hints = typing.get_type_hints(attr)
                if 'return' in type_hints and type_hints['return'] != inspect.Parameter.empty:
                    dependency = scope.resolve(type_hints['return'])
                    setattr(instance, name, dependency)
    
    def _create_instance(self, cls: typing.Type, scope: Scope) -> typing.Any:
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

                    is_optional = False
                    origin = typing.get_origin(param_annotation)
                    if origin in (typing.Union, types.UnionType):
                        args_ = typing.get_args(param_annotation)
                        if type(None) in args_:
                            is_optional = True
                            non_none_args = [a for a in args_ if a is not type(None)]
                            if non_none_args:
                                param_annotation = non_none_args[0]
                            else:
                                param_annotation = typing.Any

                    if param_annotation == inspect.Parameter.empty:
                        raise MissingTypeAnnotationException(name, cls)

                    try:
                        dependency = scope.resolve(param_annotation)
                    except ServiceNotRegisteredException:
                        if is_optional:
                            dependency = None
                        else:
                            raise
                    args.append(dependency)
                instance = cls(*args)
            self._inject_properties(instance, scope)
            return instance
        finally:
            self._resolving.remove(cls)