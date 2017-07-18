# vCloud Air CLI 10
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
# This product is licensed to you under the
# Apache License, Version 2.0 (the "License").
# You may not use this product except in compliance with the License.
# This product may include a number of subcomponents with
# separate copyright notices and license terms. Your use of the source
# code for the these subcomponents is subject to the terms and
# conditions of the subcomponent's license, as noted in the LICENSE file.
#

import pip
from pip.req import parse_requirements
from setuptools import find_packages
from setuptools import setup
requirements = [
    str(requirement.req)
    for requirement in parse_requirements('requirements.txt',
                                          session=pip.download.PipSession())
]

setup(
    name='vca-cli',
    version='18.0.1',
    description='VMware vCloud CLI',
    url='https://github.com/vmware/vca-cli',
    author='VMware, Inc.',
    author_email='pgomez@vmware.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    license='License :: OSI Approved :: Apache Software License',
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Distributed Computing',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
    ],
    keywords='pyvcloud vcloud vcloudair vmware cli',
    platforms=['Windows', 'Linux', 'Solaris', 'Mac OS-X', 'Unix'],
    test_suite='tests',
    tests_require=[],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'vca=vca_cli.vca_cli:cli',
            'vcd=vca_cli.vca_cli:cli',
        ],
    }
)
