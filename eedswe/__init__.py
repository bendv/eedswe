from .dswe import dswe, cdswe
from .__version__ import __version__
import ee
ee.Initialize()
del ee

__all__ = ['dswe', 'cdswe']
