# VMware Cloud Director Python Client
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
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

API = 'api'
CLOUDAPI = 'cloudapi'
API_AUTH_KEY = 'ApiKeyAuth'

HEADER_ACCEPT = 'Accept'
HEADER_AUTHORIZATION = 'Authorization'
HEADER_LINK = 'Link'
HEADER_LOCATION = 'Location'
HEADER_X_VCLOUD_TOKEN_TYPE = 'X-VMWARE-VCLOUD-TOKEN-TYPE'
HEADER_X_VCLOUD_ACCESS_TOKEN = 'X-VMWARE-VCLOUD-ACCESS-TOKEN'
HEADER_X_VCLOUD_REQUEST_ID = 'X-VMWARE-VCLOUD-REQUEST-ID'
HEADER_CONTENT_TYPE_NAME = 'Content-Type'

APPLICATION_JSON = 'application/json'
APPLICATION_JSON_VCLOUD = 'application/*+json'
BEARER_TOKEN_TYPE = 'Bearer'

HEADERS_TO_REDACT = [
    'Authorization', 'x-vcloud-authorization',
    'X-VMWARE-VCLOUD-ACCESS-TOKEN'
]

DEFAULT_LOG_FILE = 'cloud_director_python_client.log'

API_VERSION_33 = '33.0'

SESSIONS_API_URI = 'sessions'

SESSION_API_URI = 'session'

LEGACY_SESSION_API_MEDIA_TYPE = 'application/vnd.vmware.vcloud.session+json'

API_VERSION_URI = 'versions'

import json
import time
from datetime import datetime, timedelta
from enum import Enum

from six.moves import http_client
from pyvcloud.vcd.api_helper import ApiHelper
from pyvcloud.vcd.client import Client, BasicLoginCredentials, Link, ApiVersion
from vcloud.rest.openapi.apis.sessions_api import SessionsApi
from vcloud.api.rest.schema_v1_5.task_type import TaskType
from vcloud.api.rest.schema_v1_5.session_type import SessionType
from vcloud.rest.openapi.rest import ApiException
from pyvcloud.vcd.exceptions import (
    AccessForbiddenException, BadRequestException, ConflictException,
    InternalServerException, InvalidContentLengthException,
    MethodNotAllowedException, NotAcceptableException, NotFoundException,
    RequestTimeoutException, TaskTimeoutException, UnauthorizedException,
    UnknownApiException, UnsupportedMediaTypeException, VcdTaskException, ClientException)

class BearerLoginCredentials(object):
    """
    Description : Class for initializing Bearer Login method
    """

    def __init__(self, bearer_token):
        self.bearer_token = bearer_token


class RestLink(object):
    """
    Description : Class which stores object response links
    """

    def __init__(self, href, rel, model=None, title=None, type=None):
        self.href = href
        self.rel = rel
        self.model = model
        self.title = title
        self.type = type

    def __repr__(self):
        return 'Link(%s, rel=%s, model=%s, title=%s, type=%s)' % (
            self.href, self.rel, self.model, self.title, self.type)


class TaskStatus(Enum):
    """
    Description : Class having status of all tasks
    """
    QUEUED = 'queued'
    PRE_RUNNING = 'preRunning'
    RUNNING = 'running'
    SUCCESS = 'success'
    ERROR = 'error'
    CANCELED = 'canceled'
    ABORTED = 'aborted'


class _TaskMonitor(object):
    """
    Description : Class for monitoring the task
    """
    _DEFAULT_POLL_SEC = 5
    _DEFAULT_TIMEOUT_SEC = 600

    def __init__(self, client, logger):
        self._client = client
        self._logger = logger

    def wait_for_success(self,
                         task,
                         timeout=_DEFAULT_TIMEOUT_SEC,
                         poll_frequency=_DEFAULT_POLL_SEC,
                         callback=None):
        return self.wait_for_status(task,
                                    timeout,
                                    poll_frequency, [TaskStatus.ERROR],
                                    [TaskStatus.SUCCESS],
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
        self._logger.debug('Waiting for task: ' + task.get('operation'))
        while True:
            task = self._get_task_status(task_href)
            self._logger.debug('Task status: ' + task.get('status'))
            if callback is not None: callback(task)
            task_status = task.get('status').lower()
            for status in expected_target_statuses:
                if task_status == status.value.lower():
                    return task
            for status in _fail_on_statuses:
                if task_status == status.value.lower():
                    raise VcdTaskException(task_status, task['error'])
            if start_time - datetime.now() > timedelta(seconds=timeout):
                break
            time.sleep(poll_frequency)
        raise TaskTimeoutException("Task timeout")

    def _get_task_status(self, task_href):
        return self._client.get_resource(task_href)

    def get_status(self, task):
        return self._get_task_status(task.get('href')).get('status').lower()


class VcdClient(Client):
    """A client to interact with the vCloud Director OpenAPI & Legacy Api.

    Client defaults to the highest API version supported by vCloud Director
    when api_Version is not provided. You can also set the version explicitly
    using the api_version parameter.

    :param str uri: vCD server host name or connection URI.
    :param str api_version: vCD API version to use.
    :param boolean verify_ssl_certs: If True validate server certificate;
        False allows self-signed certificates.
    :param str log_file: log file name or None, which suppresses logging.
    """
    API = '/api/'
    CLOUDAPI = '/cloudapi/'

    ACCEPT_TYPE_API = 'application/json'
    ACCEPT_TYPE_CLOUDAPI = 'application/*+json'

    def __init__(self,
                 uri,
                 api_version=None,
                 verify_ssl_certs=True,
                 log_file=None,
                 log_requests=False,
                 log_bodies=None,
                 log_headers=None
                 ):
        self.prep_base_uri(uri)
        self._api_version = api_version
        # Initialize ApiBaseClient without any parameter
        super().__init__(uri, api_version, verify_ssl_certs, log_file, log_requests, log_bodies=log_bodies, log_headers=log_headers)
        # Disable HTTP debug logging on stdout
        http_client.HTTPConnection.debuglevel = 0
        self._api_helper = ApiHelper()
        self._versions = None
        self._task_monitor = None

    def prep_base_uri(self, uri):
        self._uri = uri
        if len(self._uri) > 0:
            if self._uri.startswith('https://') or self._uri.startswith(
                    'http://'):
                pass
            else:
                self._uri = 'https://' + self._uri

    def logout(self):
        """Logout current user and clear the session.
        """
        super(VcdClient, self).logout()
        self.__remove_session_token()

    def __remove_session_token(self):
        del self._config.api_key_prefix[HEADER_AUTHORIZATION]
        del self._config.api_key[HEADER_AUTHORIZATION]

    def _is_api_uri(self, uri):
        if self.API in uri:
            return True
        elif self.CLOUDAPI in uri:
            return False
        else:
            raise ClientException('%s is not a valid vCD URI' % uri)

    def build_api_uri(self, resource_path):
        """Builds API uri.

        :param str resource_path: relative resource path.

        :return: complete API uri.

        :rtype: str

        """
        return self.get_api_uri() + resource_path

    def build_cloudapi_uri(self, resource_path):
        """Builds CloudAPI uri.

        :param str resource_path: relative resource path.

        :return: complete CloudAPI uri.

        :rtype: str

        """
        return self.get_cloudapi_uri() + resource_path

    def get_last_status(self):
        """Returns the status of last API call

        :return: Status code of last response

        :rtype: int
        """
        return self._status

    def get_last_links(self):
        """Returns links received in last API call

        :return:

        :rtype: list of Links
        """
        return self._links

    def __make_rest_call(self,
                         method,
                         url,
                         headers=None,
                         query_params=None,
                         body=None):
        response = self.rest_client.request(method,
                                            url,
                                            headers=headers,
                                            query_params=query_params,
                                            body=body)
        self.__log_request_response(headers, body, response.getheaders(),
                                    response.data)
        return response

    def get_supported_versions(self):
        """Returns the list of supported API versions by vCloud director

        :return: versions as strings, sorted in ascending order

        :rtype: list
        """
        if self._versions is None:
            headers = {HEADER_ACCEPT: APPLICATION_JSON_VCLOUD}
            if self._config.host[-1] == '/':
                url = self._config.host + API + '/' + API_VERSION_URI
            else:
                url = self._config.host + '/' + API + '/' + API_VERSION_URI
            response = self.__make_rest_call('GET', url, headers=headers)
            response_json = json.loads(response.data)
            versions = []
            for version_json in response_json.get('versionInfo'):
                if not version_json.get('deprecated'):
                    versions.append(version_json.get('version'))
            self._versions = list(set(versions))
            self._versions.sort()

        return self._versions

    def get_highest_supported_version(self):
        """Returns the highest API version supported by vCloud Director

        :return: version as string

        :rtype: str
        """
        return self.get_supported_versions()[-1]

    def find_first_link(self, rel, **kwargs):
        """Finds first links by relation and other attributes.
        :param str rel: relation of the desired link.
        :param dict kwargs: list of key-value pairs to search the desired link.
        :return: first link with the given relation and search attributes,
            None otherwise.
        :rtype: list
        """
        for link in self._links:
            if rel in link.rel.split():
                link_found = True
                for attr in kwargs:
                    if kwargs[attr] != getattr(link, attr):
                        link_found = False
                        break
                if link_found:
                    return link
        return None

    def get_last_task(self):
        """Gets the task of last API call.
        :return: task received from vCD.
        :rtype: TaskType
        """
        return self._task

    def wait_for_task(self, task):
        """Waits for success of a given task.
        :param TaskType task: task we are waiting for.
        """
        if task is not None:
            self.get_task_monitor().wait_for_success(
                self.get_resource(task.href))

    def wait_for_last_task(self):
        """Waits for the success of last task."""
        self.wait_for_task(self._task)

    def _get_accept_type(self, is_api):
        if is_api:
            return self.ACCEPT_TYPE_CLOUDAPI
        else:
            return self.ACCEPT_TYPE_API

    def call_api(self,
                 resource_path,
                 method,
                 path_params=None,
                 query_params=None,
                 header_params=None,
                 body=None,
                 post_params=None,
                 files=None,
                 response_type=None,
                 auth_settings=None,
                 callback=None,
                 _return_http_data_only=None,
                 collection_formats=None,
                 _preload_content=True,
                 _request_timeout=None):
        """
        Make openapi rest calls
        """
        auth_settings = [API_AUTH_KEY]
        self._status = self._headers = self._links = self._headers = None
        try:
            if self._config.host[-1] == '/':
                resource_path = CLOUDAPI + resource_path
            else:
                resource_path = '/' + CLOUDAPI + resource_path
            self.default_headers[HEADER_ACCEPT] = '{};version={}'.format(APPLICATION_JSON,
                                                                                   self._api_version)
            if _return_http_data_only and not resource_path.find(SESSIONS_API_URI):
                response_data = super().call_api(
                    resource_path, method, path_params, query_params,
                    header_params, body, post_params, files, response_type,
                    auth_settings, callback, _return_http_data_only,
                    collection_formats, _preload_content, _request_timeout)
            else:
                _return_http_data_only = None
                response_data, self._status, self._headers = super().call_api(
                    resource_path, method, path_params, query_params,
                    header_params, body, post_params, files, response_type,
                    auth_settings, callback, _return_http_data_only,
                    collection_formats, _preload_content, _request_timeout)
                self.__log_request_response(header_params, body, self._headers, response_data)
                self.__store_links()
                self._store_task(False, response_data)
        except ApiException as ae:
            self._status = ae.status
            ex = self.__get_specific_exception(
                self._status, ae.headers.get(HEADER_X_VCLOUD_REQUEST_ID),
                json.loads(ae.body))
            raise ex from None
        return response_data

    def call_legacy_api(self,
                 method,
                 uri,
                 contents=None,
                 media_type=None,
                 params=None,
                 response_type=None):
        """Invokes a vCD API.
        This method calls a vCD API and stores response status code, links
        and returned task if any. Model objects are serialized/deserialized
        to/from JSON objects.
        :param str method: http request method.
        :param str uri: complete request URI.
        :param object contents: model object containing the request payload.
        :param str media_type: media type of content.
        :param dict params: query parameters.
        :param type response_type: model class of the response.
        :return: model object containing the response.
        :rtype: object
        """
        is_api = self._is_api_uri(uri)
        accept_type = self._get_accept_type(is_api)
        contents_json = self._api_helper.sanitize_for_serialization(contents)
        self._status = self._headers = self._links = self._headers = None
        response = self._do_request_prim(method,
                                         uri,
                                         self._session,
                                         contents=contents_json,
                                         media_type=media_type,
                                         accept_type=accept_type,
                                         params=params)
        self._status = response.status_code
        self._headers = response.headers
        response_model = None
        if response_type:
            response_model = self._api_helper.deserialize(
                response, response_type)
        self._store_links(is_api, response_model)
        self._store_task(is_api, response_model)
        return response_model

    def _store_links(self, is_api, response):
        self._links = []
        if is_api:
            if hasattr(response, 'link') and response.link is not None:
                self._links = response.link
        elif 'Link' in self._headers:
            for link in self._headers['Link'].split(', '):
                link_entries = link.split(';')
                link = Link()
                setattr(link, 'href', link_entries[0].strip('<>'))
                for i in range(1, len(link_entries)):
                    key_value = link_entries[i].split('=')
                    setattr(link, key_value[0], key_value[1].strip('"'))
                self._links.append(link)

    def _store_task(self, is_api, response):
        if isinstance(response, TaskType):
            self._task = response
        if is_api:
            if hasattr(response, 'tasks'):
                tasks = response.tasks
                if tasks is not None:
                    tasks = tasks.task
                    if tasks and len(tasks) > 0:
                        self._task = tasks[0]
        elif 'Location' in self._headers:
            task_href = self._headers.get('Location')
            if task_href is not None:
                self._task = self.call_legacy_api('GET',
                                           uri=task_href,
                                           response_type=TaskType)

    @staticmethod
    def __get_specific_exception(status, request_id, vcd_error):
        if status == 400:
            return BadRequestException(status, request_id, vcd_error)

        if status == 401:
            return UnauthorizedException(status, request_id, vcd_error)

        if status == 403:
            return AccessForbiddenException(status, request_id, vcd_error)

        if status == 404:
            return NotFoundException(status, request_id, vcd_error)

        if status == 405:
            return MethodNotAllowedException(status, request_id, vcd_error)

        if status == 406:
            return NotAcceptableException(status, request_id, vcd_error)

        if status == 408:
            return RequestTimeoutException(status, request_id, vcd_error)

        if status == 409:
            return ConflictException(status, request_id, vcd_error)

        if status == 415:
            return UnsupportedMediaTypeException(status, request_id, vcd_error)

        if status == 416:
            return InvalidContentLengthException(status, request_id, vcd_error)

        if status == 500:
            return InternalServerException(status, request_id, vcd_error)

        return UnknownApiException(status, request_id, vcd_error)

    def __store_links(self):
        self._links = []
        for link in self._headers.getlist(HEADER_LINK):
            link_entries = link.split(';')
            link_dict = {'href': link_entries[0].strip('<>')}
            for i in range(1, len(link_entries)):
                key_value = link_entries[i].split('=')
                link_dict[key_value[0]] = key_value[1].strip('"')
            self._links.append(RestLink(**link_dict))

    def __store_task(self):
        self._task_href = self._headers.get(HEADER_LOCATION)

    def __log_request_response(self, request_headers, request_body, response_headers,
                               response_body):
        if not self._log_requests:
            return

        self._logger.debug('Request headers: %s' %
                           self._redact_headers(request_headers))
        self._logger.debug('Request body: %s' % request_body)
        self._logger.debug('Response headers: %s' %
                           self._redact_headers(response_headers))
        self._logger.debug('Response body: %s' % response_body)

class QueryParamsBuilder(object):
    """An interface to set query parameters.

    It provides setters for all query parameters and a method to get complete
    parameters set in a dictionary format.
    """

    IDRECORDS = 'idrecords',
    RECORDS = 'records',
    REFERENCES = 'references'

    def __init__(self):
        """Constructor of query parameters.

        Initializes the parameters to am empty dictionary.
        """
        self._query_params = {}

    def set_filter(self, filter_):
        """Sets the filter expression.

        :param str filter_: filter expression of the query
        """
        self._query_params['filter'] = filter_
        return self

    def set_format(self, format_):
        """Sets the format of query result.

        :param str format_: valid formats are, idrecords/records/references.
        """
        self._query_params['format'] = format_
        return self

    def set_page(self, page):
        """Sets the page number of query result.

        :param str page: if result has multiple pages, get the specific result
            page.
        """
        self._query_params['page'] = page
        return self

    def set_page_size(self, page_size):
        """Sets the page size of query result.

        :param str page_size: get 'page_size' number of results per page.
        """
        self._query_params['pageSize'] = page_size
        return self

    def set_sort_asc(self, sort_asc):
        """Sets sort_asc in the query.

        :param str sort_asc: if 'name' field is present in the result sort
            ascending by that field.
        """
        self._query_params['sortAsc'] = sort_asc
        return self

    def set_sort_desc(self, sort_desc):
        """Sets sort_desc in the query.

        :param str sort_desc: if 'name' field is present in the result sort
            descending by that field.
        """
        self._query_params['sortDesc'] = sort_desc
        return self

    def set_type(self, type_):
        """Sets type of entity to query REST API.

        :param str type_: type of the vCD entity.
        """
        self._query_params['type'] = type_
        return self

    def build(self):
        """Gets the final set of query parameters.

        :return: final set of query parameters.

        :rtype: dict
        """
        self._query_params['filterEncoded'] = 'true'
        return self._query_params
