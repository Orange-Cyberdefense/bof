"""Set of global and useful classes and functions used within the module.

:Exceptions: BOF-specific exceptions raised by the module.
:String manipulation: Functions to make basic changes on strings.
"""

from datetime import datetime
from re import sub

###############################################################################
# BOF EXCEPTIONS                                                              #
###############################################################################

class BOFError(Exception):
    """Base class for all BOF exceptions.

    .. warning:: Should not be used directly, please raise or catch subclasses
                 instead.
    """

class BOFLibraryError(BOFError):
    """Library, files and import-related exceptions.

    Raise when the library cannot find what it needs to work correctly
    (such as an external module or a file).
    """ 
    pass

class BOFNetworkError(BOFError):
    """Network-related exceptions.

    Raise when the network connection fails or is interrupted.
    """
    pass

class BOFProgrammingError(BOFError):
    """Script and module programming-related errors.

    Raise when a function or an argument is not used as expected.

    .. note:: As a module user, this exception is the most frequent one.
    """ 
    pass

class BOFDeviceError(BOFError):
    """Exceptions related to errors returned by the device.

    Raise when the device responds with an error code, but the network
    connection is still fine.
    """
    pass

###############################################################################
# STRING MANIPULATION                                                         #
###############################################################################

def to_property(value: str) -> str:
    """Lower a string and replace all non alnum characters with ``_``"""
    if isinstance(value, str):
        return sub('[^0-9a-zA-Z]+', '_', value.lower().strip())
    return value
