![Build Status](https://github.com/vshulcz/di/actions/workflows/ci.yml/badge.svg)
![Python Versions](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue)
![License](https://img.shields.io/github/license/vshulcz/di.svg)


# DI Container for Python

Injex is a lightweight and easy-to-use DI container for Python applications. This library aims to simplify the management of dependencies in your projects, making your code more modular, testable, and maintainable. This library inspired by popular DI frameworks in other programming languages.


## Features

* 🌟 Simple API: Easy to understand and use.
* 🔄 Support for singleton, transient, and scoped services.
* Register multiple implementations of the same interface using names.
* 🔍 Inject dependencies into properties after object creation.
* 🛠 Handle optional dependencies gracefully.


## Why Use Dependency Injection?

**Dependency Injection is a design pattern that helps in:**

* Modularity: Breaking down your application into interchangeable components.
* Testability: Facilitating unit testing by allowing dependencies to be mocked or stubbed.
* Maintainability: Making it easier to update, replace, or refactor components without affecting other parts of the application.
* Flexibility: Configuring different implementations of the same interface for various scenarios (e.g., testing, production).

## Quick Start

Here's a simple example of usage Injex:
```python
from abc import ABC, abstractmethod
from injex import Container

class IService(ABC):
    @abstractmethod
    def perform_action(self):
        pass

class ServiceImplementation(IService):
    def perform_action(self):
        print("Service is performing an action.")

container = Container()

container.add_transient(IService, ServiceImplementation)

service = container.resolve(IService)
service.perform_action() # output: Service is performing an action.
```
Another examples in [examples folder](./examples).