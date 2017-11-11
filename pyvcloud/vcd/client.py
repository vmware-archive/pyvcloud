# VMware vCloud Director Python SDK
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
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
from flufl.enum import Enum
import json
import logging
from lxml import etree
from lxml import objectify
import requests
import sys
import time
import urllib


SIZE_1MB = 1024*1024


NSMAP = {
         'ovf': 'http://schemas.dmtf.org/ovf/envelope/1',
         'ovfenv': 'http://schemas.dmtf.org/ovf/environment/1',
         'rasd': 'http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData',  # NOQA
         'vcloud': 'http://www.vmware.com/vcloud/v1.5',
         've': 'http://www.vmware.com/schema/ovfenv',
         'vmext': 'http://www.vmware.com/vcloud/extension/v1.5',
         'xs': 'http://www.w3.org/2001/XMLSchema',
         'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
         }


# Convenience objects for building vCloud API XML objects
E = objectify.ElementMaker(
    annotate=False,
    namespace=NSMAP['vcloud'],
    nsmap={None: NSMAP['vcloud'],
           'xsi': NSMAP['xsi'],
           'xs': NSMAP['xs'],
           'ovf': NSMAP['ovf']})

E_VMEXT = objectify.ElementMaker(
    annotate=False,
    namespace=NSMAP['vmext'],
    nsmap={None: NSMAP['vcloud'],
           'vmext': NSMAP['vmext']})

E_OVF = objectify.ElementMaker(
    annotate=False,
    namespace=NSMAP['ovf'],
    nsmap={None: NSMAP['ovf']})

E_RASD = objectify.ElementMaker(
    annotate=False,
    namespace=NSMAP['rasd'],
    nsmap={None: NSMAP['rasd'],
           'vcloud': NSMAP['vcloud']})

RESOURCE_TYPES = [
    'aclRule',
    'adminApiDefinition',
    'adminAllocatedExternalAddress',
    'adminCatalog',
    'adminCatalogItem',
    'adminDisk',
    'adminEvent',
    'adminFileDescriptor',
    'adminGroup',
    'adminMedia',
    'adminOrgNetwork',
    'adminOrgVdc',
    'adminOrgVdcStorageProfile',
    'adminRole',
    'adminService',
    'adminShadowVM',
    'adminTask',
    'adminUser',
    'adminVApp',
    'adminVAppNetwork',
    'adminVAppTemplate',
    'adminVM',
    'adminVMDiskRelation',
    'allocatedExternalAddress',
    'apiDefinition',
    'apiFilter',
    'blockingTask',
    'catalog',
    'catalogItem',
    'cell',
    'condition',
    'datastore',
    'datastoreProviderVdcRelation',
    'disk',
    'dvSwitch',
    'edgeGateway',
    'event',
    'externalLocalization',
    'externalNetwork',
    'fileDescriptor',
    'fromCloudTunnel',
    'group',
    'host',
    'media',
    'networkPool',
    'organization',
    'orgNetwork',
    'orgVdc',
    'orgVdcNetwork',
    'orgVdcResourcePoolRelation',
    'orgVdcStorageProfile',
    'portGroup',
    'providerVdc',
    'providerVdcResourcePoolRelation',
    'providerVdcStorageProfile',
    'resourcePool',
    'resourcePoolVmList',
    'right',
    'resourceClass',
    'resourceClassAction',
    'role',
    'service',
    'serviceLink',
    'serviceResource',
    'strandedItem',
    'strandedUser',
    'task',
    'toCloudTunnel',
    'user',
    'vApp',
    'vAppNetwork',
    'vAppOrgVdcNetworkRelation',
    'vAppTemplate',
    'virtualCenter',
    'vm',
    'vmDiskRelation',
    'vmGroups',
    'vmGroupVms'
    ]

API_CURRENT_VERSIONS = [
    '5.5',
    '5.6',
    '6.0',
    '13.0',
    '17.0',
    '20.0',
    '21.0',
    '22.0',
    '23.0',
    '24.0',
    '25.0',
    '26.0',
    '27.0',
    '28.0',
    '29.0',
    '30.0'
    ]

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
    DOWN = 'down'
    DOWN_EXTENSIBILITY = 'down:extensibility'
    DOWNLOAD_DEFAULT = 'download:default'
    EDIT = 'edit'
    NEXT_PAGE = 'nextPage'
    POWER_OFF = 'power:powerOff'
    POWER_ON = 'power:powerOn'
    POWER_REBOOT = 'power:reboot'
    POWER_RESET = 'power:reset'
    POWER_SHUTDOWN = 'power:shutdown'
    POWER_SUSPEND = 'power:suspend'
    REMOVE = 'remove'
    SNAPSHOT_CREATE = 'snapshot:create'
    SNAPSHOT_REVERT_TO_CURRENT = 'snapshot:revertToCurrent'
    TASK_CANCEL = 'task:cancel'
    UP = 'up'


class EntityType(Enum):
    ADMIN = 'application/vnd.vmware.admin.vcloud+xml'
    ADMIN_CATALOG = 'application/vnd.vmware.admin.catalog+xml'
    ADMIN_SERVICE = 'application/vnd.vmware.admin.service+xml'
    API_EXTENSIBILITY = 'application/vnd.vmware.vcloud.apiextensibility+xml'
    AMQP_SETTINGS = 'application/vnd.vmware.admin.amqpSettings+xml'
    CATALOG = 'application/vnd.vmware.vcloud.catalog+xml'
    CAPTURE_VAPP_PARAMS = \
        'application/vnd.vmware.vcloud.captureVAppParams+xml'
    DISK = 'application/vnd.vmware.vcloud.disk+xml'
    DISK_CREATE_PARMS = 'application/vnd.vmware.vcloud.diskCreateParams+xml'
    EXTENSION = 'application/vnd.vmware.admin.vmwExtension+xml'
    EXTENSION_SERVICES = 'application/vnd.vmware.admin.extensionServices+xml'
    INSTANTIATE_VAPP_TEMPLATE_PARAMS = \
        'application/vnd.vmware.vcloud.instantiateVAppTemplateParams+xml'
    LEASE_SETTINGS = 'application/vnd.vmware.vcloud.leaseSettingsSection+xml'
    MEDIA = 'application/vnd.vmware.vcloud.media+xml'
    METADATA = 'application/vnd.vmware.vcloud.metadata+xml'
    NETWORK_CONFIG_SECTION = \
        'application/vnd.vmware.vcloud.networkConfigSection+xml'
    NETWORK_CONNECTION_SECTION = \
        'application/vnd.vmware.vcloud.networkConnectionSection+xml'
    ORG = 'application/vnd.vmware.vcloud.org+xml'
    ORG_NETWORK = 'application/vnd.vmware.vcloud.orgNetwork+xml'
    ORG_LIST = 'application/vnd.vmware.vcloud.orgList+xml'
    PUBLISH_CATALOG_PARAMS = \
        'application/vnd.vmware.admin.publishCatalogParams+xml'
    QUERY_LIST = 'application/vnd.vmware.vcloud.query.queryList+xml'
    SYSTEM_SETTINGS = 'application/vnd.vmware.admin.systemSettings+xml'
    TASK = 'application/vnd.vmware.vcloud.task+xml'
    TASKS_LIST = 'application/vnd.vmware.vcloud.tasksList+xml'
    TEXT_XML = 'text/xml'
    UPLOAD_VAPP_TEMPLATE_PARAMS = \
        'application/vnd.vmware.vcloud.uploadVAppTemplateParams+xml'
    USER = 'application/vnd.vmware.admin.user+xml'
    VAPP = 'application/vnd.vmware.vcloud.vApp+xml'
    VAPP_TEMPLATE = 'application/vnd.vmware.vcloud.vAppTemplate+xml'
    VDC = 'application/vnd.vmware.vcloud.vdc+xml'


class QueryResultFormat(Enum):
    RECORDS = ('application/vnd.vmware.vcloud.query.records+xml',
               'records')
    ID_RECORDS = ('application/vnd.vmware.vcloud.query.idrecords+xml',
                  'idrecords')
    REFERENCES = ('application/vnd.vmware.vcloud.query.references+xml',
                  'references')


class _WellKnownEndpoint(Enum):
    # ENTITY_RESOLVER = ()
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


class MultipleRecordsException(Exception):
    pass


class MissingRecordException(Exception):
    pass


class LinkException(Exception):
    def __init__(self, href, rel, media_type):
        self.href = href
        self.rel = rel
        self.media_type = media_type

    def __str__(self):
        return '%s; href: %s, rel: %s, mediaType: %s' % \
            (super(LinkException, self).__str__(),
             self.href,
             self.rel,
             self.media_type)


class MultipleLinksException(LinkException):
    def __init__(self, href, rel, media_type):
        super(MultipleLinksException, self).__init__(href, rel, media_type)


class MissingLinkException(LinkException):
    def __init__(self, href, rel, media_type):
        super(MissingLinkException, self).__init__(href, rel, media_type)


class VcdErrorException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


class VcdErrorResponseException(VcdErrorException):
    def __init__(self, status_code, request_id, vcd_error):
        super(VcdErrorResponseException, self).__init__(status_code)
        self.vcd_error = vcd_error
        self.request_id = request_id

    def __str__(self):
        return \
            'VcdErrorResponseException; ' + \
            (('%d: no <Error> in response body' % self.status_code)
                if self.vcd_error is None else
                ('%d/%s: %s' %
                 (self.status_code,
                  self.vcd_error.get('minorErrorCode'),
                  self.vcd_error.get('message')))) + \
            (' (request ID: %s)' % self.request_id)


class VcdTaskException(Exception):
    def __init__(self, error_message, vcd_error):
        self.error_message = error_message
        self.vcd_error = vcd_error

    def __str__(self):
        return \
            'VcdTaskException; %s/%s: %s (%s)' % \
            (self.vcd_error.get('majorErrorCode'),
             self.vcd_error.get('minorErrorCode'),
             self.error_message,
             self.vcd_error.get('message'))


def _get_session_endpoints(session):
    """Build and return a map keyed by well-known endpoints, yielding hrefs, from a <Session>

    """  # NOQA
    smap = {}
    for endpoint in _WellKnownEndpoint:
        (rel, media_type) = endpoint.value
        link = find_link(session, rel, media_type, False)
        if link is not None:
            smap[endpoint] = link.href
    return smap


def _response_has_content(response):
    return response.content is not None and len(response.content) > 0


def _objectify_response(response):
    return objectify.fromstring(response.content) \
        if _response_has_content(response) else None


class TaskStatus(Enum):
    QUEUED = "queued"
    PENDING = "pending"
    PRE_RUNNING = "pre-running"
    RUNNING = "running"
    SUCCESS = "success"
    ABORTED = "aborted"
    ERROR = "error"
    CANCELED = "canceled"


class _TaskMonitor(object):
    _DEFAULT_POLL_SEC = 5

    def __init__(self, client):
        self._client = client

    def wait_for_status(self,
                        task,
                        timeout,
                        poll_frequency,
                        fail_on_status,
                        expected_target_statuses,
                        callback=None):
        """Waits for task to reach expected status.

         * @param task
         *            task returned by post or put calls.
         * @param timeout
         *            time (in seconds, floating point, fractional) to wait for task to finish.
         * @param pollFrequency
         *            time (in seconds, as above) with which task will be polled.
         * @param failOnStatus
         *            task will fail if this {@link TaskStatus} is reached. If this parameter is null then
         *            either task will achieve expected target status or throw {@link TimeOutException}.
         * @param expectedTargetStatus
         *            list of expected alternative target status.
         * @return {@link TaskType} from list of expected target status.
         * @throws TimeoutException
         *             exception thrown when task is not finished within given time.
        """  # NOQA
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
                else:
                    if fail_on_status is not None and \
                       task_status == fail_on_status.value.lower():
                        raise VcdTaskException(
                            'Expected task status "%s" but got "%s"' %
                            (status.value.lower(), task_status), task.Error)

                if start_time - datetime.now() > timedelta(seconds=timeout):
                    break

            time.sleep(poll_frequency)

        raise Exception("Task timeout")  # TODO(clean up)

    def wait_for_success(self,
                         task,
                         timeout,
                         poll_frequency=_DEFAULT_POLL_SEC,
                         callback=None):
        return self.wait_for_status(task,
                                    timeout,
                                    poll_frequency,
                                    TaskStatus.ERROR,
                                    [TaskStatus.SUCCESS],
                                    callback=callback)

    def _get_task_status(self, task_href):
        return self._client.get_resource(task_href)


class Client(object):
    """A low-level interface to the vCloud Director REST API.

    """

    _REQUEST_ID_HDR_NAME = 'X-VMWARE-VCLOUD-REQUEST-ID'

    def __init__(self,
                 uri,
                 api_version='6.0',
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
            if not (self._uri.startswith('https://') or
                    self._uri.startswith('http://')):
                self._uri = 'https://' + self._uri

        self._api_version = api_version
        self._session_endpoints = None
        self._session = None
        self._query_list_map = None
        self._task_monitor = None
        self._verify_ssl_certs = verify_ssl_certs

        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(log_file) if log_file is not None else \
            logging.NullHandler()
        formatter = logging.Formatter(
            '%(asctime)-23.23s | '
            '%(levelname)-5.5s | '
            '%(name)-15.15s | '
            '%(module)-15.15s | '
            '%(funcName)-12.12s | '
            '%(message)s')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

        requests_logger = logging.getLogger("requests.packages.urllib3")
        requests_logger.addHandler(handler)
        requests_logger.setLevel(logging.DEBUG)

        self._log_requests = log_requests
        self._log_headers = log_headers
        self._log_bodies = log_bodies

        self.fsencoding = sys.getfilesystemencoding()

    def _get_response_request_id(self, response):
        return response.headers[self._REQUEST_ID_HDR_NAME]

    def get_supported_versions(self):
        new_session = requests.Session()
        response = self._do_request_prim('GET',
                                         self._uri + '/versions',
                                         new_session,
                                         accept_type='')
        sc = response.status_code
        if sc != 200:
            raise Exception('Unable to get supported API versions.')
        return objectify.fromstring(response.content)

    def set_highest_supported_version(self):
        versions = self.get_supported_versions()
        active_versions = []
        for version in versions.VersionInfo:
            if not hasattr(version, 'deprecated') or \
               version.get('deprecated') == 'false':
                active_versions.append(float(version.Version))
        active_versions.sort()
        self._api_version = active_versions[-1]
        self._logger.debug('API versions supported: %s' % active_versions)
        self._logger.debug('API version set to highest supported: %s' %
                           self._api_version)
        return self._api_version

    def set_credentials(self, creds):
        """Sets the credentials used for authentication.

        """
        new_session = requests.Session()
        response = self._do_request_prim('POST',
                                         self._uri + '/sessions',
                                         new_session,
                                         auth=('%s@%s' % (creds.user,
                                                          creds.org),
                                               creds.password))
        sc = response.status_code
        if sc != 200:
            r = None
            try:
                r = _objectify_response(response)
            except Exception:
                pass
            raise VcdErrorResponseException(
                sc,
                self._get_response_request_id(response),
                r) if r is not None else \
                Exception("Unknown login failure")

        session = objectify.fromstring(response.content)
        self._session_endpoints = _get_session_endpoints(session)

        self._session = new_session
        self._session.headers['x-vcloud-authorization'] = \
            response.headers['x-vcloud-authorization']

    def rehydrate(self, state):
        self._session = requests.Session()
        self._session.headers['x-vcloud-authorization'] = state.get('token')
        wkep = state.get('wkep')
        self._session_endpoints = {}
        for endpoint in _WellKnownEndpoint:
            if endpoint.name in wkep:
                self._session_endpoints[endpoint] = wkep[endpoint.name]

    def rehydrate_from_token(self, token):
        new_session = requests.Session()
        new_session.headers['x-vcloud-authorization'] = token
        new_session.headers['Accept'] = 'application/*+xml;version=%s' % \
            self._api_version
        response = self._do_request_prim('GET',
                                         self._uri + "/session",
                                         new_session)
        sc = response.status_code
        if sc != 200:
            raise VcdErrorResponseException(
                sc,
                self._get_response_request_id(response),
                _objectify_response(response)) if sc == 401 else \
                Exception("Unknown login failure")

        session = objectify.fromstring(response.content)
        self._session_endpoints = _get_session_endpoints(session)
        self._session = new_session
        self._session.headers['x-vcloud-authorization'] = \
            response.headers['x-vcloud-authorization']
        return session

    def logout(self):
        uri = self._uri + '/session'
        return self._do_request('DELETE', uri)

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
                    accept_type=None,
                    objectify_results=True):
        response = self._do_request_prim(method,
                                         uri,
                                         self._session,
                                         contents=contents,
                                         media_type=media_type)
        sc = response.status_code

        if 200 <= sc <= 299:
            return _objectify_response(response) if objectify_results else \
                etree.fromstring(response.content)

        if 400 <= sc <= 499:
            raise VcdErrorResponseException(
                sc,
                self._get_response_request_id(response),
                objectify.fromstring(response.content))

        raise Exception("Unsupported HTTP status code (%d) encountered" % sc)

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
            headers['Content-Type'] = media_type
        headers['Accept'] = '%s;version=%s' % \
            ('application/*+xml' if accept_type is None else accept_type,
             self._api_version)

        if contents is None:
            data = None
        else:
            if isinstance(contents, dict):
                data = json.dumps(contents)
            else:
                data = etree.tostring(contents)

        response = session.request(method,
                                   uri,
                                   data=data,
                                   headers=headers,
                                   auth=auth,
                                   verify=self._verify_ssl_certs)

        if self._log_requests or self._log_headers or self._log_bodies:
            self._logger.debug('Request uri (%s): %s' % (method, uri))
        if self._log_headers:
            self._logger.debug('Request headers: %s, %s' %
                               (session.headers, headers))
        if self._log_bodies and data is not None:
            if sys.version_info[0] < 3:
                d = data
            else:
                if isinstance(data, str):
                    d = data
                else:
                    d = data.decode(self.fsencoding)
            self._logger.debug('Request body: %s' % d)
        if self._log_requests or self._log_headers or self._log_bodies:
            self._logger.debug('Response status code: %s' %
                               response.status_code)
        if self._log_headers:
            self._logger.debug('Response headers: %s' %
                               response.headers)
        if self._log_bodies and _response_has_content(response):
            if sys.version_info[0] < 3:
                d = response.content
            else:
                if isinstance(response.content, str):
                    d = response.content
                else:
                    d = response.content.decode(self.fsencoding)
            self._logger.debug('Response body: %s' % d)
        return response

    def upload_fragment(self, uri, contents, range_str):
        headers = {}
        headers['Content-Range'] = range_str
        headers['Content-Length'] = str(len(contents))
        data = contents
        response = self._session.request('PUT',
                                         uri,
                                         data=data,
                                         headers=headers,
                                         verify=self._verify_ssl_certs)
        if self._log_headers or self._log_bodies:
            self._logger.debug('Request uri: %s' % uri)
        if self._log_headers:
            self._logger.debug('Request headers: %s, %s' %
                               (self._session.headers,
                                headers))
        if self._log_headers:
            self._logger.debug('Response status code: %s' %
                               response.status_code)
            self._logger.debug('Response headers: %s' %
                               response.headers)
        if self._log_bodies and _response_has_content(response):
            self._logger.debug('Response body: %s' %
                               response.content)
        return response

    def download_from_uri(self,
                          uri,
                          file_name,
                          chunk_size=SIZE_1MB,
                          size=0,
                          callback=None):
        response = self._session.request('GET',
                                         uri,
                                         stream=True,
                                         verify=self._verify_ssl_certs)
        bytes_written = 0
        with open(file_name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    bytes_written += len(chunk)
                    if callback is not None:
                        callback(bytes_written, size)
                    if self._log_headers or self._log_bodies:
                        self._logger.debug('Request uri: %s' % uri)
                    if self._log_headers:
                        self._logger.debug('Response status code: %s' %
                                           response.status_code)
                        self._logger.debug('Response headers: %s' %
                                           response.headers)
        return bytes_written

    def put_resource(self, uri, contents, media_type, objectify_results=True):
        """Puts the specified contents to the specified resource.  (Does an HTTP PUT.)

        """  # NOQA
        return self._do_request('PUT',
                                uri,
                                contents=contents,
                                media_type=media_type,
                                objectify_results=objectify_results)

    def put_linked_resource(self, resource, rel, media_type, contents):
        """Puts the contents of the resource referenced by the link with the specified rel and mediaType in the specified resource.

        """  # NOQA
        return self.put_resource(find_link(resource, rel, media_type).href,
                                 contents,
                                 media_type)

    def post_resource(self, uri, contents, media_type, objectify_results=True):
        """Posts the specified contents to the specified resource.  (Does an HTTP POST.)

        """  # NOQA
        return self._do_request('POST',
                                uri,
                                contents=contents,
                                media_type=media_type,
                                objectify_results=objectify_results)

    def post_linked_resource(self, resource, rel, media_type, contents):
        """Posts the contents of the resource referenced by the link with the specified rel and mediaType in the specified resource.

        """  # NOQA
        return self.post_resource(find_link(resource, rel, media_type).href,
                                  contents,
                                  media_type)

    def get_resource(self, uri, objectify_results=True):
        """Gets the specified contents to the specified resource.  (Does an HTTP GET.)

        """  # NOQA
        return self._do_request('GET',
                                uri,
                                objectify_results=objectify_results)

    def get_linked_resource(self, resource, rel, media_type):
        """Gets the contents of the resource referenced by the link with the specified rel and mediaType in the specified resource.

        """  # NOQA
        return self.get_resource(find_link(resource, rel, media_type).href)

    def delete_resource(self, uri, force=False, recursive=False):
        full_uri = '%s?force=%s&recursive=%s' % (uri, force, recursive)
        return self._do_request('DELETE', full_uri)

    def delete_linked_resource(self, resource, rel, media_type):
        """Deletes the resource referenced by the link with the specified rel and mediaType in the specified resource.

        """  # NOQA
        return self.delete_resource(find_link(resource, rel, media_type).href)

    def get_admin(self):
        """Returns the "admin" root resource type.

        """
        return self._get_wk_resource(_WellKnownEndpoint.ADMIN)

    def get_query_list(self):
        """Returns the list of supported queries.

        """
        return self._get_wk_resource(_WellKnownEndpoint.QUERY_LIST)

    def get_org(self):
        """Returns the logged in org.

        """
        return self._get_wk_resource(_WellKnownEndpoint.LOGGED_IN_ORG)

    def get_extensibility(self):
        """Returns the 'extensibility' resource type.

        """
        return self._get_wk_resource(_WellKnownEndpoint.API_EXTENSIBILITY)

    def get_extension(self):
        """Returns the 'extension' resource type.

        """
        return self._get_wk_resource(_WellKnownEndpoint.EXTENSION)

    def get_org_list(self):
        """Returns the list of organizations.

        """
        return self._get_wk_resource(_WellKnownEndpoint.ORG_LIST)

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
        return _TypedQuery(query_type_name,
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
        return self._session_endpoints[wk_type]


def find_link(resource, rel, media_type, fail_if_absent=True):
    """Returns the link of the specified rel and type in the specified resource

     * @param resource the resource with the link
     * @param rel the rel of the desired link
     * @param mediaType media type of content
     * @param failIfAbsent controls whether an exception is thrown if there's \
              not exactly one link of the specified rel and media type
     * @return the link, or null if no such link is present and failIfAbsent \
               is false
     * @throws MissingLinkException if no link of the specified rel and media \
               type is found
     * @throws MultipleLinksException if multiple links of the specified rel \
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
    """Returns all the links of the specified rel and type in the resource

     * @param resource the resource with the link
     * @param rel the rel of the desired link
     * @param mediaType media type of content
     * @return the links (could be an empty list)

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
    """Abstraction over <Link> elements.

    """
    def __init__(self, link_elem):
        self.rel = link_elem.get('rel')
        self.media_type = link_elem.get('type')
        self.href = link_elem.get('href')
        self.name = link_elem.get('name') \
            if 'name' in link_elem.attrib else None


class _AbstractQuery(object):

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
            if sys.version_info[0] < 3:
                self._filter += urllib.quote(equality_filter[1])
            else:
                self._filter += urllib.parse.quote(equality_filter[1])

        self._sort_desc = sort_desc
        self._sort_asc = sort_asc

        self.fields = fields

    def execute(self):
        query_uri = self._build_query_uri(
            self._find_query_uri(self._query_result_format),
            self._page, self._page_size, self._filter,
            self._include_links, fields=self.fields)
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
            query_results = self._client.get_resource(next_page_uri,
                                                      objectify_results=True)

    def find_unique(self):
        """Convenience wrapper over execute() for the case where exactly one match is expected.

        """  # NOQA
        query_results = self.execute()

        # Make sure we got at least one result record
        try:
            if sys.version_info[0] < 3:
                item = query_results.next()
            else:
                item = next(query_results)
        except StopIteration:
            raise MissingRecordException()

        # Make sure we didn't get more than one result record
        try:
            if sys.version_info[0] < 3:
                query_results.next()
            else:
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
            # filterEncoded=true allows VCD to properly
            # parse encoded '==' in the filter parameter.
            uri += '&filterEncoded=true&filter='
            uri += qfilter

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
        super(_TypedQuery, self).__init__(query_result_format,
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
            _get_query_list_map()[(query_media_type, self._query_type_name)]
        return query_href
