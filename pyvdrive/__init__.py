# type: ignore
"""
Mantid PyVDRive
===============

A PyQt-based version of VDrive program based
on Mantid (http://www.mantidproject.org).
"""
__description__ = "Reduction software for VULCAN"
__url__ = 'https://github.com/neutrons/PyVDrive'

__author__ = 'W.Zhou'
__email__ = 'zhouw@ornl.gov'

__license__ = 'GNU GENERAL PUBLIC LICENSE'

from ._version import get_versions  # noqa: E402
__version__ = get_versions()['version']
del get_versions
