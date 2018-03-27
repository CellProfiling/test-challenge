"""Set up techdevprojects."""
from setuptools import find_packages, setup

GITHUB_URL = 'https://github.com/CellProfiling/test-challenge'
DOWNLOAD_URL = '{}/archive/master.zip'.format(GITHUB_URL)
CLASSIFIERS = [
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 3 - Alpha',

    # Indicate who your project is intended for
    'Intended Audience :: Science/Research',
    'Topic :: Scientific/Engineering',

    # Pick your license as you wish (should match "license" above)
    'License :: OSI Approved :: MIT License',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
]

CONFIG = {
    'description': 'Create an image analysis challenge.',
    'author': 'Cell Profiling',
    'url': GITHUB_URL,
    'download_url': DOWNLOAD_URL,
    'license': 'MIT',
    'author_email': 'cell.profiling@scilifelab.se',
    'version': '0.1.0',
    'install_requires': [
        'Click',
        'numpy',
        'pandas',
    ],
    'packages': find_packages(exclude=['contrib', 'docs', 'tests*']),
    'include_package_data': True,
    'entry_points': {
        'console_scripts': ['testchallenge = testchallenge.__main__:main']},
    'name': 'testchallenge',
    'zip_safe': False,
    'classifiers': CLASSIFIERS,
}

setup(**CONFIG)
