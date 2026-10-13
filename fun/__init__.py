"""Fun: a small toolkit of entertaining yet somewhat useful utilities."""

__author__ = "Christopher Couch"
__license__ = "MIT"
__version__ = "0.2.0"

from fun.communications import communicator as et
from fun.printing.formatted_console_print import fancy_print

__all__ = ["et", "fancy_print", "__version__"]
