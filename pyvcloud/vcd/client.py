# VMware vCloud Director Python SDK
# Copyright (c) 2017-2018 VMware, Inc. All Rights Reserved.
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

from datetime import datetime
from datetime import timedelta
from distutils.version import StrictVersion
from enum import Enum
import json
import logging
import sys
import time
import urllib

from lxml import etree
from lxml import objectify
import requests

from pyvcloud.vcd.exceptions import AccessForbiddenException, \
    BadRequestException, ClientException, ConflictException, \
    EntityNotFoundException, InternalServerException, \
    InvalidContentLengthException, MethodNotAllowedException, \
    MissingLinkException, MissingRecordException, MultipleLinksException, \
    MultipleRecordsException, NotAcceptableException, NotFoundException, \
    OperationNotSupportedException, RequestTimeoutException,\
    TaskTimeoutException, UnauthorizedException, UnknownApiException, \
    UnsupportedMediaTypeException, VcdException, VcdResponseException, \
    VcdTaskException  # NOQA

SIZE_1MB = 1024 * 1024

NSMAP = {
    'ovf':
    'http://schemas.dmtf.org/ovf/envelope/1',
    'ovfenv':
    'http://schemas.dmtf.org/ovf/environment/1',
    'rasd':
    'http://schemas.dmtf.org/wbem/wscim/1/cim-schema/'
    '2/CIM_ResourceAllocationSettingData',
    'vcloud':
    'http://www.vmware.com/vcloud/v1.5',
    've':
    'http://www.vmware.com/schema/ovfenv',
    'vmw':
    'http://www.vmware.com/schema/ovf',
    'vmext':
    'http://www.vmware.com/vcloud/extension/v1.5',
    'xs':
    'http://www.w3.org/2001/XMLSchema',
    'xsi':
    'http://www.w3.org/2001/XMLSchema-instance'
}

# Convenience objects for building vCloud API XML objects
E = objectify.ElementMaker(
    annotate=False,
    namespace=NSMAP['vcloud'],
    nsmap={
        None: NSMAP['vcloud'],
        'xsi': NSMAP['xsi'],
        'xs': NSMAP['xs'],
        'ovf': NSMAP['ovf']
    })

E_VMEXT = objectify.ElementMaker(
    annotate=False,
    namespace=NSMAP['vmext'],
    nsmap={
        None: NSMAP['vcloud'],
        'vmext': NSMAP['vmext']
    })

E_OVF = objectify.ElementMaker(
    annotate=False, namespace=NSMAP['ovf'], nsmap={None: NSMAP['ovf']})

E_RASD = objectify.ElementMaker(
    annotate=False,
    namespace=NSMAP['rasd'],
    nsmap={
        None: NSMAP['rasd'],
        'vcloud': NSMAP['vcloud']
    })


class ApiVersion(Enum):
    VERSION_29 = '29.0'
    VERSION_30 = '30.0'
    VERSION_31 = '31.0'
    VERSION_32 = '32.0'


# Important! Values must be listed in ascending order.
API_CURRENT_VERSIONS = [
    ApiVersion.VERSION_29.value, ApiVersion.VERSION_30.value,
    ApiVersion.VERSION_31.value, ApiVersion.VERSION_32.value
]


class EdgeGatewayType(Enum):
    NSXV_BACKED = 'NSXV_BACKED'
    NSXT_BACKED = 'NSXT_BACKED'
    NSXT_IMPORTED = 'NSXT_IMPORTED'


class IpAddressMode(Enum):
    DHCP = 'DHCP'
    POOL = 'POOL'
    MANUAL = 'MANUAL'
    NONE = 'NONE'


class VmNicProperties(Enum):
    INDEX = 'index'
    CONNECTED = 'connected'
    PRIMARY = 'primary'
    NETWORK = 'network'
    IP_ADDRESS_MODE = 'ip_address_mode'
    IP_ADDRESS = 'ip_address'
    ADAPTER_TYPE = 'adapter_type'


VCLOUD_STATUS_MAP = {
    -1: "Could not be created",
    0: "Unresolved",
    1: "Resolved",
    2: "Deployed",
    3: "Suspended",
    4: "Powered on",
    5: "Waiting for user input",
    6: "Unknown state",
    7: "Unrecognized state",
    8: "Powered off",
    9: "Inconsistent state",
    10: "Children do not all have the same status",
    11: "Upload initiated, OVF descriptor pending",
    12: "Upload initiated, copying contents",
    13: "Upload initiated , disk contents pending",
    14: "Upload has been quarantined",
    15: "Upload quarantine period has expired"
}


class BasicLoginCredentials(object):
    def __init__(self, user, org, password):
        self.user = user
        self.org = org
        self.password = password


class RelationType(Enum):
    ADD = 'add'
    ALTERNATE = 'alternate'
    CONTROL_ACCESS = 'controlAccess'
    CONVERT_TO_ADVANCED_GATEWAY = 'edgeGateway:convertToAdvancedGateway'
    DEPLOY = 'deploy'
    DISABLE = 'disable'
    DISABLE_GATEWAY_DISTRIBUTED_ROUTING = \
        'edgeGateway:disableDistributedRouting'
    DISK_ATTACH = 'disk:attach'
    DISK_DETACH = 'disk:detach'
    DOWN = 'down'
    DOWN_EXTENSIBILITY = 'down:extensibility'
    DOWNLOAD_DEFAULT = 'download:default'
    EDGE_GATEWAYS = 'edgeGateways'
    EDIT = 'edit'
    ENABLE = 'enable'
    ENABLE_GATEWAY_DISTRIBUTED_ROUTING =\
        'edgeGateway:enableDistributedRouting'
    GATEWAY_REDEPLOY = 'edgeGateway:redeploy'
    GATEWAY_SYNC_SYSLOG_SETTINGS = 'edgeGateway:syncSyslogSettings'
    GATEWAY_SYS_SERVER_SETTING_IP = 'edgeGateway:configureSyslogServerSettings'
    GATEWAY_UPDATE_PROPERTIES = 'edgeGateway:updateProperties'
    LINK_TO_TEMPLATE = 'linkToTemplate'
    MIGRATE_VMS = 'migrateVms'
    MODIFY_FORM_FACTOR = 'edgeGateway:modifyFormFactor'
    NEXT_PAGE = 'nextPage'
    ORG_VDC_NETWORKS = 'orgVdcNetworks'
    POWER_OFF = 'power:powerOff'
    POWER_ON = 'power:powerOn'
    POWER_REBOOT = 'power:reboot'
    POWER_RESET = 'power:reset'
    POWER_SHUTDOWN = 'power:shutdown'
    POWER_SUSPEND = 'power:suspend'
    PUBLISH = 'publish'
    RECOMPOSE = 'recompose'
    REMOVE = 'remove'
    REPAIR = 'repair'
    RIGHTS = 'rights'
    RESOURCE_POOL_VM_LIST = 'resourcePoolVmList'
    SNAPSHOT_CREATE = 'snapshot:create'
    SNAPSHOT_REVERT_TO_CURRENT = 'snapshot:revertToCurrent'
    SNAPSHOT_REMOVE_ALL = 'snapshot:removeAll'
    TASK_CANCEL = 'task:cancel'
    UNDEPLOY = 'undeploy'
    UNLINK_FROM_TEMPLATE = 'unlinkFromTemplate'
    UNREGISTER = 'unregister'
    UP = 'up'
    UPDATE_RESOURCE_POOLS = 'update:resourcePools'
    VDC_ROUTED_CONVERT_TO_DISTRIBUTED_INTERFACE = \
        'orgVdcNetwork:convertToDistributedInterface'
    VDC_ROUTED_CONVERT_TO_SUB_INTERFACE = 'orgVdcNetwork:convertToSubInterface'
    VDC_ROUTED_CONVERT_TO_INTERNAL_INTERFACE = \
        'orgVdcNetwork:convertToInternalInterface'


class ResourceType(Enum):
    """Contains resource type names."""

    ACL_RULE = 'aclRule'
    ADMIN_API_DEFINITION = 'adminApiDefinition'
    ADMIN_ALLOCATED_EXTERNAL_ADDRESS = 'adminAllocatedExternalAddress'
    ADMIN_CATALOG = 'adminCatalog'
    ADMIN_CATALOG_ITEM = 'adminCatalogItem'
    ADMIN_DISK = 'adminDisk'
    ADMIN_EVENT = 'adminEvent'
    ADMIN_FILE_DESCRIPTOR = 'adminFileDescriptor'
    ADMIN_GROUP = 'adminGroup'
    ADMIN_MEDIA = 'adminMedia'
    ADMIN_ORG_NETWORK = 'adminOrgNetwork'
    ADMIN_ORG_VDC = 'adminOrgVdc'
    ADMIN_ORG_VDC_STORAGE_PROFILE = 'adminOrgVdcStorageProfile'
    ADMIN_ROLE = 'adminRole'
    ADMIN_SERVICE = 'adminService'
    ADMIN_SHADOW_VM = 'adminShadowVM'
    ADMIN_TASK = 'adminTask'
    ADMIN_USER = 'adminUser'
    ADMIN_VAPP = 'adminVApp'
    ADMIN_VAPP_NETWORK = 'adminVAppNetwork'
    ADMIN_VAPP_TEMPLATE = 'adminVAppTemplate'
    ADMIN_VM = 'adminVM'
    ADMIN_VM_DISK_RELATION = 'adminVMDiskRelation'
    ALLOCATED_EXTERNAL_ADDRESS = 'allocatedExternalAddress'
    API_DEFINITION = 'apiDefinition'
    API_FILTER = 'apiFilter'
    BLOCKING_TASK = 'blockingTask'
    CATALOG = 'catalog'
    CATALOG_ITEM = 'catalogItem'
    CELL = 'cell'
    CONDITION = 'condition'
    DATASTORE = 'datastore'
    DATASTORE_PROVIDER_VDC_RELATION = 'datastoreProviderVdcRelation'
    DISK = 'disk'
    DV_SWITCH = 'dvSwitch'
    EDGE_GATEWAY = 'edgeGateway'
    EVENT = 'event'
    EXTERNAL_LOCALIZATION = 'externalLocalization'
    EXTERNAL_NETWORK = 'externalNetwork'
    FILE_DESCRIPTOR = 'fileDescriptor'
    FROM_CLOUD_TUNNEL = 'fromCloudTunnel'
    GROUP = 'group'
    HOST = 'host'
    MEDIA = 'media'
    NETWORK_POOL = 'networkPool'
    NSXT_MANAGER = 'nsxTManager'
    ORGANIZATION = 'organization'
    ORG_NETWORK = 'orgNetwork'
    ORG_VDC = 'orgVdc'
    ORG_VDC_NETWORK = 'orgVdcNetwork'
    ORG_VDC_RESOURCE_POOL_RELATION = 'orgVdcResourcePoolRelation'
    ORG_VDC_STORAGE_PROFILE = 'orgVdcStorageProfile'
    PORT_GROUP = 'portgroup'
    PROVIDER_VDC = 'providerVdc'
    PROVIDER_VDC_RESOURCE_POOL_RELATION = 'providerVdcResourcePoolRelation'
    PROVIDER_VDC_STORAGE_PROFILE = 'providerVdcStorageProfile'
    RESOURCE_CLASS = 'resourceClass'
    RESOURCE_CLASS_ACTION = 'resourceClassAction'
    RESOURCE_POOL = 'resourcePool'
    RESOURCE_POOL_VM_LIST = 'resourcePoolVmList'
    RIGHT = 'right'
    ROLE = 'role'
    SERVICE = 'service'
    SERVICE_LINK = 'serviceLink'
    SERVICE_RESOURCE = 'serviceResource'
    STRANDED_ITEM = 'strandedItem'
    STRANDED_USER = 'strandedUser'
    TASK = 'task'
    TO_CLOUD_TUNNEL = 'toCloudTunnel'
    USER = 'user'
    VAPP = 'vApp'
    VAPP_NETWORK = 'vAppNetwork'
    VAPP_ORG_VDC_NETWORK_RELATION = 'vAppOrgVdcNetworkRelation'
    VAPP_TEMPLATE = 'vAppTemplate'
    VIRTUAL_CENTER = 'virtualCenter'
    VM = 'vm'
    VM_DISK_RELATION = 'vmDiskRelation'
    VM_GROUPS = 'vmGroups'
    VM_GROUP_VMS = 'vmGroupVms'


RESOURCE_TYPES = [r.value for r in ResourceType]


class EntityType(Enum):
    ADMIN = 'application/vnd.vmware.admin.vcloud+xml'
    ADMIN_CATALOG = 'application/vnd.vmware.admin.catalog+xml'
    ADMIN_ORG = 'application/vnd.vmware.admin.organization+xml'
    ADMIN_SERVICE = 'application/vnd.vmware.admin.service+xml'
    ALLOCATED_NETWORK_ADDRESS = \
        'application/vnd.vmware.vcloud.allocatedNetworkAddress+xml'
    API_EXTENSIBILITY = 'application/vnd.vmware.vcloud.apiextensibility+xml'
    AMQP_SETTINGS = 'application/vnd.vmware.admin.amqpSettings+xml'
    CATALOG = 'application/vnd.vmware.vcloud.catalog+xml'
    CAPTURE_VAPP_PARAMS = \
        'application/vnd.vmware.vcloud.captureVAppParams+xml'
    COMPOSE_VAPP_PARAMS = \
        'application/vnd.vmware.vcloud.composeVAppParams+xml'
    CONTROL_ACCESS_PARAMS = 'application/vnd.vmware.vcloud.controlAccess+xml'
    DEFAULT_CONTENT_TYPE = 'application/*+xml'
    DEPLOY = 'application/vnd.vmware.vcloud.deployVAppParams+xml'
    DISK = 'application/vnd.vmware.vcloud.disk+xml'
    DISK_ATTACH_DETACH_PARAMS = \
        'application/vnd.vmware.vcloud.diskAttachOrDetachParams+xml'
    DISK_CREATE_PARMS = 'application/vnd.vmware.vcloud.diskCreateParams+xml'
    EDGE_GATEWAY = 'application/vnd.vmware.admin.edgeGateway+xml'
    EDGE_GATEWAY_FORM_FACTOR = \
        'application/vnd.vmware.vcloud.edgeGatewayFormFactor+xml'
    EDGE_GATEWAY_SERVICE_CONFIGURATION = \
        'application/vnd.vmware.admin.edgeGatewayServiceConfiguration+xml'
    EDGE_GATEWAY_SYS_LOG_SERVER_IP = \
        'application/vnd.vmware.vcloud.SyslogSettings+xml'
    EXTENSION = 'application/vnd.vmware.admin.vmwExtension+xml'
    EXTENSION_SERVICES = 'application/vnd.vmware.admin.extensionServices+xml'
    EXTERNAL_NETWORK = 'application/vnd.vmware.admin.vmwexternalnet+xml'
    EXTERNAL_NETWORK_REFS = \
        'application/vnd.vmware.admin.vmwExternalNetworkReferences+xml'
    INSTANTIATE_VAPP_TEMPLATE_PARAMS = \
        'application/vnd.vmware.vcloud.instantiateVAppTemplateParams+xml'
    LEASE_SETTINGS = 'application/vnd.vmware.vcloud.leaseSettingsSection+xml'
    MEDIA = 'application/vnd.vmware.vcloud.media+xml'
    METADATA = 'application/vnd.vmware.vcloud.metadata+xml'
    METADATA_VALUE = 'application/vnd.vmware.vcloud.metadata.value+xml'
    NETWORK_CONFIG_SECTION = \
        'application/vnd.vmware.vcloud.networkConfigSection+xml'
    NETWORK_CONNECTION_SECTION = \
        'application/vnd.vmware.vcloud.networkConnectionSection+xml'
    NETWORK_MANAGERS = 'application/vnd.vmware.admin.networkManagers+xml'
    NETWORK_POOL_REFERENCES = \
        'application/vnd.vmware.admin.vmwNetworkPoolReferences+xml'
    NSXT_MANAGER = 'application/vnd.vmware.admin.nsxTmanager+xml'
    ORG = 'application/vnd.vmware.vcloud.org+xml'
    ORG_NETWORK = 'application/vnd.vmware.vcloud.orgNetwork+xml'
    ORG_LIST = 'application/vnd.vmware.vcloud.orgList+xml'
    ORG_RIGHTS = 'application/vnd.vmware.admin.org.rights+xml'
    ORG_VDC_NETWORK = 'application/vnd.vmware.vcloud.orgVdcNetwork+xml'
    OWNER = 'application/vnd.vmware.vcloud.owner+xml'
    PROVIDER_VDC = 'application/vnd.vmware.admin.providervdc+xml'
    PROVIDER_VDC_PARAMS = \
        'application/vnd.vmware.admin.createProviderVdcParams+xml'
    PUBLISH_CATALOG_PARAMS = \
        'application/vnd.vmware.admin.publishCatalogParams+xml'
    QUERY_LIST = 'application/vnd.vmware.vcloud.query.queryList+xml'
    RASD_ITEM = 'application/vnd.vmware.vcloud.rasdItem+xml'
    RASD_ITEMS_LIST = 'application/vnd.vmware.vcloud.rasdItemsList+xml'
    RECOMPOSE_VAPP_PARAMS = \
        'application/vnd.vmware.vcloud.recomposeVAppParams+xml'
    RECORDS = 'application/vnd.vmware.vcloud.query.records+xml'
    REGISTER_VC_SERVER_PARAMS = \
        'application/vnd.vmware.admin.registerVimServerParams+xml'
    RESOURCE_POOL_LIST = \
        'application/vnd.vmware.admin.resourcePoolList+xml'
    RES_POOL_SET_UPDATE_PARAMS = \
        'application/vnd.vmware.admin.resourcePoolSetUpdateParams+xml'
    ROLE = 'application/vnd.vmware.admin.role+xml'
    RIGHT = 'application/vnd.vmware.admin.right+xml'
    RIGHTS = 'application/vnd.vmware.admin.rights+xml'
    SNAPSHOT_CREATE = 'application/vnd.vmware.vcloud.createSnapshotParams+xml'
    SYSTEM_SETTINGS = 'application/vnd.vmware.admin.systemSettings+xml'
    TASK = 'application/vnd.vmware.vcloud.task+xml'
    TASKS_LIST = 'application/vnd.vmware.vcloud.tasksList+xml'
    TEXT_XML = 'text/xml'
    UNDEPLOY = 'application/vnd.vmware.vcloud.undeployVAppParams+xml'
    UPDATE_PROVIDER_VDC_STORAGE_PROFILES = \
        'application/vnd.vmware.admin.updateProviderVdcStorageProfiles+xml'
    UPLOAD_VAPP_TEMPLATE_PARAMS = \
        'application/vnd.vmware.vcloud.uploadVAppTemplateParams+xml'
    USER = 'application/vnd.vmware.admin.user+xml'
    VAPP = 'application/vnd.vmware.vcloud.vApp+xml'
    VAPP_TEMPLATE = 'application/vnd.vmware.vcloud.vAppTemplate+xml'
    VDC = 'application/vnd.vmware.vcloud.vdc+xml'
    VDC_ADMIN = 'application/vnd.vmware.admin.vdc+xml'
    VDC_REFERENCES = 'application/vnd.vmware.admin.vdcReferences+xml'
    VDCS_PARAMS = 'application/vnd.vmware.admin.createVdcParams+xml'
    VIM_SERVER_REFS = 'application/vnd.vmware.admin.vmwVimServerReferences+xml'
    VIRTUAL_CENTER = 'application/vnd.vmware.admin.vmwvirtualcenter+xml'
    VM = 'application/vnd.vmware.vcloud.vm+xml'
    VMS = 'application/vnd.vmware.vcloud.vms+xml'
    VMW_PROVIDER_VDC_RESOURCE_POOL = \
        'application/vnd.vmware.admin.vmwProviderVdcResourcePool+xml'
    VMW_PROVIDER_VDC_RESOURCE_POOL_SET = \
        'application/vnd.vmware.admin.vmwProviderVdcResourcePoolSet+xml'
    VMW_PVDC_STORAGE_PROFILE = \
        'application/vnd.vmware.admin.vmwPvdcStorageProfile+xml'
    VMW_STORAGE_PROFILES = \
        'application/vnd.vmware.admin.vmwStorageProfiles+xml'


class QueryResultFormat(Enum):
    RECORDS = ('application/vnd.vmware.vcloud.query.records+xml', 'records')
    ID_RECORDS = ('application/vnd.vmware.vcloud.query.idrecords+xml',
                  'idrecords')
    REFERENCES = ('application/vnd.vmware.vcloud.query.references+xml',
                  'references')


class _WellKnownEndpoint(Enum):
    LOGGED_IN_ORG = (RelationType.DOWN, EntityType.ORG.value)
    ORG_VDC = (RelationType.DOWN, EntityType.VDC.value)
    ORG_NETWORK = (RelationType.DOWN, EntityType.ORG_NETWORK.value)
    ORG_CATALOG = (RelationType.DOWN, EntityType.CATALOG.value)
    QUERY_LIST = (RelationType.DOWN, EntityType.QUERY_LIST.value)
    ADMIN = (RelationType.DOWN, EntityType.ADMIN.value)
    API_EXTENSIBILITY = (RelationType.DOWN_EXTENSIBILITY,
                         EntityType.API_EXTENSIBILITY.value)
    EXTENSION = (RelationType.DOWN, EntityType.EXTENSION.value)
    ORG_LIST = (RelationType.DOWN, EntityType.ORG_LIST.value)
    SNAPSHOT_CREATE = (RelationType.SNAPSHOT_CREATE,
                       EntityType.SNAPSHOT_CREATE.value)


class FenceMode(Enum):
    ISOLATED = 'isolated'
    DIRECT = 'direct'
    BRIDGED = 'bridged'
    NAT_ROUTED = 'natRouted'


class NetworkAdapterType(Enum):
    VMXNET = 'VMXNET'
    VMXNET2 = 'VMXNET2'
    VMXNET3 = 'VMXNET3'
    E1000 = 'E1000'
    E1000E = 'E1000E'
    VLANCE = 'PCNet32'


# vCD docs are incomplete about valid Metadata Domain and Visibility values
# Looking at vCD code the following are the only valid combinations, anything
# else will generate a 400 or 500 response from vCD.
# SYSTEM - PRIVATE
# SYSTEM - READONLY
# GENERAL - READWRITE
class MetadataDomain(Enum):
    GENERAL = 'GENERAL'
    SYSTEM = 'SYSTEM'


class MetadataVisibility(Enum):
    PRIVATE = 'PRIVATE'
    READONLY = 'READONLY'
    READ_WRITE = 'READWRITE'


class MetadataValueType(Enum):
    STRING = 'MetadataStringValue'
    NUMBER = 'MetadataNumberValue'
    BOOLEAN = 'MetadataBooleanValue'
    DATA_TIME = 'MetadataDateTimeValue'


def _get_session_endpoints(session):
    """Return a map of well known endpoints.

    Build and return a map keyed by well-known endpoints, yielding hrefs,
    from a <Session> XML element.

    :param lxml.objectify.ObjectifiedElement session: session object.

    :return: session endpoint hrefs.

    :rtype: dict
    """
    smap = {}
    for endpoint in _WellKnownEndpoint:
        (rel, media_type) = endpoint.value
        link = find_link(session, rel, media_type, False)
        if link is not None:
            smap[endpoint] = link.href
    return smap


def _response_has_content(response):
    return response.content is not None and len(response.content) > 0


def _objectify_response(response, as_object=True):
    """Convert XML response content to an lxml object.

    :param str response: an XML response as a string.
    :param boolean as_object: If True convert to an
        lxml.objectify.ObjectifiedElement where XML properties look like
        python object attributes.

    :return: lxml.objectify.ObjectifiedElement or xml.etree.ElementTree object.

    :rtype: lxml.objectify.ObjectifiedElement
    """
    if _response_has_content(response):
        if as_object:
            return objectify.fromstring(response.content)
        else:
            return etree.fromstring(response.content)
    else:
        return None


class TaskStatus(Enum):
    QUEUED = 'queued'
    PRE_RUNNING = 'preRunning'
    RUNNING = 'running'
    SUCCESS = 'success'
    ERROR = 'error'
    CANCELED = 'canceled'
    ABORTED = 'aborted'


class GatewayBackingConfigType(Enum):
    COMPACT = 'compact'
    FULL = 'full'
    FULL4 = 'full4'
    XLARGE = 'x-large'


class VAppPowerStatus(Enum):
    RUNNING = '4'
    STOPPED = '8'
    SUSPENDED = '3'
    DEPLOYED = '2'
    UNDEPLOYED = '1'


class _TaskMonitor(object):
    _DEFAULT_POLL_SEC = 5
    _DEFAULT_TIMEOUT_SEC = 600

    def __init__(self, client):
        self._client = client

    def wait_for_success(self,
                         task,
                         timeout=_DEFAULT_TIMEOUT_SEC,
                         poll_frequency=_DEFAULT_POLL_SEC,
                         callback=None):
        return self.wait_for_status(
            task,
            timeout,
            poll_frequency, [TaskStatus.ERROR], [TaskStatus.SUCCESS],
            callback=callback)

    def wait_for_status(self,
                        task,
                        timeout=_DEFAULT_TIMEOUT_SEC,
                        poll_frequency=_DEFAULT_POLL_SEC,
                        fail_on_statuses=[
                            TaskStatus.ABORTED, TaskStatus.CANCELED,
                            TaskStatus.ERROR
                        ],
                        expected_target_statuses=[TaskStatus.SUCCESS],
                        callback=None):
        """Waits for task to reach expected status.

        :param Task task: Task returned by post or put calls.
        :param float timeout: Time (in seconds, floating point, fractional)
            to wait for task to finish.
        :param float poll_frequency: time (in seconds, as above) with which
            task will be polled.
        :param list fail_on_statuses: method will raise an exception if any
            of the TaskStatus in this list is reached. If this parameter is
            None then either task will achieve expected target status or throw
            TimeOutException.
        :param list expected_target_statuses: list of expected target
            status.
        :return: Task we were waiting for
        :rtype Task:
        :raises TimeoutException: If task is not finished within given time.
        :raises VcdException: If task enters a status in fail_on_statuses list
        """
        if fail_on_statuses is None:
            _fail_on_statuses = []
        elif isinstance(fail_on_statuses, TaskStatus):
            _fail_on_statuses[fail_on_statuses]
        else:
            _fail_on_statuses = fail_on_statuses
        task_href = task.get('href')
        start_time = datetime.now()
        while True:
            task = self._get_task_status(task_href)
            if callback is not None:
                callback(task)
            task_status = task.get('status').lower()
            for status in expected_target_statuses:
                if task_status == status.value.lower():
                    return task
            for status in _fail_on_statuses:
                if task_status == status.value.lower():
                    raise VcdTaskException(task_status, task.Error)
            if start_time - datetime.now() > timedelta(seconds=timeout):
                break
            time.sleep(poll_frequency)
        raise TaskTimeoutException("Task timeout")

    def _get_task_status(self, task_href):
        return self._client.get_resource(task_href)

    def get_status(self, task):
        return self._get_task_status(task.get('href')).get('status').lower()


class Client(object):
    """A low-level interface to the vCloud Director REST API.

    Clients default to the production vCD API version as of the pyvcloud
    module release and will try to negotiate down to a lower API version
    that pyvcloud certifies if the vCD server is older. You can also set
    the version explicitly using the api_version parameter or by calling
    the set_highest_supported_version() method.

    The log_file is set by the first client instantiated and will be
    ignored in later clients.

    :param str uri: vCD server host name or connection URI.
    :param str api_version: vCD API version to use.
    :param boolean verify_ssl_certs: If True validate server certificate;
        False allows self-signed certificates.
    :param str log_file: log file name or None, which suppresses logging.
    :param boolean log_request: if True log HTTP requests.
    :param boolean log_headers: if True log HTTP headers.
    :param boolean log_bodies: if True log HTTP bodies.
    """

    _HEADER_ACCEPT_NAME = 'Accept'
    _HEADER_CONNECTION_NAME = 'Connection'
    _HEADER_CONTENT_LENGTH_NAME = 'Content-Length'
    _HEADER_CONTENT_RANGE_NAME = 'Content-Range'
    _HEADER_CONTENT_TYPE_NAME = 'Content-Type'
    _HEADER_REQUEST_ID_NAME = 'X-VMWARE-VCLOUD-REQUEST-ID'
    _HEADER_X_VCLOUD_AUTH_NAME = 'x-vcloud-authorization'

    _HEADER_CONNECTION_VALUE_CLOSE = 'close'

    _UPLOAD_FRAGMENT_MAX_RETRIES = 5

    def __init__(self,
                 uri,
                 api_version=None,
                 verify_ssl_certs=True,
                 log_file=None,
                 log_requests=False,
                 log_headers=False,
                 log_bodies=False):
        self._uri = uri
        if len(self._uri) > 0:
            if self._uri[-1] == '/':
                self._uri += 'api'
            else:
                self._uri += '/api'
            if self._uri.startswith('https://') or self._uri.startswith(
                    'http://'):
                pass
            else:
                self._uri = 'https://' + self._uri

        # If user provides API version we accept it, otherwise use default
        # and set negotiation flag.
        if api_version is None:
            self._api_version = API_CURRENT_VERSIONS[-1]
            self._negotiate_api_version = True
        else:
            self._api_version = api_version
            self._negotiate_api_version = False

        self._session_endpoints = None
        self._session = None
        self._query_list_map = None
        self._task_monitor = None
        self._verify_ssl_certs = verify_ssl_certs

        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        # This makes sure that we don't append a new handler to the logger
        # every time we create a new client.
        if not self._logger.handlers:
            if log_file is not None:
                handler = logging.FileHandler(log_file)
            else:
                handler = logging.NullHandler()
            formatter = logging.Formatter('%(asctime)-23.23s | '
                                          '%(levelname)-5.5s | '
                                          '%(name)-15.15s | '
                                          '%(module)-15.15s | '
                                          '%(funcName)-12.12s | '
                                          '%(message)s')
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

        self._log_requests = log_requests
        self._log_headers = log_headers
        self._log_bodies = log_bodies

        self.fsencoding = sys.getfilesystemencoding()

        self._is_sysadmin = False

    def _get_response_request_id(self, response):
        """Extract request id of a request to vCD from the response.

        :param requests.Response response: response from vCD.

        :return: the request id.

        :rtype: str
        """
        return response.headers[self._HEADER_REQUEST_ID_NAME]

    def is_connection_closed(self, response):
        """Determine from server response if the connection has been closed.

        :param requests.Response response: the response received from server
            for the last REST call.

        :return: True, if the response from server indicates that the
            connection has been closed, else False.

        :rtype: boolean
        """
        if response is None:
            return False

        if self._HEADER_CONNECTION_NAME in response.headers:
            if response.headers[self._HEADER_CONNECTION_NAME].lower() == \
               self._HEADER_CONNECTION_VALUE_CLOSE.lower():
                return True

        return False

    def get_api_version(self):
        """Return vCD API version client is using.

        :return: api version of the client.

        :rtype: str
        """
        return self._api_version

    def get_supported_versions_list(self):
        """Return non-deprecated server API versions as a list.

        :return: versions as strings, sorted in numerical order.

        :rtype: list
        """
        versions = self.get_supported_versions()
        active_versions = []
        for version in versions.VersionInfo:
            # Versions must be explicitly assigned as text values using the
            # .text property. Otherwise lxml will return "corrected" numbers
            # that drop non-significant digits. For example, 5.10 becomes
            # 5.1.  This transformation corrupts the version.
            if not hasattr(version, 'deprecated') or \
               version.get('deprecated') == 'false':
                active_versions.append(str(version.Version.text))
        active_versions.sort(key=StrictVersion)
        return active_versions

    def get_supported_versions(self):
        """Return non-deprecated API versions on vCD server.

        :return: an object containing SupportedVersions XML element which
            represents versions supported by vCD.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        with requests.Session() as new_session:
            # Use with block to avoid leaking socket connections.
            response = self._do_request_prim(
                'GET', self._uri + '/versions', new_session, accept_type='')
            sc = response.status_code
            if sc != 200:
                raise VcdException('Unable to get supported API versions.')
            return objectify.fromstring(response.content)

    def set_highest_supported_version(self):
        """Set the client API version to the highest server API version.

        This call is intended to make it easy to work with new vCD
        features before they are officially supported in pyvcloud.
        Production applications should either use the default pyvcloud API
        version or set the API version explicitly to freeze compatibility.

        :return: selected api version.

        :rtype: str
        """
        active_versions = self.get_supported_versions_list()
        self._api_version = active_versions[-1]
        self._negotiate_api_version = False
        self._logger.debug('API versions supported: %s' % active_versions)
        self._logger.debug('API version set to: %s' % self._api_version)
        return self._api_version

    def set_credentials(self, creds):
        """Set credentials and authenticate to create a new session.

        This call will automatically negotiate the server API version if
        it was not set previously. Note that the method may generate
        exceptions from the underlying socket connection, which we pass
        up unchanged to the client.

        :param BasicLoginCredentials creds: Credentials containing org,
            user, and password.

        :raises: VcdException: if automatic API negotiation fails to arrive
            at a supported client version
        """
        # If we need to negotiate the server API level find the highest
        # server version that pyvcloud supports.
        if self._negotiate_api_version:
            self._logger.debug("Negotiating API version")
            active_versions = self.get_supported_versions_list()
            self._logger.debug('API versions supported: %s' % active_versions)
            # Versions are strings sorted in ascending order, so we can work
            # backwards to find a match.
            for version in reversed(active_versions):
                if version in API_CURRENT_VERSIONS:
                    self._api_version = version
                    self._negotiate_api_version = False
                    self._logger.debug(
                        'API version negotiated to: %s' % self._api_version)
                    break

            # Still need to negotiate?  That means we didn't find a
            # suitable version.
            if self._negotiate_api_version:
                raise VcdException(
                    "Unable to find a supported API version in available \
                        server versions: {0}".format(active_versions))

        # We can now proceed to login. Ensure we close session if
        # any exception is thrown to avoid leaking a socket connection.
        self._logger.debug('API version in use: %s' % self._api_version)
        new_session = requests.Session()
        try:
            response = self._do_request_prim(
                'POST',
                self._uri + '/sessions',
                new_session,
                auth=('%s@%s' % (creds.user, creds.org), creds.password))

            sc = response.status_code
            if sc != 200:
                r = None
                try:
                    r = _objectify_response(response)
                except Exception:
                    pass
                if r is not None:
                    self._response_code_to_exception(
                        sc, self._get_response_request_id(response), r)
                else:
                    raise VcdException('Login failed.')

            session = objectify.fromstring(response.content)
            self._session_endpoints = _get_session_endpoints(session)

            self._session = new_session
            self._session.headers[self._HEADER_X_VCLOUD_AUTH_NAME] = \
                response.headers[self._HEADER_X_VCLOUD_AUTH_NAME]
            self._is_sysadmin = self._is_sys_admin(session.get('org'))
        except Exception:
            new_session.close()
            raise

    def rehydrate(self, state):
        self._session = requests.Session()
        self._session.headers[self._HEADER_X_VCLOUD_AUTH_NAME] = \
            state.get('token')
        self._is_sysadmin = self._is_sys_admin(state.get('org'))
        wkep = state.get('wkep')
        self._session_endpoints = {}
        for endpoint in _WellKnownEndpoint:
            if endpoint.name in wkep:
                self._session_endpoints[endpoint] = wkep[endpoint.name]

    def rehydrate_from_token(self, token):
        new_session = requests.Session()
        new_session.headers[self._HEADER_X_VCLOUD_AUTH_NAME] = token
        response = self._do_request_prim('GET', self._uri + "/session",
                                         new_session)
        sc = response.status_code
        if sc != 200:
            self._response_code_to_exception(
                sc, self._get_response_request_id(response),
                _objectify_response(response))

        session = objectify.fromstring(response.content)

        self._is_sysadmin = self._is_sys_admin(session.get('org'))
        self._session_endpoints = _get_session_endpoints(session)
        self._session = new_session
        self._session.headers[self._HEADER_X_VCLOUD_AUTH_NAME] = \
            response.headers[self._HEADER_X_VCLOUD_AUTH_NAME]
        return session

    def logout(self):
        """Destroy the server session and de-allocate local resources.

        Logout is idempotent. Reusing a client after logout will result
        in undefined behavior.
        """
        if self._session is not None:
            uri = self._uri + '/session'
            result = self._do_request('DELETE', uri)
            self._session.close()
            self._session = None
            return result

    def _is_sys_admin(self, logged_in_org):
        if logged_in_org.lower() == 'system':
            return True
        return False

    def is_sysadmin(self):
        return self._is_sysadmin

    def get_api_uri(self):
        return self._uri

    def get_task_monitor(self):
        if self._task_monitor is None:
            self._task_monitor = _TaskMonitor(self)
        return self._task_monitor

    def _do_request(self,
                    method,
                    uri,
                    contents=None,
                    media_type=None,
                    objectify_results=True):
        response = self._do_request_prim(
            method,
            uri,
            self._session,
            contents=contents,
            media_type=media_type)

        sc = response.status_code
        if 200 <= sc <= 299:
            return _objectify_response(response, objectify_results)

        self._response_code_to_exception(
            sc, self._get_response_request_id(response),
            _objectify_response(response, objectify_results))

    @staticmethod
    def _response_code_to_exception(sc, request_id, objectify_response):
        if sc == 400:
            raise BadRequestException(sc, request_id, objectify_response)

        if sc == 401:
            raise UnauthorizedException(sc, request_id, objectify_response)

        if sc == 403:
            raise AccessForbiddenException(sc, request_id, objectify_response)

        if sc == 404:
            raise NotFoundException(sc, request_id, objectify_response)

        if sc == 405:
            raise MethodNotAllowedException(sc, request_id, objectify_response)

        if sc == 406:
            raise NotAcceptableException(sc, request_id, objectify_response)

        if sc == 408:
            raise RequestTimeoutException(sc, request_id, objectify_response)

        if sc == 409:
            raise ConflictException(sc, request_id, objectify_response)

        if sc == 415:
            raise UnsupportedMediaTypeException(sc, request_id,
                                                objectify_response)

        if sc == 416:
            raise InvalidContentLengthException(sc, request_id,
                                                objectify_response)

        if sc == 500:
            raise InternalServerException(sc, request_id, objectify_response)

        raise UnknownApiException(sc, request_id, objectify_response)

    def _log_request_response(self,
                              response,
                              request_body=None,
                              skip_logging_response_body=False):
        if not self._log_requests:
            return

        self._logger.debug('Request uri (%s): %s' % (response.request.method,
                                                     response.request.url))

        if self._log_headers:
            self._logger.debug(
                'Request headers: %s' % response.request.headers)

        if self._log_bodies and request_body is not None:
            if isinstance(request_body, str):
                body = request_body
            else:
                body = request_body.decode(self.fsencoding)
            self._logger.debug('Request body: %s' % body)

        self._logger.debug('Response status code: %s' % response.status_code)

        if self._log_headers:
            self._logger.debug('Response headers: %s' % response.headers)

        if self._log_bodies and not skip_logging_response_body and \
           _response_has_content(response):
            if isinstance(response.content, str):
                response_body = response.content
            else:
                response_body = response.content.decode(self.fsencoding)
            self._logger.debug('Response body: %s' % response_body)

    def _do_request_prim(self,
                         method,
                         uri,
                         session,
                         contents=None,
                         media_type=None,
                         accept_type=None,
                         auth=None):
        headers = {}
        if media_type is not None:
            headers[self._HEADER_CONTENT_TYPE_NAME] = media_type
        headers[self._HEADER_ACCEPT_NAME] = '%s;version=%s' % \
            ('application/*+xml' if accept_type is None else accept_type,
             self._api_version)

        if contents is None:
            data = None
        else:
            if isinstance(contents, dict):
                data = json.dumps(contents)
            else:
                data = etree.tostring(contents)

        response = session.request(
            method,
            uri,
            data=data,
            headers=headers,
            auth=auth,
            verify=self._verify_ssl_certs)

        self._log_request_response(response=response, request_body=data)

        return response

    def upload_fragment(self, uri, contents, range_str):
        headers = {}
        headers[self._HEADER_CONTENT_RANGE_NAME] = range_str
        headers[self._HEADER_CONTENT_LENGTH_NAME] = str(len(contents))
        data = contents

        # If we pump data too fast, server can reply back with statuses other
        # than 200 e.g. 416. As counter measure, on receiving non 200 status,
        # we will retry the upload for a fixed number of times. If all the
        # retry efforts fail, we will fail the upload completely and return.
        for attempt in range(1, self._UPLOAD_FRAGMENT_MAX_RETRIES + 1):
            try:
                response = self._session.put(
                    uri,
                    data=data,
                    headers=headers,
                    verify=self._verify_ssl_certs)
                self._log_request_response(response)

                sc = response.status_code
                if sc != 200:
                    self._response_code_to_exception(sc, None, response)
                else:
                    return response
            except VcdResponseException:
                # retry if not the last attempt
                if attempt < self._UPLOAD_FRAGMENT_MAX_RETRIES:
                    self._logger.debug(
                        'Failure: attempt#%s to upload data in '
                        'range %s failed. Retrying.' % (attempt, range_str))
                    continue
                else:
                    self._logger.error(
                        'Reached max retry limit. Failing upload.')
                    raise

    def download_from_uri(self,
                          uri,
                          file_name,
                          chunk_size=SIZE_1MB,
                          size=0,
                          callback=None):

        response = self._session.get(
            uri, stream=True, verify=self._verify_ssl_certs)
        self._log_request_response(response, skip_logging_response_body=True)

        sc = response.status_code
        if sc != 200:
            self._response_code_to_exception(sc, None, response)

        bytes_written = 0
        with open(file_name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    bytes_written += len(chunk)
                    if callback is not None:
                        callback(bytes_written, size)
                    self._logger.debug('Downloaded bytes : %s' % bytes_written)
        return bytes_written

    def put_resource(self, uri, contents, media_type, objectify_results=True):
        """Puts the specified contents to the specified resource.

        This method does an HTTP PUT.
        """
        return self._do_request(
            'PUT',
            uri,
            contents=contents,
            media_type=media_type,
            objectify_results=objectify_results)

    def put_linked_resource(self, resource, rel, media_type, contents):
        """Puts to a resource link.

        Puts the contents of the resource referenced by the link with the
        specified rel and mediaType in the specified resource.

        :return: the result of the PUT operation.

        :raises: OperationNotSupportedException: if the operation fails due to
            the link being not visible to the logged in user of the client.
        """
        try:
            return self.put_resource(
                find_link(resource, rel, media_type).href, contents,
                media_type)
        except MissingLinkException as e:
            raise OperationNotSupportedException from e

    def post_resource(self, uri, contents, media_type, objectify_results=True):
        """Posts to a resource link.

        Posts the specified contents to the specified resource. (Does an HTTP
        POST.)
        """
        return self._do_request(
            'POST',
            uri,
            contents=contents,
            media_type=media_type,
            objectify_results=objectify_results)

    def post_linked_resource(self, resource, rel, media_type, contents):
        """Posts to a resource link.

        Posts the contents of the resource referenced by the link with the
        specified rel and mediaType in the specified resource.

        :return: the result of the POST operation.

        :raises: OperationNotSupportedException: if the operation fails due to
            the link being not visible to the logged in user of the client.
        """
        try:
            return self.post_resource(
                find_link(resource, rel, media_type).href, contents,
                media_type)
        except MissingLinkException as e:
            raise OperationNotSupportedException(
                "Operation is not supported").with_traceback(e.__traceback__)

    def get_resource(self, uri, objectify_results=True):
        """Gets the specified contents to the specified resource.

        This method does an HTTP GET.
        """
        return self._do_request(
            'GET', uri, objectify_results=objectify_results)

    def get_linked_resource(self, resource, rel, media_type):
        """Gets the content of the resource link.

        Gets the contents of the resource referenced by the link with the
        specified rel and mediaType in the specified resource.

        :return: an object containing XML representation of the resource the
            link points to.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: OperationNotSupportedException: if the operation fails due to
            the link being not visible to the logged in user of the client.
        """
        try:
            return self.get_resource(find_link(resource, rel, media_type).href)
        except MissingLinkException as e:
            raise OperationNotSupportedException(
                "Operation is not supported").with_traceback(e.__traceback__)

    def delete_resource(self, uri, force=False, recursive=False):
        full_uri = '%s?force=%s&recursive=%s' % (uri, force, recursive)
        return self._do_request('DELETE', full_uri)

    def delete_linked_resource(self, resource, rel, media_type):
        """Deletes the resource referenced by the link.

        Deletes the resource referenced by the link with the specified rel and
        mediaType in the specified resource.

        :raises: OperationNotSupportedException: if the operation fails due to
            the link being not visible to the logged in user of the client.
        """
        try:
            return self.delete_resource(
                find_link(resource, rel, media_type).href)
        except MissingLinkException as e:
            raise OperationNotSupportedException(
                "Operation is not supported").with_traceback(e.__traceback__)

    def get_admin(self):
        """Returns the "admin" root resource type."""
        return self._get_wk_resource(_WellKnownEndpoint.ADMIN)

    def get_query_list(self):
        """Returns the list of supported queries."""
        return self._get_wk_resource(_WellKnownEndpoint.QUERY_LIST)

    def get_org(self):
        """Returns the logged in org.

        :return: a sparse representation of the logged in org. The returned
            object has an 'Org' XML element with 'name', 'href', and 'type'
            attribute.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self._get_wk_resource(_WellKnownEndpoint.LOGGED_IN_ORG)

    def get_extensibility(self):
        """Returns the 'extensibility' resource type."""
        return self._get_wk_resource(_WellKnownEndpoint.API_EXTENSIBILITY)

    def get_extension(self):
        """Returns the 'extension' resource type."""
        return self._get_wk_resource(_WellKnownEndpoint.EXTENSION)

    def get_org_list(self):
        """Returns the list of organizations visible to the user.

        :return: a list of objects, where each object contains EntityType.ORG
            XML data which represents a single organization.

        :rtype: list
        """
        orgs = self._get_wk_resource(_WellKnownEndpoint.ORG_LIST)
        result = []
        if hasattr(orgs, 'Org'):
            for org in orgs.Org:
                org_resource = self.get_resource(org.get('href'))
                result.append(org_resource)
        return result

    def get_org_by_name(self, org_name):
        """Retrieve an organization.

        :param str org_name: name of the organization to be retrieved.

        :return: object containing EntityType.ORG XML data representing the
            organization.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if organization with the provided
            name couldn't be found.
        """
        # Avoid using get_org_list() to fetch all orgs and then filter the
        # result by organization name, since get_org_list() will fetch details
        # of all the organizations before filtering, it's expensive. In the
        # following implementation, we delay the REST call to fetch
        # organization details until we have narrowed down our target to
        # exactly 1 organization.
        orgs = self._get_wk_resource(_WellKnownEndpoint.ORG_LIST)
        if hasattr(orgs, 'Org'):
            for org in orgs.Org:
                if org.get('name').lower() == org_name.lower():
                    return self.get_resource(org.get('href'))
        raise EntityNotFoundException('org \'%s\' not found' % org_name)

    def get_user_in_org(self, user_name, org_href):
        """Retrieve user from a particular organization.

        :param str user_name: name of the user to be retrieved.
        :param str org_href: href of the organization to which the user
            belongs.

        :return: an object containing EntityType.USER XML data which respresnts
            an user in vCD.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        resource_type = ResourceType.USER.value
        org_filter = None
        if self.is_sysadmin():
            resource_type = ResourceType.ADMIN_USER.value
            org_filter = 'org==%s' % urllib.parse.quote_plus(org_href)
        query = self.get_typed_query(
            resource_type,
            query_result_format=QueryResultFormat.REFERENCES,
            equality_filter=('name', user_name),
            qfilter=org_filter)
        records = list(query.execute())
        if len(records) == 0:
            raise EntityNotFoundException('user \'%s\' not found' % user_name)
        elif len(records) > 1:
            raise MultipleRecordsException('multiple users found')
        return self.get_resource(records[0].get('href'))

    def _get_query_list_map(self):
        if self._query_list_map is None:
            self._query_list_map = {}
            for link in self.get_query_list().Link:
                self._query_list_map[(link.get('type'),
                                      link.get('name'))] = link.get('href')
        return self._query_list_map

    def get_typed_query(self,
                        query_type_name,
                        query_result_format=QueryResultFormat.REFERENCES,
                        page_size=None,
                        include_links=False,
                        qfilter=None,
                        equality_filter=None,
                        sort_asc=None,
                        sort_desc=None,
                        fields=None):
        """Issue a typed query using vCD query API.

        :param str query_type_name: name of the entity, which should be a
            string listed in ResourceType enum values.
        :param QueryResultFormat query_result_format: format of query result.
        :param int page_size: number of entries per page.
        :param include_links: (not used).
        :param str qfilter: filter expression for the query. Is normally made
            up of sub expressions, where each sub-expression is of the form
            <filter name><operator><value>. Few of the allowed operators are
            == for equality, =lt= for less than, =gt= for greater than etc.
            Multiple sub expression can be joined using logical AND i.e. ;
            logical OR i.e. , etc. Each value in query string must be
            url-encoded. E.g. 'numberOfCpus=gt=4' , 'name==abc%20def'.
        :param tuple equality_filter: a special filter that will be logically
            AND-ed to qfilter, with the operator being ==. The first element in
            the tuple is treated as filter name, while the second element is
            treated as value. There is no need to url-encode the value in this
            case.
        :param str sort_asc: if 'name' field is present in the result sort
            ascending by that field.
        :param str sort_desc: if 'name' field is present in the result sort
            descending by that field.
        :param str fields: comma separated list of fields to return.

        :return: A query object that runs the query when execute()
            method is called.

        :rtype: pyvcloud.vcd.client._TypedQuery
        """
        return _TypedQuery(
            query_type_name,
            self,
            query_result_format,
            page_size=page_size,
            include_links=include_links,
            qfilter=qfilter,
            equality_filter=equality_filter,
            sort_asc=sort_asc,
            sort_desc=sort_desc,
            fields=fields)

    def _get_wk_resource(self, wk_type):
        return self.get_resource(self._get_wk_endpoint(wk_type))

    def _get_wk_endpoint(self, wk_type):
        if wk_type in self._session_endpoints:
            return self._session_endpoints[wk_type]
        else:
            raise ClientException(
                'The current user does not have access to the resource (%s).' %
                str(wk_type).split('.')[-1])


def find_link(resource, rel, media_type, fail_if_absent=True):
    """Returns the link of the specified rel and type in the resource.

    :param lxml.objectify.ObjectifiedElement resource: the resource with the
        link.
    :param ResourceType rel: the rel of the desired link.
    :param str media_type: media type of content.
    :param bool fail_if_absent: if True raise an exception if there's
        not exactly one link of the specified rel and media type.

    :return: an object containing Link XML element representing the desired
        link or None if no such link is present and fail_if_absent is False.

    :rtype: lxml.objectify.ObjectifiedElement

    :raises MissingLinkException: if no link of the specified rel and media
        type is found
    :raises MultipleLinksException: if multiple links of the specified rel
        and media type are found
    """
    links = get_links(resource, rel, media_type)
    num_links = len(links)
    if num_links == 0:
        if fail_if_absent:
            raise MissingLinkException(resource.get('href'), rel, media_type)
        else:
            return None
    elif num_links == 1:
        return links[0]
    else:
        raise MultipleLinksException(resource.get('href'), rel, media_type)


def get_links(resource, rel=RelationType.DOWN, media_type=None):
    """Returns all the links of the specified rel and type in the resource.

    :param lxml.objectify.ObjectifiedElement resource: the resource with the
        links.
    :param RelationType rel: the rel of the desired link.
    :param str media_type: media type of content.

    :return: list of lxml.objectify.ObjectifiedElement objects, where each
        object contains a Link XML element. Result could include an empty list.

    :rtype: list
    """
    links = []
    for link in resource.findall('{http://www.vmware.com/vcloud/v1.5}Link'):
        link_rel = link.get('rel')
        link_media_type = link.get('type')
        if link_rel == rel.value:
            if media_type is None and link_media_type is None:
                links.append(Link(link))
            elif media_type is not None and \
                    link_media_type == media_type:
                links.append(Link(link))
    return links


class Link(object):
    """Abstraction over <Link> elements."""

    def __init__(self, link_elem):
        self.rel = link_elem.get('rel')
        self.media_type = link_elem.get('type')
        self.href = link_elem.get('href')
        self.name = link_elem.get('name') \
            if 'name' in link_elem.attrib else None


class _AbstractQuery(object):
    """Implements internal query object representation."""

    def __init__(self,
                 query_result_format,
                 client,
                 page_size=None,
                 include_links=False,
                 qfilter=None,
                 equality_filter=None,
                 sort_asc=None,
                 sort_desc=None,
                 fields=None):
        """Constructor for _AbstractQuery object.

        :param QueryResultFormat query_result_format: format of query result.
        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param int page_size:
        :param bool include_links: if True, query result will include links in
            the body.
        :param str qfilter: filter expression for the query. The values in the
            query string must be url-encoded.
        :param tuple equality_filter: a special filter that will be logically
            AND-ed to query filter. The first element in the tuple is treated
            as key, while the second element is treated as value. There is no
            need to url-encode the value, this function will do that the final
            query url is constructed.
        :param str sort_asc: sort results by attribute-name in ascending order.
            attribute-name cannot include metadata.
        :param str sort_desc: sort results by attribute-name in descending
            order. attribute-name cannot include metadata.
        :param str fields: comma-separated list of attribute names or metadata
            key names to return
        """
        self._client = client
        self._query_result_format = query_result_format
        self._page_size = page_size
        self._include_links = include_links
        self._page = 1

        self._filter = qfilter
        if equality_filter is not None:
            if self._filter is not None:
                self._filter += ';'
            else:
                self._filter = ''
            self._filter += equality_filter[0]
            self._filter += '=='
            self._filter += urllib.parse.quote(equality_filter[1])

        self._sort_desc = sort_desc
        self._sort_asc = sort_asc

        self.fields = fields

    def execute(self):
        """Executes query and returns results.

        :return: A generator to returns results.

        :rtype: generator object
        """
        query_href = self._find_query_uri(self._query_result_format)
        if query_href is None:
            raise OperationNotSupportedException('Unable to execute query.')
        query_uri = self._build_query_uri(
            query_href,
            self._page,
            self._page_size,
            self._filter,
            self._include_links,
            fields=self.fields)
        return self._iterator(self._client.get_resource(query_uri))

    def _iterator(self, query_results):
        while True:
            next_page_uri = None
            for r in query_results.iterchildren():
                tag = etree.QName(r.tag)
                if tag.localname == 'Link':
                    if r.get('rel') == RelationType.NEXT_PAGE.value:
                        next_page_uri = r.get('href')
                else:
                    yield r
            if next_page_uri is None:
                break
            query_results = self._client.get_resource(
                next_page_uri, objectify_results=True)

    def find_unique(self):
        """Convenience wrapper over execute().

        Convenience wrapper over execute() for the case where exactly one match
        is expected.
        """
        query_results = self.execute()

        # Make sure we got at least one result record
        try:
            item = next(query_results)
        except StopIteration:
            raise MissingRecordException()

        # Make sure we didn't get more than one result record
        try:
            next(query_results)
            raise MultipleRecordsException()
        except StopIteration:
            pass

        return item

    def _build_query_uri(self,
                         base_query_href,
                         page,
                         page_size,
                         qfilter,
                         include_links,
                         fields=None):
        uri = base_query_href
        uri += '&page='
        uri += str(page)

        if (page_size is not None):
            uri += 'pageSize='
            uri += str(page_size)

        if qfilter is not None:
            # filterEncoded=true directs vCD to decode the individual filter
            # values, i.e. the value after each ==.
            uri += '&filterEncoded=true&filter='
            # Need to encode the value of filter param again to escape special
            # characters like ',', ';' which have special meaning in context of
            # query filter.
            uri += urllib.parse.quote(qfilter)

        if fields is not None:
            uri += '&fields='
            uri += fields

        if self._sort_asc is not None:
            uri += '&sortAsc='
            uri += self._sort_asc

        if self._sort_desc is not None:
            uri += '&sortDesc='
            uri += self._sort_desc

        return uri


class _TypedQuery(_AbstractQuery):
    def __init__(self,
                 query_type_name,
                 client,
                 query_result_format,
                 page_size=None,
                 include_links=False,
                 qfilter=None,
                 equality_filter=None,
                 sort_asc=None,
                 sort_desc=None,
                 fields=None):
        super(_TypedQuery, self).__init__(
            query_result_format,
            client,
            page_size=page_size,
            include_links=include_links,
            qfilter=qfilter,
            equality_filter=equality_filter,
            sort_asc=sort_asc,
            sort_desc=sort_desc,
            fields=fields)
        self._query_type_name = query_type_name

    def _find_query_uri(self, query_result_format):
        (query_media_type, _) = query_result_format.value
        query_href = \
            self. \
            _client. \
            _get_query_list_map().get(
                (query_media_type, self._query_type_name))
        if query_href is None:
            self._client._logger.warning(
                'Unable to locate query href for \'%s\' typed query.' %
                self._query_type_name)
        return query_href


def create_element(node_name, value=None):
    """Creates Objectify Element.

    It is useful in the use case where one wants to add ObjectifiedElement to
    either StringElement or to the BooleanElement e.g:

    <dhcp><enable>false</enable><ippools/></dhcp>

    Here:<ippools/> is a StringElement, and user cannot add child element
    <ippool> to <ippools> by using ippools.append(E.ippool(ippool))

    It creates the Objectify element with provided value and this element can
    be appended with StringElement or BooleanElement

    :param node_name: name of the node
    :param value: value of the node
    :return: Objectify element with given value
    :type: ObjectifyElement

    """
    if value is None:
        return etree.Element(node_name)
    if isinstance(value, bool):
        if value is True:
            value = 'true'
        elif value is False:
            value = 'false'
    if not isinstance(value, str):
        value = str(value)
    element = etree.Element(node_name)
    element.text = value
    return element
