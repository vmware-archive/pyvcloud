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

import requests
from gateway import Gateway
from vapp import VAPP
from schema.vcd.v1_5.schemas.vcloud import networkType, vdcType, queryRecordViewType, taskType, vAppType, organizationType, catalogType, diskType, vmsType, vcloudType
from schema.vcd.v1_5.schemas.vcloud.diskType import OwnerType, DiskType, VdcStorageProfileType, DiskCreateParamsType
from helper import generalHelperFunctions as ghf
from urlparse import urlparse
from xml.etree import ElementTree as ET

class VCD(object):

    # def __init__(self, vCloudSession, serviceId, vdcId):
    def __init__(self, token, href, version, serviceId, vdcId):
        # vdcLink = vCloudSession.get_VdcLink()
        # self.token = vdcLink.get_authorizationToken()
        self.token = token
        self.href = href
        self.version = version
        self.headers = self._get_vcdHeaders()
        # self.href = vdcLink.get_href()
        self.service = serviceId
        self.vdc = vdcId        
        
    def _get_vcdHeaders(self):
        headers = {}
        headers["x-vcloud-authorization"] = self.token
        headers["Accept"] = "application/*+xml;version=" + self.version
        return headers

    def _get_vdc(self):
        response = requests.get(self.href, headers = self.headers)
        return vdcType.parseString(response.content, True)
        
    def get_vdcResources(self):
        vdc = self._get_vdc()
        computeCapacity = vdc.get_ComputeCapacity()
        cpu = computeCapacity.get_Cpu()
        memory = computeCapacity.get_Memory()
        storageCapacity = vdc.get_StorageCapacity()
        return (cpu, memory, storageCapacity)
        
    def get_gateways(self):
        gateways = []
        link = filter(lambda link: link.get_rel() == "edgeGateways", self._get_vdc().get_Link())
        response = requests.get(link[0].get_href(), headers = self.headers)
        queryResultRecords = queryRecordViewType.parseString(response.content, True)
        if queryResultRecords.get_Record():
            for edgeGatewayRecord in queryResultRecords.get_Record():
                response = requests.get(edgeGatewayRecord.get_href(), headers = self.headers)
                edgeGateway = networkType.parseString(response.content, True)
                gateways.append(Gateway(edgeGateway, self.headers))
        return gateways
        
    def get_gateway(self, gatewayId):
        gateways = filter(lambda gateway: gateway.get_name() == gatewayId, self.get_gateways())
        if gateways:
            return gateways[0]
        return None
        
    # for now, each user is under one org
    def get_org(self):
        vdc = self._get_vdc()
        # link to the organization
        link = filter(lambda link: link.get_type() == "application/vnd.vmware.vcloud.org+xml", vdc.get_Link())[0]
        response = requests.get(link.get_href(), headers = self.headers)
        return organizationType.parseString(response.content, True)
        
    # return all available network references within this virtual data center (use the reference to get the actual network)
    def get_networkRefs(self):
        vdc = self._get_vdc()
        availableNetworks = vdc.get_AvailableNetworks()
        return availableNetworks.get_Network()
        
    # return all catalog references within this virtual data center (use reference to get the actual catalog)
    def get_catalogRefs(self):
        org = self.get_org()
        return filter(lambda link: link.get_type() == "application/vnd.vmware.vcloud.catalog+xml",
                      org.get_Link())

    # return all catalogs within this virtual data center
    def get_catalogs(self):
        links = self.get_catalogRefs()
        catalogs = []
        for link in links:
            response = requests.get(link.get_href(), headers = self.headers)
            catalogs.append(catalogType.parseString(response.content, True))
        return catalogs       
         
    # this method returns a list of catalogs (together with their details) inside the organization that manages the vdc
    # note, this might be limited to 25 by default
    def list_catalogs(self):
        result = []
        catalogs_href = self.href.split("/vdc")[0] + "/catalogs/query"
        response = requests.get(catalogs_href, headers = self.headers)
        # use ET to parse response because some attributes would be missing if it is converted to python object
        queryResultRecords = ET.fromstring(response.content)
        catalogRecords = [child for child in queryResultRecords if "CatalogRecord" in child.tag]
        if catalogRecords:
            for catalogRecord in catalogRecords:
                name = catalogRecord.get("name")
                numberOfVAppTemplates = catalogRecord.get("numberOfVAppTemplates")
                numberOfMedia = catalogRecord.get("numberOfMedia")
                isPublished = catalogRecord.get("isPublished")
                isShared = catalogRecord.get("isShared")
                ownerName = catalogRecord.get("ownerName")
                result.append([name, numberOfVAppTemplates, numberOfMedia, ownerName, isPublished, isShared])
        return result

    # this method returns a list of templates (together with their details) inside the vdc
    def list_templates(self, args):
        result = []
        page = 1
        more_pages = True
        while more_pages:
            templates_href = self.href.split("/vdc")[0] + "/vAppTemplates/query?sortAsc=name&page=%d" % page
            response = requests.get(templates_href, headers=self.headers)
            # use ET to parse response because some attributes would be missing if it is converted to python object
            queryResultRecords = ET.fromstring(response.content)
            more_pages = [child for child in queryResultRecords if "Link" in child.tag and child.attrib['rel'] == 'nextPage']
            if more_pages:
                page = page + 1                
            vAppTemplateRecords = [child for child in queryResultRecords if "VAppTemplateRecord" in child.tag]
            if vAppTemplateRecords:
                # filter out other catalogs if catalog is specified
                if args["--catalog"]:
                    vAppTemplateRecords = filter(lambda vAppTemplateRecord: vAppTemplateRecord.get("catalogName").lower() == args["--catalog"].lower(), vAppTemplateRecords)
                if vAppTemplateRecords:
                    for vAppTemplateRecord in vAppTemplateRecords:
                        catalog = vAppTemplateRecord.get("catalogName")
                        name = vAppTemplateRecord.get("name")
                        status = vAppTemplateRecord.get("status")
                        ownerName = vAppTemplateRecord.get("ownerName")
                        vms = vAppTemplateRecord.get("numberOfVMs")
                        cpu = vAppTemplateRecord.get("numberOfCpus")
                        # memory = int(vAppTemplateRecord.get("memoryAllocationMB")) / 1000 if isinstance(vAppTemplateRecord.get("memoryAllocationMB"), int) else ''
                        # storage = int(vAppTemplateRecord.get("storageKB")) / 1000000 if isinstance(vAppTemplateRecord.get("storageKB"), int) else ''
                        memory = int(vAppTemplateRecord.get("memoryAllocationMB")) / 1024
                        storage = int(vAppTemplateRecord.get("storageKB")) / (1024*1024)
                        storageProfileName = vAppTemplateRecord.get("storageProfileName")
                        result.append([catalog, name, status, ownerName, vms, cpu, memory, storage, storageProfileName])
        return result

    def get_task_from_id(self, id, mode=None):
        url = self.href[:self.href.index('/api')]+'/api/task/'+id
        response = requests.get(url, headers = self.headers)
        if response.status_code == requests.codes.ok:
            task = taskType.parseString(response.content, True)
            if mode == "json":
                print ghf.task_json(response.content)
            else:
                if mode == "table":
                    print ghf.task_table(response.content)
                else:
                    pass
            return (True, task)                            
        else:
            ghf.print_xml_error(response.content, args["--json"])                    
            return (False, None)
        
    def get_task(self, task, mode=None):
        response = requests.get(task.get_href(), headers = self.headers)
        if response.status_code == requests.codes.ok:
            task = taskType.parseString(response.content, True)
            if mode == "json":
                print ghf.task_json(response.content)
            else:
                if mode == "table":
                    print ghf.task_table(response.content)
                else:
                    pass
            return (True, task)                            
        else:
            ghf.print_xml_error(response.content, args["--json"])                    
            return (False, None)
    
    def get_tasks(self):
        vdc = self._get_vdc()
        o = urlparse(vdc.get_href())
        url = o.scheme + '://' + o.netloc
        response = requests.get(url + '/api/query?type=task&page=10&pageSize=20&sortDesc=endDate&format=records', headers = self.headers)
        # print response.content
        queryResultRecords = queryRecordViewType.parseString(response.content, True)
        return queryResultRecords.get_Record()
        # if queryResultRecords.get_Record():
            # for taskRecord in queryResultRecords.get_Record():
            #     print taskRecord.__dict__
                # task = taskType.parseString(response.content, True)
            # if mode == "json":
            #     print ghf.task_json(response.content)
            # else:
            #     if mode == "table":
            #         print ghf.task_table(response.content)
            #     else:
            #         pass
            
    def get_vAppRefs(self):
        vdc = self._get_vdc()
        resourceEntities = vdc.get_ResourceEntities().get_ResourceEntity()
        return [resourceEntity for resourceEntity in resourceEntities
                    if resourceEntity.get_type() == "application/vnd.vmware.vcloud.vApp+xml"]

    def get_vApps(self):
        vAppRefs = self.get_vAppRefs()
        result = []
        for vAppRef in vAppRefs:
            response = requests.get(vAppRef.get_href(),headers=self.headers)
            result.append(vAppType.parseString(response.content, True))
        return result

    def get_vApp(self, vAppName):
        vAppRefs = [vAppRef for vAppRef in self.get_vAppRefs() if vAppRef.get_name().lower() == vAppName.lower()]
        if vAppRefs:
            response = requests.get(vAppRefs[0].get_href(), headers=self.headers)
            vapp = vAppType.parseString(response.content,True)
            return VAPP(vapp, self.headers)
            
    def create_vApp(self, vAppName, template, catalogName, args):
        catalogRefs = filter(lambda catalogRef: catalogRef.get_name().lower() == catalogName.lower(), self.get_catalogRefs())
        if catalogRefs:
            response = requests.get(catalogRefs[0].get_href(), headers=self.headers)
            catalog = catalogType.parseString(response.content, True)
            catalogItemRefs = filter(lambda catalogItemRef: catalogItemRef.get_name().lower() == template.lower(),
                                 catalog.get_CatalogItems().get_CatalogItem())
            if catalogItemRefs:
                response = requests.get(catalogItemRefs[0].get_href(), headers=self.headers)
                # use ElementTree instead because none of the types inside resources (not even catalogItemType) is able to parse the response correctly
                catalogItem = ET.fromstring(response.content)
                # the entity inside catalogItem contains link to get vAppTemplate
                entity = [child for child in catalogItem if child.get("type") == "application/vnd.vmware.vcloud.vAppTemplate+xml"][0]
                # this link gives us the template that can be used to instantiate the vapp
                template_href = entity.get("href")
                # optional arguments
                deploy = args["--deploy"]
                power = args["--on"]
                # create template that can be used as body of http request
                templateParams = VAPP.create_instantiateVAppTemplateParams(vAppName, template_href, deploy, power)

                # if network is specified then connect this vapp to a parent network
                if args["--network"]:
                    # find the name and the href of the chosen parent network
                    networkRefs = filter(lambda networkRef: networkRef.get_name().lower() == args["--network"].lower(), self.get_networkRefs())
                    if networkRefs:
                        network_name = networkRefs[0].get_name()
                        network_href = networkRefs[0].get_href()
                        # fence mode is default to bridged if not specified
                        if not args["--fencemode"]:
                            fence_mode = "bridged"
                        else:
                            fence_mode = args["--fencemode"]
                        # add networkConfigSection to templateParams
                        networkConfigSection = VAPP.create_networkConfigSection(network_name, network_href, fence_mode)
                        instantiationParams = vcloudType.InstantiationParamsType()
                        instantiationParams.add_Section(networkConfigSection)
                        # add networkConnectionSection to templateParams
                        ipAddressAllocationMode = args["--IpAddressAllocationMode"]        
                            # def create_networkConnectionSection(network_name, network_href, IpAddressAllocationMode):
                        # networkConnectionSection = VAPP.create_networkConnectionSection(network_name, network_href, ipAddressAllocationMode)
                        # instantiationParams.add_Section(networkConnectionSection)
                        
                        templateParams.set_InstantiationParams(instantiationParams)
                    else:
                        ghf.print_error("no such network found", args["--json"])
                        return (False, None)  

                # turn templateParams into body of http requests (a bit complicated because some of the elements
                # inside templateParams do not have the right names that can be used as the body of http request
                # so need to be replaced with the new name)
                body = '<?xml version="1.0" encoding="UTF-8"?>' + \
                ghf.convertPythonObjToStr(templateParams, name = 'InstantiateVAppTemplateParams',
                                          namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"').\
                replace("ovf:Section", "NetworkConfigSection", 2).replace('Info msgid=""', "ovf:Info").replace("/Info", "/ovf:Info")
                
                #if version >= 5.6
                # body = body.replace("<AllEULAsAccepted>",
                # """
                # <SourcedVmInstantiationParams>
                #     <Source href="https://p1v21-vcd.vchs.vmware.com/api/vAppTemplate/vappTemplate-971dd408-5f80-4bb7-89d2-764d6bbb1517"/>
                #     <InstantiationParams>
                #         <NetworkConnectionSection>
                #             <ovf:Info />
                #             <PrimaryNetworkConnectionIndex>0</PrimaryNetworkConnectionIndex>
                #             <NetworkConnection needsCustomization="true" network="%s">
                #                 <NetworkConnectionIndex>0</NetworkConnectionIndex>
                #                 <IsConnected>true</IsConnected>
                #                 <IpAddressAllocationMode>POOL</IpAddressAllocationMode>
                #             </NetworkConnection>
                #         </NetworkConnectionSection>
                #     </InstantiationParams>
                # </SourcedVmInstantiationParams>
                # <AllEULAsAccepted>
                # """ % args["--network"])
                # # .replace("ovf:Section", "NetworkConnectionSection", 2)
                # print body
                # find link from vdc that can be used for post request
                vdc = self._get_vdc()
                content_type = "application/vnd.vmware.vcloud.instantiateVAppTemplateParams+xml"
                # get link element that contains an action URL for instantiateVAppTemplate.
                # It implements an action that adds an object (a vApp) to the VDC.
                link = filter(lambda link: link.get_type() == content_type, vdc.get_Link())
                # send post request using this body as data
                response = requests.post(link[0].get_href(), data=body, headers=self.headers)
                if response.status_code == requests.codes.created:
                    vApp = vAppType.parseString(response.content, True)
                    task = vApp.get_Tasks().get_Task()[0]
                    task_string = ghf.convertPythonObjToStr(task, name = 'Task')
                    # if blocking then display progress bar before outputing the result 
                    if args["--blocking"]:
                        ghf.display_progress(task, args["--json"], self.headers)
                    # else display result immediately
                    else:
                        return(True, vApp)
                        # if args["--json"]:
                        #     print ghf.task_json(task_string)
                        # else:
                        #     print ghf.task_table(task_string)
                else:
                    # print error
                    # ghf.print_xml_error(response.content, args["--json"])
                    return(False, response.content)  
            else:
                # ghf.print_error("No such template found in this catalog", args["--json"])
                return(False, "No such template found in this catalog")
        else:
            # ghf.print_error("No such catalog found", args["--json"])   
            return(False, "No such catalog found")
            
    def connect_vApp(self, vApp, networkName, fenceMode):
        networkRefs = filter(lambda networkRef: networkRef.get_name().lower() == networkName.lower(), self.get_networkRefs())
        if networkRefs:
            network_name = networkRefs[0].get_name()
            network_href = networkRefs[0].get_href()
            return vApp.connect_to_network(network_name, network_href, fenceMode, False, True)
        else:
            ghf.print_error("network not found", args["--json"])
            return (False, "network not found")
    
    def disconnect_vApp(self, vApp, networkName):
        return vApp.disconnect_from_network(networkName, False, True)
            
    # def connect_vApp(self, vApp, networkName, fenceMode):
    #     networkRefs = filter(lambda networkRef: networkRef.get_name().lower() == networkName.lower(), self.get_networkRefs())
    #     if networkRefs:
    #         network_name = networkRefs[0].get_name()
    #         network_href = networkRefs[0].get_href()
    #         parentNetwork = vcloudType.ReferenceType(href=network_href)
    #         configuration = vcloudType.NetworkConfigurationType()
    #         configuration.set_ParentNetwork(parentNetwork)
    #         configuration.set_FenceMode(fenceMode)
    #         networkConfig = vcloudType.VAppNetworkConfigurationType()
    #         networkConfig.set_networkName(network_name)
    #         networkConfig.set_Configuration(configuration)
    #         info = vcloudType.Msg_Type()
    #         info.set_valueOf_("Configuration parameters for logical networks")
    #         networkConfigSection = vcloudType.NetworkConfigSectionType()
    #         networkConfigSection.add_NetworkConfig(networkConfig)
    #         networkConfigSection.set_Info(info)
    #         body = '<?xml version="1.0" encoding="UTF-8"?>' + \
    #         ghf.convertPythonObjToStr(networkConfigSection, name = 'NetworkConfigSection',
    #                                   namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1"').\
    #         replace('Info msgid=""', "ovf:Info").replace("/Info", "/ovf:Info")
    #         response = requests.put(vApp.me.get_href() + "/networkConfigSection/", data = body, headers=self.headers)
    #         if response.status_code == requests.codes.accepted:
    #             task = taskType.parseString(response.content, True)
    #             ghf.display_progress(task, False, self.headers)
    #             task = taskType.parseString(response.content, True)
    #             return (True, task)
    #         else:
    #             return (False, response.content)
    #     else:
    #         ghf.print_error("network not found", args["--json"])
    #         return (False, "network not found")
            
    def get_diskRefs(self):
        vdc = self._get_vdc()
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
        return disk
        
    # return all independent disks within this virtual data center
    def get_disks(self):
        links = self.get_diskRefs()
        disks = []
        for link in links:
            response = requests.get(link.get_href(), headers = self.headers)
            disk = self._parse_disk(response.content)

            vms = []
            content_type = "application/vnd.vmware.vcloud.vms+xml"
            response = requests.get(link.get_href()+'/attachedVms', headers = self.headers)
            # print response.content
            listofvms = vmsType.parseString(response.content, True)
            for vmReference in listofvms.get_VmReference():
                # print vmReference.name
                vms.append(vmReference)
            disks.append([disk, vms])
        return disks
        
    def add_disk(self, name, size):
        body = """
                <vcloud:DiskCreateParams xmlns:vcloud="http://www.vmware.com/vcloud/v1.5">
                    <vcloud:Disk name="%s" size="%s"/>
                </vcloud:DiskCreateParams>
            """ % (name, size)        
        vdc = self._get_vdc()
        content_type = "application/vnd.vmware.vcloud.diskCreateParams+xml"
        link = filter(lambda link: link.get_type() == content_type, vdc.get_Link())
        response = requests.post(link[0].get_href(), data=body, headers=self.headers)
        if response.status_code == requests.codes.created:
            disk = self._parse_disk(response.content)
            return(True, disk)
        else:
            return(False, response.content)
            
    def delete_disk(self, id):
        link = filter(lambda link: link.get_href().endswith(id), self.get_diskRefs())
        if len(link)>0:
            response = requests.delete(link[0].get_href(), headers=self.headers)
            if response.status_code == requests.codes.accepted:
                task = taskType.parseString(response.content, True)
                return (True, task)            
            else:
                return(False, response.content)
        else:
            return(False, 'disk not found')
            
    #usage attach_disk(vcd.get_vApp('vapp'), 'vm', 'disk')
    def attach_disk(self, vApp, vm, disk):
        diskRefs = filter(lambda diskRef: diskRef.get_href().endswith('/disk/' + disk) or diskRef.get_name() == disk, self.get_diskRefs())
        if diskRefs:
            return vApp.attach_disk_to_vm(vm, diskRefs[0])
        else:
            return (False, 'disk not found')
            
    def detach_disk(self, vApp, vm, disk):
        diskRefs = filter(lambda diskRef: diskRef.get_href().endswith('/disk/' + disk) or diskRef.get_name() == disk, self.get_diskRefs())
        if diskRefs:
            return vApp.detach_disk_from_vm(vm, diskRefs[0])
        else:
            return (False, 'disk not found')
            

