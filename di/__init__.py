import inspect
import types
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)


class DIException(Exception):
    """Base exception class for dependency injection errors."""


class ServiceNotRegisteredException(DIException):
    def __init__(self, interface_description: str):
        super().__init__(
            f"Service for interface '{interface_description}' is not registered."
        )


class CyclicDependencyException(DIException):
    def __init__(self, cls: Type):
        super().__init__(f"Cyclic dependency detected: {cls}.")


class MissingTypeAnnotationException(DIException):
    def __init__(self, param_name: str, cls: Type):
        super().__init__(
            f"Missing type annotation for parameter '{param_name}' in class '{cls.__name__}'."
        )


class InvalidLifestyleException(DIException):
    def __init__(self, lifestyle: str):
        super().__init__(
            f"Invalid lifestyle '{lifestyle}'. Valid options are 'transient' or 'singleton'."
        )


def inject(func: Callable) -> Callable:
    func.__annotations__["_inject"] = True
    return func


def is_injectable(func: Callable) -> bool:
    return hasattr(func, "__annotations__") and func.__annotations__.get(
        "_inject", False
    )


class LifeStyle:
    TRANSIENT = "transient"
    SINGLETON = "singleton"
    SCOPED = "scoped"


class Scope:
    __slots__ = ("container", "_scoped_instances")

    def __init__(self, container: "Container"):
        self.container = container
        self._scoped_instances: Dict[Tuple[Type, Optional[str]], Any] = {}

    def resolve(self, interface: Type, name: Optional[str] = None) -> Any:
        key = (interface, name)
        if key in self._scoped_instances:
            return self._scoped_instances[key]
        instance = self.container._resolve_in_scope(interface, self, name)
        return instance


class Container:
    __slots__ = (
        "_services",
        "_factories",
        "_singletons",
        "_resolving",
    )

    def __init__(self):
        self._services: Dict[Tuple[Type, Optional[str]], Dict[str, Any]] = {}
        self._factories: Dict[Tuple[Type, Optional[str]], Dict[str, Any]] = {}
        self._singletons: Dict[Tuple[Type, Optional[str]], Any] = {}
        self._resolving: Set[Type] = set()

    def register(
        self,
        interface: Type,
        implementation: Optional[Type] = None,
        lifestyle: str = LifeStyle.TRANSIENT,
        name: Optional[str] = None,
    ) -> None:
        if lifestyle not in (
            LifeStyle.TRANSIENT,
            LifeStyle.SINGLETON,
            LifeStyle.SCOPED,
        ):
            raise InvalidLifestyleException(lifestyle)
        if implementation is None:
            implementation = interface
        key = (interface, name)
        self._services[key] = {"implementation": implementation, "lifestyle": lifestyle}

    def register_factory(
        self,
        interface: Type,
        factory: Callable[..., Any],
        lifestyle: str = LifeStyle.TRANSIENT,
        name: Optional[str] = None,
    ) -> None:
        if not callable(factory):
            raise ValueError("Factory must be callable")
        if lifestyle not in (
            LifeStyle.TRANSIENT,
            LifeStyle.SINGLETON,
            LifeStyle.SCOPED,
        ):
            raise InvalidLifestyleException(lifestyle)
        key = (interface, name)
        self._factories[key] = {"factory": factory, "lifestyle": lifestyle}

    def resolve(self, interface: Type, name: Optional[str] = None) -> Any:
        key = (interface, name)
        if key in self._singletons:
            return self._singletons[key]

        if key in self._services or key in self._factories:
            scope = self.create_scope()
            return self._resolve_in_scope(interface, scope, name)
        else:
            interface_name = f"{interface}"
            if name is not None:
                interface_name += f" with name '{name}'"
            raise ServiceNotRegisteredException(interface_name)

    def create_scope(self) -> Scope:
        return Scope(self)

    def add_singleton(
        self,
        interface: Type,
        implementation: Optional[Type] = None,
        name: Optional[str] = None,
    ) -> None:
        self.register(
            interface, implementation, lifestyle=LifeStyle.SINGLETON, name=name
        )

    def add_transient(
        self,
        interface: Type,
        implementation: Optional[Type] = None,
        name: Optional[str] = None,
    ) -> None:
        self.register(
            interface, implementation, lifestyle=LifeStyle.TRANSIENT, name=name
        )

    def add_scoped(
        self,
        interface: Type,
        implementation: Optional[Type] = None,
        name: Optional[str] = None,
    ) -> None:
        self.register(interface, implementation, lifestyle=LifeStyle.SCOPED, name=name)

    def add_singleton_factory(
        self,
        interface: Type,
        factory: Callable[..., Any],
        name: Optional[str] = None,
    ) -> None:
        self.register_factory(
            interface, factory, lifestyle=LifeStyle.SINGLETON, name=name
        )

    def add_transient_factory(
        self,
        interface: Type,
        factory: Callable[..., Any],
        name: Optional[str] = None,
    ) -> None:
        self.register_factory(
            interface, factory, lifestyle=LifeStyle.TRANSIENT, name=name
        )

    def add_scoped_factory(
        self,
        interface: Type,
        factory: Callable[..., Any],
        name: Optional[str] = None,
    ) -> None:
        self.register_factory(interface, factory, lifestyle=LifeStyle.SCOPED, name=name)

    def add_instance(
        self, interface: Type, instance: Any, name: Optional[str] = None
    ) -> None:
        key = (interface, name)
        self._singletons[key] = instance

    def _resolve_in_scope(
        self, interface: Type, scope: Scope, name: Optional[str] = None
    ) -> Any:
        key = (interface, name)
        if key in self._singletons:
            return self._singletons[key]

        if key in scope._scoped_instances:
            return scope._scoped_instances[key]

        if key in self._services:
            service = self._services[key]
            implementation = service["implementation"]
            lifestyle = service["lifestyle"]
            instance = self._create_instance(implementation, scope)
        elif key in self._factories:
            service = self._factories[key]
            factory = service["factory"]
            lifestyle = service["lifestyle"]
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
            if callable(attr) and is_injectable(attr):
                type_hints = get_type_hints(attr)
                if (
                    "return" in type_hints
                    and type_hints["return"] != inspect.Parameter.empty
                ):
                    dependency_type = type_hints["return"]
                    dependency = scope.resolve(dependency_type)
                    setattr(instance, name, dependency)

    def _create_instance(self, cls: Type, scope: Scope) -> Any:
        if cls in self._resolving:
            raise CyclicDependencyException(cls)

        self._resolving.add(cls)
        try:
            constructor = cls.__init__
            if constructor is object.__init__:
                instance = cls()
            else:
                type_hints = get_type_hints(constructor)
                params = inspect.signature(constructor).parameters
                args = []
                for name, param in params.items():
                    if name == "self":
                        continue
                    param_annotation = type_hints.get(name, param.annotation)

                    is_optional = False
                    origin = get_origin(param_annotation)
                    if origin in (Union, types.UnionType):
                        args_ = get_args(param_annotation)
                        if type(None) in args_:
                            is_optional = True
                            non_none_args = [a for a in args_ if a is not type(None)]
                            if non_none_args:
                                param_annotation = non_none_args[0]
                            else:
                                param_annotation = Any

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
