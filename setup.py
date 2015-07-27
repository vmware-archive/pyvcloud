from setuptools import setup, find_packages
import pip
from pip.req import parse_requirements
requirements = [
    str(requirement.req)
    for requirement in parse_requirements('requirements.txt', session=pip.download.PipSession())
]

setup(
    name='vca-cli',
    version='14rc1',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/vmware/vca-cli',
    author='VMware, Inc.',
    author_email='pgomez@vmware.com',
    install_requires=requirements,
    entry_points='''
        [console_scripts]
        vca=vca_cli.vca_cli:cli
    '''
)