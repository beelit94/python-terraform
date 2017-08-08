"""
This is a python module provide a wrapper of terraform command line tool
"""
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

dependencies = []
module_name = 'python-terraform'
short_description = 'This is a python module provide a wrapper ' \
                    'of terraform command line tool'

try:
    with open('DESCRIPTION.rst') as f:
        long_description = f.read()
except IOError:
    long_description = short_description


setup(
    name=module_name,
    version='0.9.0',
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
