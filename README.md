# Injex - DI Container for Python

![Build Status](https://github.com/vshulcz/di/actions/workflows/ci.yml/badge.svg)
[![pypi](https://img.shields.io/pypi/v/injex.svg)](https://pypi.python.org/pypi/injex)
[![Python Versions](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue)](https://github.com/vshulcz/injex)
[![License](https://img.shields.io/github/license/vshulcz/di.svg)](https://github.com/vshulcz/injex/LICENSE)

Injex is a lightweight and easy-to-use Dependency Injection (DI) container for Python applications. It simplifies dependency management, making your code more modular, testable, and maintainable. Injex is inspired by popular DI frameworks in other programming languages and brings similar capabilities to Python.

## Features

🌟 Simple API: Easy to understand and use.
🔄 Multiple Lifestyles: Support for singleton, transient, and scoped services.
🧩 Flexible Registrations: Register services, factories, and instances.
🏷️ Named Registrations: Register multiple implementations of the same interface using names.
🔍 Property Injection: Inject dependencies into properties after object creation.
🛠 Optional Dependencies: Handle optional dependencies gracefully.
🚀 No External Dependencies: Pure Python implementation without third-party packages.

## Installation

```bash
pip install injex
```

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

## Documentation

For detailed documentation on all functionalities, usage examples, and best practices, please refer to the [Documentation](./docs/tutorial.md).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.
