from setuptools import setup, find_packages

setup(
    name='vca-cli',
    version='20',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        vca=vca_cli.vca_cli:cli
    ''',
)