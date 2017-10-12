try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('VERSION.txt', 'r') as v:
    version = v.read().strip()

with open('REQUIREMENTS.txt', 'r') as r:
    requires = r.read().split()

with open('README.rst', 'r') as r:
    readme = r.read()

download_url = (
    'https://github.com/duccioa/SeLoger/tarball/%s'
)

setup(
    name='python-seloger',
    packages=['SeLoger'],
    version=version,
    description=('Simple SeLoger.com wrapper.'),
    long_description=readme,
    author='Duccio Aiazzi',
    author_email='duccio.aiazzi@gmail.com',
    url='https://github.com/duccioa/SeLoger',
    download_url=download_url % version,
    install_requires=requires,
    license='MIT-Zero'
)
