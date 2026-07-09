class PineRouteException(Exception):
    """Base exception for PineRoute."""
    pass

class ExchangeConnectionError(PineRouteException):
    """Raised when there is an issue connecting to the exchange."""
    pass

class OrderExecutionError(PineRouteException):
    """Raised when an order fails to execute on the exchange."""
    pass

class InvalidSignalError(PineRouteException):
    """Raised when the received signal is invalid or malformed."""
    pass
