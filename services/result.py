"""
Result pattern implementation for service-layer error handling.
Provides a type-safe way to handle success and failure cases.
"""
from typing import TypeVar, Generic, Optional, Callable, Union
from dataclasses import dataclass


T = TypeVar('T')  # Success type
E = TypeVar('E')  # Error type


@dataclass
class Result(Generic[T, E]):
    """
    Result type that represents either success or failure.
    
    This pattern allows explicit error handling without exceptions,
    making error cases visible in the type system.
    """
    _value: Optional[T] = None
    _error: Optional[E] = None
    _is_success: bool = False
    
    @staticmethod
    def success(value: T) -> 'Result[T, E]':
        """Create a successful result."""
        return Result(_value=value, _is_success=True)
    
    @staticmethod
    def failure(error: E) -> 'Result[T, E]':
        """Create a failed result."""
        return Result(_error=error, _is_success=False)
    
    def is_success(self) -> bool:
        """Check if the result is successful."""
        return self._is_success
    
    def is_failure(self) -> bool:
        """Check if the result is a failure."""
        return not self._is_success
    
    @property
    def value(self) -> T:
        """
        Get the success value.
        Raises ValueError if called on a failure result.
        """
        if not self._is_success:
            raise ValueError("Cannot get value from a failure result")
        return self._value
    
    @property
    def error(self) -> E:
        """
        Get the error value.
        Raises ValueError if called on a success result.
        """
        if self._is_success:
            raise ValueError("Cannot get error from a success result")
        return self._error
    
    def value_or(self, default: T) -> T:
        """Get the value or return a default if this is a failure."""
        return self._value if self._is_success else default
    
    def map(self, func: Callable[[T], 'U']) -> 'Result[U, E]':
        """
        Transform the success value if present.
        If this is a failure, return the failure unchanged.
        """
        if self._is_success:
            try:
                return Result.success(func(self._value))
            except Exception as e:
                return Result.failure(e)
        return Result.failure(self._error)
    
    def map_error(self, func: Callable[[E], 'F']) -> 'Result[T, F]':
        """
        Transform the error value if present.
        If this is a success, return the success unchanged.
        """
        if self._is_success:
            return Result.success(self._value)
        return Result.failure(func(self._error))
    
    def flat_map(self, func: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        """
        Chain operations that return Results.
        If this is a failure, return the failure unchanged.
        """
        if self._is_success:
            try:
                return func(self._value)
            except Exception as e:
                return Result.failure(e)
        return Result.failure(self._error)
    
    def __repr__(self) -> str:
        if self._is_success:
            return f"Success({self._value})"
        return f"Failure({self._error})"
    
    def __bool__(self) -> bool:
        """Allow using Result in boolean context."""
        return self._is_success


# Convenience type aliases
Success = Result.success
Failure = Result.failure
