import io
import os

from setuptools import setup, find_packages, Command

# Package meta-data.
NAME = 'bitbucket-runner-autoscaler'
DESCRIPTION = 'Autoscale Bitbucket Pipelines runners using Kubernetes'
URL = 'https://bitbucket.org/bitbucketpipelines/runners-autoscaler'
EMAIL = 'pipelines-feedback@atlassian.com'
AUTHOR = 'Bitbucket Pipelines'
REQUIRES_PYTHON = '>=3.7.0'
VERSION = None

with open('requirements.txt') as fp:
    install_reqs = fp.read()

here = os.path.abspath(os.path.dirname(__file__))

readme = DESCRIPTION

with io.open(os.path.join(here, "README.md"), "rt", encoding="utf8") as f:
    readme = f.read()

with io.open(os.path.join(here, "CHANGELOG.md"), "rt", encoding="utf8") as f:
    changelog = f.read()

# Load the package's __version__.py module as a dictionary.
if not VERSION:
    with open(os.path.join(here, 'autoscaler', '__version__.py')) as f:
        about = {}
        exec(f.read(), about)
        VERSION = about['__version__']


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('rm -vrf ./build ./dist ./*.pyc ./*.egg-info')


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=u"\n\n".join([readme, changelog]),
    long_description_content_type='text/markdown',
    tests_require=['pytest'],
    url=URL,
    author=AUTHOR,
    author_email=EMAIL,
    license='MIT',
    packages=find_packages(exclude=('tests',)),
    python_requires=REQUIRES_PYTHON,

    entry_points={
        'console_scripts': [
            'bitbucket-runner-autoscaler = autoscaler.cli:main'
        ]
    },

    install_requires=install_reqs,

    classifiers=[
        'Development Status :: 4 - Beta',

        'Environment :: Console',

        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: OS Independent',
    ],

    cmdclass={
        'clean': CleanCommand,
    }
)
