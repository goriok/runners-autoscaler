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
