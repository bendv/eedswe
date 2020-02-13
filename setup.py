from setuptools import setup
import os
import ee

ee.Initialize()

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'eedswe',
    version = '0.0.1',
    packages = ['eedswe',],
    license = 'MIT',
    long_description = read('README.md'),
    long_description_content_type='text/markdown',
    install_requires = [
        'earthengine_api'
        ],
    author = 'Ben DeVries',
    author_email = 'bdv@uoguelph.ca',
    url = 'https://github.com/bendv/eedswe'
)
