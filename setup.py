from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='vca-cli',
    version='20rc1',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/vmware/pyvcloud',
    author='VMware, Inc.',
    author_email='pgomez@vmware.com',
    install_requires=required,
    entry_points='''
        [console_scripts]
        vca=vca_cli.vca_cli:cli
    '''
)