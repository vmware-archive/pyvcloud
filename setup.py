from setuptools import setup, find_packages
from pip.req import parse_requirements


install_reqs = parse_requirements('requirements.txt')
required = [str(ir.req) for ir in install_reqs]


setup(
    name='vca-cli',
    version='20rc1',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/vmware/vca-cli',
    author='VMware, Inc.',
    author_email='pgomez@vmware.com',
    install_requires=required,
    entry_points='''
        [console_scripts]
        vca=vca_cli.vca_cli:cli
    '''
)