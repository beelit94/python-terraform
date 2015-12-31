"""
My Tool does one thing, and one thing well.
"""
from distutils.core import setup
import os

dependencies = []
module_name = 'terraform'


setup(
    name=module_name,
    version="0.0.1",
    url='https://github.com/beelit94/python-terraform',
    license='BSD',
    author='Freddy Tan',
    author_email='ftan@splunk.com',
    description='This is a python module provide a wrapper of terraform command line tool',
    long_description=__doc__,
    packages=[module_name],
    include_package_data=True,
    package_data={},
    zip_safe=False,
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
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Operating System :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
