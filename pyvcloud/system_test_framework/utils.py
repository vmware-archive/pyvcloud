# VMware vCloud Director Python SDK
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


def create_empty_vapp(client, vdc, name, description):
    """Helper method to create an empty vApp.

    :param pyvcloud.vcd.client.Client client: a client that would be used
        to make ReST calls to vCD.
    :param pyvcloud.vcd.vdc.VDC vdc: the vdc in which the vApp will be
        created.
    :param str name: name of the new vApp.
    :param str description: description of the new vApp.

    :return: href of the created vApp.

    :rtype: str
    """
    vapp_sparse_resouce = vdc.create_vapp(
        name=name, description=description, accept_all_eulas=True)

    client.get_task_monitor().wait_for_success(
        vapp_sparse_resouce.Tasks.Task[0])

    return vapp_sparse_resouce.get('href')


def create_vapp_from_template(client,
                              vdc,
                              name,
                              catalog_name,
                              template_name,
                              power_on=True,
                              deploy=True):
    """Helper method to create a vApp from template.

    :param pyvcloud.vcd.client.Client client: a client that would be used
        to make ReST calls to vCD.
    :param pyvcloud.vcd.vdc.VDC vdc: the vdc in which the vApp will be
        created.
    :param str name: name of the new vApp.
    :param str catalog_name: name of the catalog.
    :param str template_name: name of the vApp template.

    :return: href of the created vApp.

    :rtype: str
    """
    vapp_sparse_resouce = vdc.instantiate_vapp(
        name=name,
        catalog=catalog_name,
        template=template_name,
        accept_all_eulas=True,
        power_on=power_on,
        deploy=deploy)

    client.get_task_monitor().wait_for_success(
        vapp_sparse_resouce.Tasks.Task[0])

    return vapp_sparse_resouce.get('href')


def create_customized_vapp_from_template(client,
                                         vdc,
                                         name,
                                         catalog_name,
                                         template_name,
                                         description=None,
                                         memory_size=None,
                                         num_cpu=None,
                                         disk_size=None,
                                         vm_name=None,
                                         vm_hostname=None,
                                         nw_adapter_type=None):
    """Helper method to create a customized vApp from template.

    :param pyvcloud.vcd.client.Client client: a client that would be used
        to make ReST calls to vCD.
    :param pyvcloud.vcd.vdc.VDC vdc: the vdc in which the vApp will be
        created.
    :param str name: name of the new vApp.
    :param str catalog_name: name of the catalog.
    :param str template_name: name of the vApp template.
    :param str description: description of the new vApp.
    :param int memory_size: size of memory of the first vm.
    :param int num_cpu: number of cpus in the first vm.
    :param int disk_size: size of the first disk of the first vm.
    :param str vm_name: when provided, sets the name of the vm.
    :param str vm_hostname: when provided, sets the hostname of the guest OS.
    :param str nw_adapter_type: One of the values in
            pyvcloud.vcd.client.NetworkAdapterType.

    :return: href of the created vApp.

    :rtype: str
    """
    vapp_sparse_resouce = vdc.instantiate_vapp(
        name=name,
        catalog=catalog_name,
        template=template_name,
        description=description,
        deploy=True,
        power_on=True,
        accept_all_eulas=True,
        memory=memory_size,
        cpu=num_cpu,
        disk_size=disk_size,
        vm_name=vm_name,
        hostname=vm_hostname,
        network_adapter_type=nw_adapter_type)

    client.get_task_monitor().wait_for_success(
        vapp_sparse_resouce.Tasks.Task[0])

    return vapp_sparse_resouce.get('href')


def create_independent_disk(client, vdc, name, size, description):
    """Helper method to create an independent disk in a given orgVDC.

    :param pyvcloud.vcd.client.Client client: a client that would be used
        to make ReST calls to vCD.
    :param pyvcloud.vcd.vdc.VDC vdc: the vdc in which the disk will be
        created.
    :param str name: name of the disk to be created.
    :param str size: size of the disk to be created in bytes.
    :param str description: description of the disk to be created.

    :return: id of the created independent disk.

    :rtype: str
    """
    disk_sparse = vdc.create_disk(
        name=name, size=size, description=description)
    client.get_task_monitor().wait_for_success(disk_sparse.Tasks.Task[0])
    # clip 'urn:vcloud:disk:' from the id returned by vCD.
    return disk_sparse.get('id')[16:]
