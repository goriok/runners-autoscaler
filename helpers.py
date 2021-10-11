import os
import sys
import base64

from colorama import Fore, Style

from logger import logger


def get_variable(name, required=False, default=None):
    """Fetch the value of a pipe variable.

    Args:
        name (str): Variable name.
        required (bool, optional): Throw an exception if the env var is unset.
        default (:obj:`str`, optional): Default value if the env var is unset.

    Returns:
        Value of the variable

    Raises
        Exception: If a required variable is missing.
    """
    value = os.getenv(name)
    if required and (value is None or not value.strip()):
        raise Exception(f'{name} variable missing.')
    return value if value else default


def required(name):
    """Get the value of a required pipe variable.

    This function is basically an alias to get_variable with the required
        parameter set to True.

    Args:
        name (str): Variable name.

    Returns:
        Value of the variable

    Raises
        Exception: If a required variable is missing.
    """
    return get_variable(name, required=True)


def success(message='Success', do_exit=True):
    """Prints the colorized success message (in green)

    Args:
        message (str, optional): Output message
        do_exit (bool, optional): Call sys.exit if set to True

    """
    print('{}✔ {}{}'.format(Fore.GREEN, message, Style.RESET_ALL), flush=True)

    if do_exit:
        sys.exit(0)


def fail(message='Fail!', do_exit=True):
    """Prints the colorized failure message (in red)

    Args:
        message (str, optional): Output message
        do_exit (bool, optional): Call sys.exit if set to True

    """
    print('{}✖ {}{}'.format(Fore.RED, message, Style.RESET_ALL))

    if do_exit:
        sys.exit(1)


def enable_debug():  # pragma: no cover
    """Enable the debug log level."""

    debug = get_variable('DEBUG', required=False, default="False").lower()
    if debug == 'true':
        logger.info('Enabling debug mode.')
        logger.setLevel('DEBUG')


def string_to_base64string(string, encoding='utf-8'):
    return base64.b64encode(bytes(string, encoding)).decode(encoding)
