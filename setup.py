from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.readlines()

setup(
    name='mee6',
    author='cookkkie',
    url='https://github.com/mee6/mee6',
    version='0.0.1',
    packages=find_packages(),
    license='MIT',
    description='',
    include_package_data=True,
    install_requires=requirements
)
