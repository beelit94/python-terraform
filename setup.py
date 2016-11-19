"""
This is a python module provide a wrapper of terraform command line tool
"""
from setuptools import setup
import os

dependencies = []
module_name = 'python-terraform'
short_description = 'This is a python module provide a wrapper ' \
                    'of terraform command line tool'

try:
    with open('DESCRIPTION.rst') as f:
        long_description = f.read()
except IOError:
    long_description = short_description


def get_version():
    p = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "VERSION")
    with open(p) as f:
        version = f.read()
        version = version.strip()
        if not version:
            raise ValueError("could not read version")
        return version

setup(
    name=module_name,
    version=get_version(),
    url='https://github.com/beelit94/python-terraform',
    license='MIT',
    author='Freddy Tan',
    author_email='beelit94@gmail.com',
    description=short_description,
    long_description=long_description,
    packages=['python_terraform'],
    package_data={},
    platforms='any',
    install_requires=dependencies,
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        # 'Operating System :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
