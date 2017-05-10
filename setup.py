from setuptools import setup, find_packages
from mee6 import VERSION

with open('requirements.txt') as f:
    requirements = f.readlines()

setup(
    name='mee6',
    author='cookkkie',
    url='https://github.com/mee6/mee6',
    version=VERSION,
    packages=find_packages(),
    license='MIT',
    description='',
    include_package_data=True,
    install_requires=requirements
)
