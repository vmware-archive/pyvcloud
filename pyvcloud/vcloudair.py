# VMware vCloud Python SDK
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
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

# coding: utf-8

#todo: upload/download ovf to/from catalog
#todo: create vapp network name is not being used, clean it up
#todo: pass parameters in the create vapp to optimize for speed, available from 6.3
#todo: refactor returns, raise exceptions, document with release notes

import time
import requests
from StringIO import StringIO
import json
from xml.etree import ElementTree as ET
from pyvcloud.schema.vcd.v1_5.schemas.admin import vCloudEntities
from pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities import AdminCatalogType
from pyvcloud.schema.vcd.v1_5.schemas.vcloud import sessionType, organizationType, \
    vAppType, organizationListType, vdcType, catalogType, queryRecordViewType, \
    networkType, vcloudType, taskType, diskType, vmsType, vdcTemplateListType, mediaType
from schema.vcd.v1_5.schemas.vcloud.diskType import OwnerType, DiskType, VdcStorageProfileType, DiskCreateParamsType
from pyvcloud.vcloudsession import VCS
from pyvcloud.vapp import VAPP
from pyvcloud.gateway import Gateway
from pyvcloud.schema.vcim import serviceType, vchsType
from pyvcloud.helper import CommonUtils
from pyvcloud.schema.vcd.v1_5.schemas.vcloud.networkType import OrgVdcNetworkType,\
    ReferenceType, NetworkConfigurationType, IpScopesType, IpScopeType,\
    IpRangesType, IpRangeType, DhcpPoolServiceType
from pyvcloud.score import Score
from pyvcloud import _get_logger, Http, Log

VCA_SERVICE_TYPE_ONDEMAND = 'ondemand'
VCA_SERVICE_TYPE_SUBSCRIPTION = 'subscription'
VCA_SERVICE_TYPE_STANDALONE = 'standalone'

class VCA(object):

    def __init__(self, host, username, service_type=VCA_SERVICE_TYPE_ONDEMAND, version='5.7', verify=True, log=False):
        """
        Create a VCA connection

        :param host: (str): The vCloud Air Host. Varies by service type. 
                            Valid values are https://vchs.vmware.com and https://iam.vchs.vmware.com
        :param username: (str): The username for the vCloud Air Service. 
        :param service_type: (str, optional): The type of vCloud Air Service. Valid values are ondemand, subscription, vcd.
        :param version: (str, optional): The API version. Note: may vary by service type.
        :verify: (bool, optional): Enforce strict ssl certificate checking.
        :log: (bool, optional): enable logging for the connection.
        :return: (bool): True if the user was successfully logged in, False otherwise.
        
        **service type:**  subscription, ondemand, vcd
        """
        if not (host.startswith('https://') or host.startswith('http://')):
            host = 'https://' + host
        self.host = host
        self.username = username
        self.token = None
        self.service_type = service_type
        self.version = version
        self.verify = verify
        self.vcloud_session = None
        self.instances = None
        self.org = None
        self.organization = None
        self.vdc = None
        self.services = None
        self.response =  None
        self.log = log
        self.logger = _get_logger() if log else None

    def _get_services(self):
        headers = {}
        headers["x-vchs-authorization"] = self.token
        headers["Accept"] = "application/xml;version=" + self.version
        response = Http.get(self.host + "/api/vchs/services", headers=headers, verify=self.verify, logger=self.logger)
        if response.status_code == requests.codes.ok:
            return serviceType.parseString(response.content, True)

    def login(self, password=None, token=None, org=None, org_url=None):
        """
        Request to login to vCloud Air

        :param password: (str, optional): The password.
        :param token: (str, optional): The token from a previous successful login, None if this is a new login request.
        :param org: (str, optional): The organization identifier.
        :param org_url: (str, optional): The org_url.
        :return: (bool): True if the user was successfully logged in, False otherwise.
        
        **service type:**  subscription, ondemand, vcd

        """

        if self.service_type == VCA_SERVICE_TYPE_SUBSCRIPTION:
            if token:
                headers = {}
                headers["x-vchs-authorization"] = token
                headers["Accept"] = "application/xml;version=" + self.version
                self.response = Http.get(self.host + "/api/vchs/services", headers=headers, verify=self.verify, logger=self.logger)
                if self.response.status_code == requests.codes.ok:
                    self.services = serviceType.parseString(self.response.content, True)
                    self.token = token
                    return True
                else:
                    return False
            else:
                url = self.host + "/api/vchs/sessions"
                headers = {}
                headers["Accept"] = "application/xml;version=" + self.version
                self.response = Http.post(url, headers=headers, auth=(self.username, password), verify=self.verify, logger=self.logger)
                if self.response.status_code == requests.codes.created:
                    self.token = self.response.headers["x-vchs-authorization"]
                    self.services = self._get_services()
                    return True
                else:
                    return False
        elif self.service_type == VCA_SERVICE_TYPE_ONDEMAND:
            if token:
                self.token = token
                self.instances = self.get_instances()
                return self.instances != None
            else:
                url = self.host + "/api/iam/login"
                headers = {}
                headers["Accept"] = "application/json;version=%s" % self.version
                self.response = Http.post(url, headers=headers, auth=(self.username, password), verify=self.verify, logger=self.logger)
                if self.response.status_code == requests.codes.created:
                    self.token = self.response.headers["vchs-authorization"]
                    self.instances = self.get_instances()
                    return True
                else:
                    return False
        elif self.service_type == VCA_SERVICE_TYPE_STANDALONE or self.service_type == 'vcd':
            if token:
                url = self.host + '/api/sessions'
                vcloud_session = VCS(url, self.username, org, None, org_url, org_url, version=self.version, verify=self.verify, log=self.log)
                result = vcloud_session.login(token=token)
                if result:
                    self.org = org
                    self.vcloud_session = vcloud_session
                return result
            else:
                url = self.host + '/api/sessions'
                vcloud_session = VCS(url, self.username, org, None, org_url, org_url, version=self.version, verify=self.verify, log=self.log)
                result = vcloud_session.login(password=password)
                if result:
                    self.token = vcloud_session.token
                    self.org = org
                    self.vcloud_session = vcloud_session
                return result
        else:
            return False
        return False

    #ondemand
    def get_plans(self):
        """
        Request available plans available for an ondemand account. 

        :return: (list of str): list of available plans in json format.
        
        **service type:**  ondemand

        """

        headers = self._get_vcloud_headers()
        headers['Accept'] = "application/json;version=%s;class=com.vmware.vchs.sc.restapi.model.planlisttype" % self.version
        self.response = Http.get(self.host + "/api/sc/plans", headers=headers, verify=self.verify, logger=self.logger)
        if self.response.history and self.response.history[-1]:
            self.response = Http.get(self.response.history[-1].headers['location'], headers=headers, verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            return json.loads(self.response.content)['plans']
        else:
            return None

    def get_instances(self):
        """
        Request available instances 

        :return: (list of str): list of available instances in json format.
        
        **service type:**  ondemand

        """
        self.response = Http.get(self.host + "/api/sc/instances", headers=self._get_vcloud_headers(), verify=self.verify, logger=self.logger)
        if self.response.history and self.response.history[-1]:
            self.response = Http.get(self.response.history[-1].headers['location'], headers=self._get_vcloud_headers(), verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            return json.loads(self.response.content)['instances']
        else:
            return None

    def delete_instance(self, instance):
        """
        Request to delete an existing instance 

        :param instance: (str): The instance identifer.
        :return: (): True if the user was successfully logged in, False otherwise.
       
        **service type:**  ondemand
       
        """
        self.response = Http.delete(self.host + "/api/sc/instances/" + instance, headers=self._get_vcloud_headers(), verify=self.verify, logger=self.logger)
        print self.response.status_code, self.response.content

    def login_to_instance(self, instance, password, token=None, org_url=None):
        """
        Request to login into a specific instance 

        :param instance: (str): The instance identifer.
        :param password: (str): The password.
        :param token: (str, optional): The token from a previous successful login, None if this is a new login request.
        :param org_url: (str, optional): 
        :return: (bool): True if the login was successful, False otherwise.

        **service type:**  ondemand
        
        """
        instances = filter(lambda i: i['id']==instance, self.instances)
        if len(instances)>0:
            if 'No Attributes' == instances[0]['instanceAttributes']:
                return False
            attributes = json.loads(instances[0]['instanceAttributes'])
            session_uri = attributes['sessionUri']
            org_name = attributes['orgName']
            vcloud_session = VCS(session_uri, self.username, org_name, instance, instances[0]['apiUrl'], org_url, version=self.version, verify=self.verify, log=self.log)
            result = vcloud_session.login(password, token)
            if result:
                self.vcloud_session = vcloud_session
                return True
        return False

    #subscription
    def get_vdc_references(self, serviceId):
        """
        Request a list of references to existing virtual data centers.

        :param serviceId: (str): The service instance identifier.
        :return: (list of ReferenceType): a list of :class:`<pyvcloud.schema.vcim.vchsType.VdcReferenceType` objects for the vdcs hosting the service.
       
        **service type:**  subscription

        """
        serviceReferences = filter(lambda serviceReference: serviceReference.get_serviceId() == serviceId, self.services.get_Service())
        if len(serviceReferences) == 0:
            return []
        self.response = Http.get(serviceReferences[0].get_href(), headers=self._get_vcloud_headers(), verify=self.verify, logger=self.logger)
        vdcs = vchsType.parseString(self.response.content, True)
        return vdcs.get_VdcRef()

    def get_vdc_reference(self, serviceId, vdcId):
        """
        Request a reference to a specific vdc context hosting a service.

        :param serviceId: (str): The service identifier for the service.
        :param vdcId: (str): The identifier for the virtual data center.
        :return: (ReferenceType) a :class:`pyvcloud.schema.vcim.vchsType.VdcReferenceType` object representing the vdc.
       
        **service type:**  subscription

        """
        vdcReferences = filter(lambda vdcRef: vdcRef.get_name() == vdcId, self.get_vdc_references(serviceId))
        if len(vdcReferences) == 0:
            return None
        return vdcReferences[0]

    #in subscription 1 org <-> 1 vdc
    def login_to_org(self, service, org_name):
        """
        Request to login into a specific organization.
        An organization is a unit of administration for a collection of users, groups, and computing resources. 

        :param service: (str): The service identifer.
        :param org_name: (str): 
        :return: (bool): True if the login was successful, False otherwise.

        **service type:** ondemand, subscription, vcd

        .. note:: for a subscription service,  1 org <-> 1 vdc

        """
        vdcReference = self.get_vdc_reference(service, org_name)
        if vdcReference:
            link = filter(lambda link: link.get_type() == "application/xml;class=vnd.vmware.vchs.vcloudsession", vdcReference.get_Link())[0]
            self.response = Http.post(link.get_href(), headers=self._get_vcloud_headers(), verify=self.verify, logger=self.logger)
            if self.response.status_code == requests.codes.created:
                vchs = vchsType.parseString(self.response.content, True)
                vdcLink = vchs.get_VdcLink()
                headers = {}
                headers[vdcLink.authorizationHeader] = vdcLink.authorizationToken
                headers["Accept"] = "application/*+xml;version=" + self.version
                self.response = Http.get(vdcLink.href, headers=headers, verify=self.verify, logger=self.logger)
                if self.response.status_code == requests.codes.ok:
                    self.vdc = vdcType.parseString(self.response.content, True)
                    self.org = self.vdc.name
                    org_url = filter(lambda link: link.get_type() == "application/vnd.vmware.vcloud.org+xml", self.vdc.get_Link())[0].href
                    vcloud_session = VCS(org_url, self.username, self.org, None, org_url, org_url, version=self.version, verify=self.verify, log=self.log)
                    if vcloud_session.login(password=None, token=vdcLink.authorizationToken):
                        self.vcloud_session = vcloud_session
                        return True
        return False

    #common
    def _get_vcloud_headers(self):
        headers = {}
        if self.service_type == VCA_SERVICE_TYPE_SUBSCRIPTION:
            headers["Accept"] = "application/xml;version=" + self.version
            headers["x-vchs-authorization"] = self.token
        elif self.service_type == VCA_SERVICE_TYPE_ONDEMAND:
            headers["Authorization"] = "Bearer %s" % self.token
            headers["Accept"] = "application/json;version=%s" % self.version
        elif self.service_type == VCA_SERVICE_TYPE_STANDALONE or self.service_type == 'vcd':
            # headers["x-vcloud-authorization"] = self.token
            pass
        return headers

    def get_vdc_templates(self):
        pass

    def get_vdc(self, vdc_name):
        """
        Request a reference to a specific Virtual Data Center.

        A vdc is a logical construct that provides compute, network, and storage resources to an organization. 
        Virtual machines can be created, stored, and operated within a vdc.
        A vdc Data centers also provides storage for virtual media. 

        :param vdc_name: (str): The virtual data center name.
        :return: (VdcType) a :class:`.vcloud.vdcType.VdcType` object describing the vdc. (For example: subscription, ondemand)
        
        **service type:** ondemand, subscription, vcd

        """
        if self.vcloud_session and self.vcloud_session.organization:
            refs = filter(lambda ref: ref.name == vdc_name and ref.type_ == 'application/vnd.vmware.vcloud.vdc+xml', self.vcloud_session.organization.Link)
            if len(refs) == 1:
                self.response = Http.get(refs[0].href, headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
                if self.response.status_code == requests.codes.ok:
                    # print self.response.content
                    return vdcType.parseString(self.response.content, True)

    def get_vapp(self, vdc, vapp_name):
        """
        Request a reference to a specific vapp.

        A vApp is an application package containing 1 or more virtual machines and their required operating system. 

        :param vdc: (VdcType): The virtual data center name.
        :param vapp_name: (str): The name of the requested vapp.
        :return: (VAPP): a :class:`pyvcloud.vapp.VAPP` object describing the vApp. 
       
        **service type:** ondemand, subscription, vcd

        """
        refs = filter(lambda ref: ref.name == vapp_name and ref.type_ == 'application/vnd.vmware.vcloud.vApp+xml', vdc.ResourceEntities.ResourceEntity)
        if len(refs) == 1:
            self.response = Http.get(refs[0].href, headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
            if self.response.status_code == requests.codes.ok:
                vapp = VAPP(vAppType.parseString(self.response.content, True), self.vcloud_session.get_vcloud_headers(), self.verify, self.log)
                return vapp


    def _create_instantiateVAppTemplateParams(self, name, template_href,
                                              vm_name, vm_href, deploy,
                                              power, vm_cpus=None,
                                              vm_memory=None):
        templateParams = vcloudType.InstantiateVAppTemplateParamsType()
        templateParams.set_name(name)
        templateParams.set_deploy(deploy)
        templateParams.set_powerOn(power)
        source = vcloudType.ReferenceType(href=template_href)
        templateParams.set_Source(source)
        templateParams.set_AllEULAsAccepted("true")

        if vm_name or vm_cpus or vm_memory:
            params = vcloudType.SourcedCompositionItemParamType()
            params.set_Source(vcloudType.ReferenceType(href=vm_href))
            if self.version == "5.5":
                pass
            else:
                templateParams.add_SourcedItem(params)

            if vm_name:
                if self.version == "5.5":
                   templateParams.set_name(vm_name)
                else:
                   gen_params = vcloudType.VmGeneralParamsType()
                   gen_params.set_Name(vm_name)
                   params.set_VmGeneralParams(gen_params)

            if vm_cpus or vm_memory:
                inst_param = vcloudType.InstantiationParamsType()
                hardware = vcloudType.VirtualHardwareSection_Type(id=None)
                hardware.original_tagname_ = "VirtualHardwareSection"
                hardware.set_Info(vAppType.cimString(valueOf_="Virtual hardware requirements"))
                inst_param.add_Section(hardware)
                params.set_InstantiationParams(inst_param)

                if vm_cpus:
                    cpudata = vAppType.RASD_Type()
                    cpudata.original_tagname_ = "ovf:Item"
                    cpudata.set_required(None)
                    cpudata.set_AllocationUnits(vAppType.cimString(valueOf_="hertz * 10^6"))
                    cpudata.set_Description(vAppType.cimString(valueOf_="Number of Virtual CPUs"))
                    cpudata.set_ElementName(vAppType.cimString(valueOf_="{0} virtual CPU(s)".format(vm_cpus)))
                    cpudata.set_InstanceID(vAppType.cimInt(valueOf_=1))
                    cpudata.set_ResourceType(3)
                    cpudata.set_VirtualQuantity(vAppType.cimInt(valueOf_=vm_cpus))
                    hardware.add_Item(cpudata)
                if vm_memory:
                    memorydata = vAppType.RASD_Type()
                    memorydata.original_tagname_ = "ovf:Item"
                    memorydata.set_required(None)
                    memorydata.set_AllocationUnits(vAppType.cimString(valueOf_="byte * 2^20"))
                    memorydata.set_Description(vAppType.cimString(valueOf_="Memory Size"))
                    memorydata.set_ElementName(vAppType.cimString(valueOf_="{0} MB of memory".format(vm_memory)))
                    memorydata.set_InstanceID(vAppType.cimInt(valueOf_=2))
                    memorydata.set_ResourceType(4)
                    memorydata.set_VirtualQuantity(vAppType.cimInt(valueOf_=vm_memory))
                    hardware.add_Item(memorydata)

        return templateParams

    def _get_vdc_templates(self):
        content_type = "application/vnd.vmware.admin.vdcTemplates+xml"
        link = filter(lambda link: link.get_type() == content_type, self.vcloud_session.get_Link())
        self.response = requests.get(link[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify)
        if self.response.status_code == requests.codes.ok:
            return vdcTemplateListType.parseString(self.response.content, True)\

    def create_vdc(self, vdc_name):
        vdcTemplateList = self._get_vdc_templates()
        content_type = "application/vnd.vmware.admin.vdcTemplate+xml"
        vdcTemplate = filter(lambda link: link.get_type() == content_type, vdcTemplateList.get_VdcTemplate())
        source = vcloudType.ReferenceType(href=vdcTemplate[0].get_href())

        templateParams = vcloudType.InstantiateVAppTemplateParamsType()  # Too simple to add InstantiateVdcTemplateParamsType class
        templateParams.set_name(vdc_name)
        templateParams.set_Source(source)
        body = CommonUtils.convertPythonObjToStr(templateParams, name="InstantiateVdcTemplateParams",
                                                 namespacedef='xmlns="http://www.vmware.com/vcloud/v1.5"')
        content_type = "application/vnd.vmware.vcloud.instantiateVdcTemplateParams+xml"
        link = filter(lambda link: link.get_type() == content_type, self.vcloud_session.get_Link())
        self.response = requests.post(link[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, data=body)
        if self.response.status_code == requests.codes.accepted:
            task = taskType.parseString(self.response.content, True)
            return task

    def create_vapp(self, vdc_name, vapp_name, template_name, catalog_name,
                    network_name=None, network_mode='bridged', vm_name=None,
                    vm_cpus=None, vm_memory=None, deploy='false',
                    poweron='false'):
        """
        Create a new vApp in a virtual data center.

        A vApp is an application package containing 1 or more virtual machines and their required operating system.


        :param vdc_name: (str): The virtual data center name.
        :param vapp_name: (str): The name of the new vapp.
        :param template_name: (str): The name of a template from a catalog that will be used to create the vApp.
        :param catalog_name: (str): The name of the catalog that contains the named template.
        :param network_name: (str): The name of the network contained within the vApp.
        :param network_mode: (str): The mode for the network contained within the vApp.
        :param vm_name: (str, optional): The name of the Virtual Machine contained in the vApp.
        :param vm_cpus: (str, optional): The number of virtual CPUs assigned to the VM. 
        :param vm_memory: (str, optional): The amount of memory assigned to the VM, specified in MB.
        :param deploy: (bool): True to deploy the vApp immediately after creation, False otherwise.
        :param poweron: (bool): True to poweron the vApp immediately after deployment, False otherwise.
        :return: (task): a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType`, a handle to the asynchronous process executing the request. 

        **service type:**. ondemand, subscription, vcd

        .. note:: In this version of pyvcloud a maximum of 1 vm can be added to a vapp.

        """
        self.vdc = self.get_vdc(vdc_name)
        if not self.vcloud_session or not self.vcloud_session.organization or not self.vdc:
            #"Select an organization and datacenter first"
            return False
        if '' == vm_name: vm_name = None
        catalogs = filter(lambda link: catalog_name == link.get_name() and link.get_type() == "application/vnd.vmware.vcloud.catalog+xml",
                                 self.vcloud_session.organization.get_Link())
        if len(catalogs) == 1:
            self.response = Http.get(catalogs[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
            if self.response.status_code == requests.codes.ok:
                catalog = catalogType.parseString(self.response.content, True)
                catalog_items = filter(lambda catalogItemRef: catalogItemRef.get_name() == template_name, catalog.get_CatalogItems().get_CatalogItem())
                if len(catalog_items) == 1:
                    self.response = Http.get(catalog_items[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
                    # use ElementTree instead because none of the types inside resources (not even catalogItemType) is able to parse the response correctly
                    catalogItem = ET.fromstring(self.response.content)
                    entity = [child for child in catalogItem if child.get("type") == "application/vnd.vmware.vcloud.vAppTemplate+xml"][0]
                    vm_href = None
                    if vm_name:
                        self.response = Http.get(entity.get('href'), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
                        if self.response.status_code == requests.codes.ok:
                            vAppTemplate = ET.fromstring(self.response.content)
                            for vm in vAppTemplate.iter('{http://www.vmware.com/vcloud/v1.5}Vm'):
                                vm_href = vm.get('href')
                    template_params = self._create_instantiateVAppTemplateParams(
                        vapp_name, entity.get("href"), vm_name=vm_name,
                        vm_href=vm_href, vm_cpus=vm_cpus, vm_memory=vm_memory,
                        deploy=deploy, power=poweron)
                    if network_name:
                        pass
                    output = StringIO()
                    template_params.export(output,
                        0,
                        name_ = 'InstantiateVAppTemplateParams',
                        namespacedef_ = '''xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"
                                           xmlns:rasd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData"''',
                                           pretty_print = False)
                    body = '<?xml version="1.0" encoding="UTF-8"?>' + \
                            output.getvalue().replace('class:', 'rasd:')\
                                             .replace(' xmlns:vmw="http://www.vmware.com/vcloud/v1.5"', '')\
                                             .replace('vmw:', 'rasd:')\
                                             .replace('Info>', "ovf:Info>")
                    content_type = "application/vnd.vmware.vcloud.instantiateVAppTemplateParams+xml"
                    link = filter(lambda link: link.get_type() == content_type, self.vdc.get_Link())
                    self.response = Http.post(link[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, data=body, logger=self.logger)
                    if self.response.status_code == requests.codes.created:
                        vApp = vAppType.parseString(self.response.content, True)
                        task = vApp.get_Tasks().get_Task()[0]
                        return task
        return False

    def block_until_completed(self, task):
        """
        Wait on a task until it has completed.
        A task is an asynchronous process executing a request. 
        The status of the task is checked at one second intervals until the task is completed.
        No timeout.
        
        :param task: (task): A :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType`  object that represents a running task.
        :return: (bool) True if the task completed successfully, False if an error completed with an error.
       
        **service type:** ondemand, subscription, vcd

        """
        progress = task.get_Progress()
        status = task.get_status()
        rnd = 0
        while status != "success":
            if status == "error":
                error = task.get_Error()
                Log.error(self.logger, "task error, major=%s, minor=%s, message=%s" % (error.get_majorErrorCode(), error.get_minorErrorCode(), error.get_message()))
                return False
            else:
                # some task doesn't not report progress
                if progress:
                    pass
                else:
                    rnd += 1
                time.sleep(1)
                self.response = Http.get(task.get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
                if self.response.status_code == requests.codes.ok:
                    task = taskType.parseString(self.response.content, True)
                    progress = task.get_Progress()
                    status = task.get_status()
                else:
                    Log.error(self.logger, "can't get task")
                    return False
        return True

    def delete_vapp(self, vdc_name, vapp_name):
        """
        Delete a specific vApp.

        A vApp is an application package containing 1 or more virtual machines and their required operating system. 
        The vApp is undeployed and removed.

        :param vdc_name: (str): The virtual data center name.
        :param vapp_name: (str): The name of the vapp to be deleted.
        :return: (bool) True if the vapp was successfully deleted, false if the vapp was not found.
       
        **service type:** ondemand, subscription, vcd

        """
        self.vdc = self.get_vdc(vdc_name)
        if not self.vcloud_session or not self.vcloud_session.organization or not self.vdc: return False
        vapp = self.get_vapp(self.vdc, vapp_name)
        if not vapp: return False
        #undeploy and remove
        if vapp.me.deployed:
            task = vapp.undeploy()
            if task:
                self.block_until_completed(task)
            else:
                Log.debug(self.logger, "vapp.undeploy() didn't return a task")
                return False
        vapp = self.get_vapp(self.vdc, vapp_name)
        if vapp: return vapp.delete()
        Log.debug(self.logger, "no vApp")

    def get_catalogs(self):
        """
        Request a list of the available Public and Organization catalogs in the vdc. 

        A catalog contains one or more vApp templates and media images.
      
        :return: (list of CatalogType) a list of :class:`pyvcloud.schema.vcd.v1_5.schemas.vcloud.catalogType.CatalogType` objects that describe the available catalogs.
        
        Each CatalogType contains a single :class:`.catalogType.CatalogItemsType` \n
        which contains a list of :class:`.vcloud.catalogType.ReferenceType` objects. 
        use get_name() on a CatalogType to retrieve the catalog name.
        use get_name() on ReferenceType to retrieve the catalog item name.     

        **service type:** ondemand, subscription, vcd

        """
        self.vcloud_session.login(token=self.vcloud_session.token)
        links = filter(lambda link: link.get_type() == "application/vnd.vmware.vcloud.catalog+xml", self.vcloud_session.organization.Link)
        catalogs = []
        for link in links:
            self.response = Http.get(link.get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
            if self.response.status_code == requests.codes.ok:
                catalogs.append(catalogType.parseString(self.response.content, True))
        return catalogs

    def create_catalog(self, catalog_name, description):
        """
        Create a new catalog.

        A catalog is a container for one or more vApp templates and media images.

        :param catalog_name: (str): The name of the new catalog.
        :param description: (str): A description for the new catalog.
        :return: (TaskType) a :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType` object that can be used to monitor the creation of the catalog.
        
        **service type:** ondemand, subscription, vcd

        """
        refs = filter(lambda ref: ref.rel == 'add' and ref.type_ == 'application/vnd.vmware.admin.catalog+xml',
                             self.vcloud_session.organization.Link)
        if len(refs) == 1:
            data = """<?xml version="1.0" encoding="UTF-8"?>
            <AdminCatalog xmlns="http://www.vmware.com/vcloud/v1.5" name="%s">
            <Description>%s</Description>
            </AdminCatalog>
            """ % (catalog_name, description)
            self.response = Http.post(refs[0].href, headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, data=data, logger=self.logger)
            if self.response.status_code == requests.codes.created:
                task = vCloudEntities.parseString(self.response.content, True)
                return task.get_Tasks().get_Task()[0]

    def delete_catalog(self, catalog_name):
        """
        Delete a specific catalog.

        A catalog is a container for one or more vApp templates and media images.

        :param catalog_name: (str): The name of the catalog to delete.
        :return: (bool) True if the catalog was successfully deleted, false if the vapp was not deleted (or found).
        
        **service type:**. ondemand, subscription, vcd

        """
        admin_url = None
        if not self.vcloud_session or not self.vcloud_session.organization: return False
        if 'ondemand' == self.service_type:
            refs = filter(lambda ref: ref.type_ == 'application/vnd.vmware.admin.organization+xml',
                                 self.vcloud_session.organization.Link)
            if len(refs) == 1:
                admin_url = refs[0].href
        else:
            refs = filter(lambda ref: ref.type_ == 'application/vnd.vmware.admin.catalog+xml',
                                 self.vcloud_session.organization.Link)
            if len(refs) == 1:
                admin_url = refs[0].href[:refs[0].href.rindex('/')]
        if admin_url:
            self.response = Http.get(admin_url, headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
            if self.response.status_code == requests.codes.ok:
                adminOrg = vCloudEntities.parseString(self.response.content, True)
                if adminOrg and adminOrg.Catalogs and adminOrg.Catalogs.CatalogReference:
                    catRefs = filter(lambda ref: ref.name == catalog_name and ref.type_ == 'application/vnd.vmware.admin.catalog+xml',
                                            adminOrg.Catalogs.CatalogReference)
                    if len(catRefs) == 1:
                        self.response = Http.delete(catRefs[0].href, headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
                        if self.response.status_code == requests.codes.no_content:
                            return True
        return False


    def upload_media(self, catalog_name, item_name, media_file_name, description=''):
        """
        Uploads a media file (ISO) to a vCloud catalog

        :param catalog_name: (str): The name of the catalog to upload the media.
        :param item_name: (str): The name of the media file in the catalog.
        :param media_file_name: (str): The name of the local media file to upload.
        :return: (bool) True if the media file was successfully uploaded, false otherwise.

        **service type:** ondemand, subscription, vcd

        """
        for catalog in self.get_catalogs():
            if catalog_name != catalog.name:
                continue
            link = filter(lambda link: link.get_type() == "application/vnd.vmware.vcloud.media+xml" and link.get_rel() == 'add', catalog.get_Link())
            assert len(link) == 1
            Log.debug(self.logger, link[0].get_href())
            data = """
            <Media
               xmlns="http://www.vmware.com/vcloud/v1.5"
               name="%s"
               size="%s"
               imageType="iso">
               <Description>%s</Description>
            </Media>
            """ % (item_name, "51242131", description)
            self.response = Http.post(link[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(), 
                            data=data, verify=self.verify, logger=self.logger)
            if self.response.status_code == requests.codes.created:
                catalogItem = ET.fromstring(self.response.content)
                entity = [child for child in catalogItem if child.get("type") == "application/vnd.vmware.vcloud.media+xml"][0]
                href = entity.get('href')
                self.response = Http.get(href, headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
                if self.response.status_code == requests.codes.ok:
                    # Log.debug(self.logger, self.response.content)
                    media = mediaType.parseString(self.response.content, True)
                    link = filter(lambda link: link.get_rel() == 'upload:default', media.get_Files().get_File()[0].get_Link())[0]
                    Log.debug(self.logger, link.get_href())
                    return True
        return False


    def delete_catalog_item(self, catalog_name, item_name):
        """
        Request the deletion of an item from a catalog.
        An item is a vApp template and media image stored in a catalog.

        :param catalog_name: (str): The name of the catalog to delete.
        :param item_name: (str): The name of the catalog item to delete.
        :return: (bool) True if the catalog item was successfully deleted, false if the vapp was not deleted (or found).
        
        **service type:** ondemand, subscription, vcd

        """
        for catalog in self.get_catalogs():
            if catalog_name != catalog.name:
                continue
            if catalog.CatalogItems and catalog.CatalogItems.CatalogItem:
                for item in catalog.CatalogItems.CatalogItem:
                    if item_name == item.name:
                        self.response = Http.delete(item.href, headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
                        if self.response.status_code == requests.codes.no_content:
                            return True
        return False

    def get_gateways(self, vdc_name):
        """
        Request a list of the Gateways within a Virtual Data Center.

        :param vdc_name: (str): The virtual data center name.
        :return: (list of Gateway)  A list of :class:`.pyvcloud.gateway.Gateway` objects describing the available gateways.
       
        **service type:** ondemand, subscription, vcd

        """
        gateways = []
        vdc = self.get_vdc(vdc_name)
        if not vdc: return gateways
        link = filter(lambda link: link.get_rel() == "edgeGateways", vdc.get_Link())
        self.response = Http.get(link[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            queryResultRecords = queryRecordViewType.parseString(self.response.content, True)
            if queryResultRecords.get_Record():
                for edgeGatewayRecord in queryResultRecords.get_Record():
                    self.response = Http.get(edgeGatewayRecord.get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
                    if self.response.status_code == requests.codes.ok:
                        gateway = Gateway(networkType.parseString(self.response.content, True), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, log=self.log)
                        gateways.append(gateway)
        return gateways

    def get_gateway(self, vdc_name, gateway_name):
        """
        Request the details of a specific Gateway Appliance within a Virtual Data Center.

        :param vdc_name: (str): The virtual data center name.
        :param gateway_name: (str): The requested gateway name.
        :return: (Gateway)  A :class:`.pyvcloud.gateway.Gateway` object describing the requested gateway.

        **service type:** ondemand, subscription, vcd

        """
        gateway = None
        vdc = self.get_vdc(vdc_name)
        if not vdc: return gateway
        link = filter(lambda link: link.get_rel() == "edgeGateways", vdc.get_Link())
        self.response = Http.get(link[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            queryResultRecords = queryRecordViewType.parseString(self.response.content, True)
            if queryResultRecords.get_Record():
                for edgeGatewayRecord in queryResultRecords.get_Record():
                    if edgeGatewayRecord.get_name() == gateway_name:
                        self.response = Http.get(edgeGatewayRecord.get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
                        if self.response.status_code == requests.codes.ok:
                            gateway = Gateway(networkType.parseString(self.response.content, True), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, log=self.log)
                            break
        return gateway

    def get_networks(self, vdc_name):
        """
        Request a list of the Networks within a Virtual Data Center.

        :param vdc_name: (str): The virtual data center name.
        :return: (list of OrgVdcNetworkType)  A list of :class:`pyvcloud.schema.vcd.v1_5.schemas.vcloud.networkType.OrgVdcNetworkType` objects describing the available networks.
        
        **service type:** ondemand, subscription, vcd

        """
        result = []
        vdc = self.get_vdc(vdc_name)
        if not vdc: return result
        networks = vdc.get_AvailableNetworks().get_Network()
        for n in networks:
            self.response = Http.get(n.get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
            if self.response.status_code == requests.codes.ok:
                network = networkType.parseString(self.response.content, True)
                result.append(network)
        return result

    def get_network(self, vdc_name, network_name):
        """
        Request the details of a specific Network within a Virtual Data Center.

        :param vdc_name: (str): The virtual data center name.
        :param network_name: (str): The name of the requested network.
        :return: (OrgVdcNetworkType)  An :class:`pyvcloud.schema.vcd.v1_5.schemas.vcloud.networkType.OrgVdcNetworkType` object describing the requested network.
       
        **service type:** ondemand, subscription, vcd

        """
        result = None
        networks = self.get_networks(vdc_name)
        for network in networks:
            if network.get_name() == network_name:
                result = network
        return result

    def parsexml_(self, string_to_parse):
        doc = ET.fromstring(string_to_parse)
        return doc

    def get_media(self, catalog_name, media_name):
        """
        Request a media resource from a catalog. 

        :param catalog_name: (str): The name of the catalog containing the media.
        :param media_name: (str): The name of the requested media.
        :return: (dict of str,str)  An dictionary describing the requested media.
                                    Dictionary keys in include a 'name' key with a value containing the media name.
                                    A 'href' key with a value containing a https url to the media.
                                    And a 'type' key with a value indicating the type of media.
       
        **service type:** ondemand, subscription, vcd

        """
        refs = filter(lambda ref: ref.name == catalog_name and ref.type_ == 'application/vnd.vmware.vcloud.catalog+xml', self.vcloud_session.organization.Link)
        if len(refs) == 1:
            self.response = Http.get(refs[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
            if self.response.status_code == requests.codes.ok:
                catalog = catalogType.parseString(self.response.content, True)
                catalog_items = filter(lambda catalogItemRef: catalogItemRef.get_name() == media_name, catalog.get_CatalogItems().get_CatalogItem())
                if len(catalog_items) == 1:
                    self.response = Http.get(catalog_items[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
                    # print self.response.content
                    if self.response.status_code == requests.codes.ok:
                        doc = self.parsexml_(self.response.content)
                        for element in doc._children:
                            if element.tag == '{http://www.vmware.com/vcloud/v1.5}Entity':
                                return element.attrib

    #todo: send DELETE
    def logout(self):
        """
        Request to logout from  vCloud Air.

        :return:
    
        **service type:** ondemand, subscription, vcd

        """
        if self.service_type == VCA_SERVICE_TYPE_STANDALONE or self.service_type == 'vcd':
            pass
        elif self.service_type == VCA_SERVICE_TYPE_SUBSCRIPTION:
            pass
        elif self.service_type == VCA_SERVICE_TYPE_ONDEMAND:
            pass
        self.token = None
        self.vcloud_session = None

    def create_vdc_network(self, vdc_name, network_name, gateway_name, start_address,
                           end_address, gateway_ip, netmask,
                           dns1, dns2, dns_suffix):
        """
        Request the creation of an new network within a vdc. 

        :param vdc_name: (str): The name of the virtual data center.
        :param network_name: (str): The name of the new network to be deleted.
        :param gateway_name: (str): The name of an existing edge Gateway appliance that will manage the virtual network.
        :param start_address: (str): The first ip address in a range of addresses for the network.
        :param end_address: (str): The last ip address in a range of addresses for the network.
        :return: (tuple of (bool, task or str))  Two values are returned, a bool success indicator and a \
                 :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType`  object if the bool value was True or a \
                 str message indicating the reason for failure if the bool value was False.  

        **service type:** ondemand, subscription, vcd

        """
        vdc = self.get_vdc(vdc_name)
        gateway = ReferenceType(href=self.get_gateway(vdc_name, gateway_name).me.href)
        gateway.original_tagname_ = "EdgeGateway"

        iprange = IpRangeType(StartAddress=start_address,
                              EndAddress=end_address)
        ipranges = IpRangesType(IpRange=[iprange])
        ipscope = IpScopeType(IsInherited=False,
                              Gateway=gateway_ip,
                              Netmask=netmask,
                              Dns1=dns1,
                              Dns2=dns2,
                              DnsSuffix=dns_suffix,
                              IpRanges=ipranges)
        ipscopes = IpScopesType(IpScope=[ipscope])

        configuration = NetworkConfigurationType(IpScopes=ipscopes,
                                                 FenceMode="natRouted")
        net = OrgVdcNetworkType(name=network_name, Description="Network created by pyvcloud",
                                EdgeGateway=gateway, Configuration=configuration,
                                IsShared=False)
        namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5"'
        content_type = "application/vnd.vmware.vcloud.orgVdcNetwork+xml"
        body = '<?xml version="1.0" encoding="UTF-8"?>{0}'.format(
            CommonUtils.convertPythonObjToStr(net, name='OrgVdcNetwork',
                                              namespacedef=namespacedef))
        postlink = filter(lambda link: link.get_type() == content_type,
                          vdc.get_Link())[0].href
        headers = self.vcloud_session.get_vcloud_headers()
        headers["Content-Type"] = content_type
        self.response = Http.post(postlink, data=body, headers=headers, verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.created:
            network = networkType.parseString(self.response.content, True)
            task = network.get_Tasks().get_Task()[0]
            return (True, task)
        else:
            return (False, self.response.content)

    def delete_vdc_network(self, vdc_name, network_name):
        """
        Request the deletion of an existing network within a vdc. 

        :param vdc_name: (str): The name of the virtual data center.
        :param network_name: (str): The name of the new network to be deleted.
        :return: (tuple of (bool, task or str))  Two values are returned, a bool success indicator and a \
                 :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType`  object if the bool value was True or a \
                 str message indicating the reason for failure if the bool value was False.  
        
        **service type:** ondemand, subscription, vcd

        """
        netref = self.get_admin_network_href(vdc_name, network_name)
        if netref is None:
            return (False, 'network not found')
        self.response = Http.delete(netref, headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.accepted:
            task = taskType.parseString(self.response.content, True)
            return (True, task)
        else:
            return (False, self.response.content)

    def get_admin_network_href(self, vdc_name, network_name):
        vdc = self.get_vdc(vdc_name)
        link = filter(lambda link: link.get_rel() == "orgVdcNetworks",
                      vdc.get_Link())
        self.response = Http.get(link[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
        queryResultRecords = queryRecordViewType.parseString(self.response.content, True)
        if self.response.status_code == requests.codes.ok:
            for record in queryResultRecords.get_Record():
                if record.name == network_name:
                    return record.href

    def get_score_service(self, score_service_url):
        if self.vcloud_session is None or self.vcloud_session.token is None:
            Log.error(self.logger, "self.vcloud_session is None")
            return None
        return Score(score_service_url, self.vcloud_session.org_url, self.vcloud_session.token, self.version, self.verify, self.log)

    def get_diskRefs(self, vdc):
        """
        Request a list of references to disk volumes in a vdc.

        :param vdc: (str): The name of the virtual data center.
        :return: (list of ResourceReferenceType)  A list of 
                 :class:`pyvcloud.schema.vcd.v1_5.schemas.vcloud.vdcType.ResourceReferenceType` objects. 
        Use   get_name(), get_type() and get_href() methods on each list entry to return disk details.

        **service type:** ondemand, subscription, vcd

        """
        resourceEntities = vdc.get_ResourceEntities().get_ResourceEntity()
        return [resourceEntity for resourceEntity in resourceEntities
                    if resourceEntity.get_type() == "application/vnd.vmware.vcloud.disk+xml"]

    def _parse_disk(self, content):
        diskDesc = diskType.parseString(content, True)
        disk = DiskType()
        ids = diskDesc.anyAttributes_.get('id').split(':')
        disk.set_id(ids[3])
        disk.set_name(diskDesc.anyAttributes_.get('name'))
        disk.set_size(diskDesc.anyAttributes_.get('size'))
        disk.set_busType(diskDesc.anyAttributes_.get('busType'))
        disk.set_busSubType(diskDesc.anyAttributes_.get('busSubType'))
        disk.set_status(diskDesc.anyAttributes_.get('status'))
        xml = ET.fromstring(content)
        for child in xml:
            if '{http://www.vmware.com/vcloud/v1.5}Owner' == child.tag:
                for grandchild in child:
                    owner = OwnerType()
                    owner.set_User(grandchild.attrib['name'])
                    disk.set_Owner(owner)
            if '{http://www.vmware.com/vcloud/v1.5}StorageProfile' == child.tag:
                storageProfile = VdcStorageProfileType()
                storageProfile.set_name(child.attrib['name'])
                disk.set_StorageProfile(storageProfile)
            if '{http://www.vmware.com/vcloud/v1.5}Tasks' == child.tag:
                task = taskType.parseString(ET.tostring(child.getchildren()[0]), True)
                disk.set_Tasks([task])
        return disk

    def get_disks(self, vdc_name):
        """
        Request a list of disks attached to a vdc. 

        :param vdc_name: (str): The name of a virtual data center.
        :return: (list of tuples of (DiskType, list of str)):  An list of tuples. \
                  Each tuple contains a :class:`pyvcloud.schema.vcd.v1_5.schemas.vcloud.diskType.DiskType` object and a list of vms utilizing the disk. 
        
        **service type:** ondemand, subscription, vcd

        """
        vdc = self.get_vdc(vdc_name)
        links = self.get_diskRefs(vdc)
        disks = []
        for link in links:
            response = Http.get(link.get_href(), headers = self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
            disk = self._parse_disk(response.content)
            vms = []
            content_type = "application/vnd.vmware.vcloud.vms+xml"
            response = Http.get(link.get_href()+'/attachedVms', headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
            # print response.content
            listofvms = vmsType.parseString(response.content, True)
            for vmReference in listofvms.get_VmReference():
                vms.append(vmReference)
            disks.append([disk, vms])
        return disks

    def add_disk(self, vdc_name, name, size):
        """
        Request the creation of an indepdent disk (not attached to a vApp). 

        :param vdc_name: (str): The name of the virtual data center.
        :param name: (str): The name of the new disk.
        :param size: (str): The size of the new disk in MB.
        :return: (tuple(bool, DiskType))  Two values are returned, a bool success indicator and a :class:`pyvcloud.schema.vcd.v1_5.schemas.vcloud.diskType.DiskType` object describing the disk resource.
       
        **service type:** ondemand, subscription, vcd

        """
        data = """
                <vcloud:DiskCreateParams xmlns:vcloud="http://www.vmware.com/vcloud/v1.5">
                    <vcloud:Disk name="%s" size="%s"/>
                </vcloud:DiskCreateParams>
            """ % (name, size)
        vdc = self.get_vdc(vdc_name)
        content_type = "application/vnd.vmware.vcloud.diskCreateParams+xml"
        link = filter(lambda link: link.get_type() == content_type, vdc.get_Link())
        self.response = Http.post(link[0].get_href(), data=data, headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.created:
            disk = self._parse_disk(self.response.content)
            return(True, disk)
        else:
            return(False, self.response.content)

    def delete_disk(self, vdc_name, name, id=None):
        """
        Request the deletion of an existing disk within a vdc. 

        :param vdc_name: (str): The name of the virtual data center.
        :param name: (str): The name of the new disk.
        :param id: (str, optional): The id of the disk resource. 
        :return: (tuple(bool, TaskType))  Two values are returned, a bool success indicator and a \
                 :class:`pyvcloud.schema.vcd.v1_5.schemas.admin.vCloudEntities.TaskType`  object if the bool value was True or a \
                 str message indicating the reason for failure if the bool value was False.  

        **service type:** ondemand, subscription, vcd

        """
        vdc = self.get_vdc(vdc_name)
        refs = self.get_diskRefs(vdc)
        link = []
        if id is not None:
            link = filter(lambda link: link.get_href().endswith('/'+id), refs)
        elif name is not None:
            link = filter(lambda link: link.get_name() == name, refs)
        if len(link) == 1:
            self.response = Http.delete(link[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(), verify=self.verify, logger=self.logger)
            if self.response.status_code == requests.codes.accepted:
                task = taskType.parseString(self.response.content, True)
                return (True, task)
            else:
                return(False, self.response.content)
        elif len(link) == 0:
            return(False, 'disk not found')
        elif len(link) > 1:
            return(False, 'more than one disks found with that name, use the disk id')


    #https://us-texas-1-14.vchs.vmware.com/api/compute/api/task/d298aec0-2b43-4dc0-8978-d73d6b17a20e/action/cancel
    def cancel_task(self, task_url):
        self.response = Http.post(task_url + '/action/cancel', headers=self.vcloud_session.get_vcloud_headers(), 
            verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.no_content:
            return True
        else:
            Log.error(self.logger, "can't cancel task")
            return False

