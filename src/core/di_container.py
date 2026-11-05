"""
Dependency Injection Container for the multi-agent system.

Provides a centralized registry for system components to enable:
- Testability through component mocking
- Loose coupling between modules
- Lifecycle management
- Configuration injection
"""

from typing import Dict, Any, Optional, Type, TypeVar, Callable, Tuple, cast
from contextlib import contextmanager
import threading
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DIContainer:
    """
    Dependency Injection Container for managing system components.

    This container manages the lifecycle of components and provides:
    - Registration of components and factories
    - Resolution of dependencies
    - Scoped lifetime management
    - Thread-safe operations
    """

    def __init__(self):
        self._registrations: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Tuple[Callable[[], Any], bool]] = {}
        self._lock = threading.RLock()

    def register_instance(self, name: str, instance: Any) -> None:
        """
        Register a pre-created instance as a singleton.

        Args:
            name: Unique identifier for the component
            instance: The instance to register
        """
        with self._lock:
            self._singletons[name] = instance
            logger.debug(f"Registered instance: {name}")

    def register_factory(
        self, name: str, factory: Callable[[], T], singleton: bool = False
    ) -> None:
        """
        Register a factory function for creating components.

        Args:
            name: Unique identifier for the component
            factory: Function that creates the component
            singleton: If True, factory is called once and result cached
        """
        with self._lock:
            self._factories[name] = (factory, singleton)
            logger.debug(f"Registered factory: {name} (singleton={singleton})")

    def register_class(
        self, name: str, cls: Type[T], singleton: bool = False, **kwargs
    ) -> None:
        """
        Register a class for instantiation.

        Args:
            name: Unique identifier for the component
            cls: The class to instantiate
            singleton: If True, only one instance is created
            **kwargs: Constructor arguments
        """

        def factory():
            return cls(**kwargs)

        self.register_factory(name, factory, singleton)

    def resolve(self, name: str) -> Any:
        """
        Resolve a component by name.

        Args:
            name: Component identifier

        Returns:
            The resolved component

        Raises:
            KeyError: If component not found
        """
        with self._lock:
            # Check for existing singleton
            if name in self._singletons:
                return self._singletons[name]

            # Check for factory
            if name in self._factories:
                factory_entry = self._factories[name]
                factory = factory_entry[0]
                is_singleton = factory_entry[1]
                instance = factory()

                if is_singleton:
                    self._singletons[name] = instance

                return instance

            raise KeyError(f"Component not found: {name}")

    def resolve_or_default(self, name: str, default: T) -> T:
        """
        Resolve a component or return default if not found.

        Args:
            name: Component identifier
            default: Default value if component not found

        Returns:
            The resolved component or default
        """
        try:
            return self.resolve(name)
        except KeyError:
            return default

    def is_registered(self, name: str) -> bool:
        """Check if a component is registered."""
        with self._lock:
            return name in self._singletons or name in self._factories

    def unregister(self, name: str) -> None:
        """
        Unregister a component.

        Args:
            name: Component identifier to remove
        """
        with self._lock:
            self._singletons.pop(name, None)
            self._factories.pop(name, None)
            logger.debug(f"Unregistered: {name}")

    def clear(self) -> None:
        """Clear all registrations."""
        with self._lock:
            self._singletons.clear()
            self._factories.clear()
            logger.debug("Cleared all registrations")

    @contextmanager
    def scope(self):
        """
        Create a scoped container for isolated testing.

        Yields:
            DIContainer: A child container with inherited registrations
        """
        child = DIContainer()
        with self._lock:
            child._singletons = self._singletons.copy()
            child._factories = self._factories.copy()

        try:
            yield child
        finally:
            child.clear()


# Global container instance
_global_container: Optional[DIContainer] = None
_container_lock = threading.Lock()


def get_container() -> DIContainer:
    """
    Get the global DI container.

    Returns:
        The global DIContainer instance
    """
    global _global_container

    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = DIContainer()

    return _global_container


def reset_container() -> None:
    """Reset the global container - useful for testing."""
    global _global_container

    with _container_lock:
        if _global_container is not None:
            _global_container.clear()
            _global_container = None


# Convenience functions for common operations
def register_component(name: str, instance: Any) -> None:
    """Register a component in the global container."""
    get_container().register_instance(name, instance)


def resolve_component(name: str) -> Any:
    """Resolve a component from the global container."""
    return get_container().resolve(name)


def resolve_component_or_default(name: str, default: T) -> T:
    """Resolve a component or return default."""
    return get_container().resolve_or_default(name, default)
