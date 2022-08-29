from setuptools import setup, find_packages
from src.nox_comb.version import __version__

setup(
    name='nox_comb',
    version=__version__,
    description='Command line helper for combining all linters output files into one.',
    author='Sam',
    author_email='sbriley.0@gmail.com',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'nox',
    ],
    entry_points={
        'console_scripts': [
            'nox_comb=lint_capture.main:main',
        ]
    },
)
