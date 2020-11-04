from setuptools import setup
import os
import ee

ee.Initialize()

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

exec(read('eedswe/__version__.py'))

setup(
    name = 'eedswe',
    version = __version__,
    packages = ['eedswe',],
    license = 'MIT',
    long_description = read('README.md'),
    long_description_content_type='text/markdown',
    install_requires = [
        'earthengine_api',
        'httplib2shim'
        ],
    author = 'Ben DeVries',
    author_email = 'bdv@uoguelph.ca',
    url = 'https://github.com/bendv/eedswe'
)
