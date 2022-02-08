"""Exceptions module for various exceptions."""


class AutoscalerException(Exception):
    """Base class for all AutoScaler exceptions."""
    pass


class AutoscalerHTTPError(AutoscalerException):
    status_code = 500

    def __init__(self, message, status_code=None):
        self.status_code = status_code or self.status_code
        super().__init__(f'Status code: {self.status_code}. {message}')


class NotAuthorized(AutoscalerHTTPError):
    status_code = 401


class KubernetesError(Exception):
    """Base class for all Kubernetes exceptions."""
    pass


class KubernetesNamespaceError(KubernetesError):
    """Base class for all Kubernetes namespace exceptions."""
    pass


class CannotCreateNamespaceError(KubernetesNamespaceError):
    """Raised when cannot create namespace."""
    pass


class NamespaceNotFoundError(KubernetesNamespaceError):
    """Raised when namespace not found."""
    pass
