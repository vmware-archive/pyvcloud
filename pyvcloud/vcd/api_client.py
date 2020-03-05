# VMware vCloud Director Python SDK
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
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

from vcloud.api.rest.schema_v1_5.task_type import TaskType
from vcloud.rest.openapi.models.link import Link

from pyvcloud.vcd.api_helper import ApiHelper
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import ClientException


class ApiClient(Client):
    """A low-level interface to the vCloud Director REST API and CloudAPI.

    API client provides an uniform way to invoke REST API and CloudAPI
    endpoints. The client uses generated model classes for request and
    response payloads.

    :param str uri: vCD server host name or connection URI.
    :param str api_version: vCD API version to use.
    :param boolean verify_ssl_certs: If True validate server certificate;
        False allows self-signed certificates.
    :param str log_file: log file name or None, which suppresses logging.
    :param boolean log_request: if True log HTTP requests.
    :param boolean log_headers: if True log HTTP headers.
    :param boolean log_bodies: if True log HTTP bodies.
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
                 log_headers=False,
                 log_bodies=False):
        super().__init__(uri, api_version, verify_ssl_certs, log_file,
                         log_requests, log_headers, log_bodies)
        self._api_helper = ApiHelper()
        self._status = None
        self._headers = None
        self._links = None
        self._task = None

    def call_api(self,
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

    def _get_accept_type(self, is_api):
        if is_api:
            return self.ACCEPT_TYPE_CLOUDAPI
        else:
            return self.ACCEPT_TYPE_API

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
                if tasks is not None and len(tasks) > 0:
                    self._task = tasks[0]
        elif 'Location' in self._headers:
            task_href = self._headers.get('Location')
            if task_href is not None:
                self._task = self.call_api('GET',
                                           uri=task_href,
                                           response_type=TaskType)

    def get_last_status(self):
        """Returns the status of last API call.

        :return: Status code of last response

        :rtype: int
        """
        return self._status

    def get_last_headers(self):
        """Returns response headers of last API call.

        :return: response headers

        :rtype: dict
        """
        return self._headers

    def get_last_links(self):
        """Returns links received in last API call.

        :return: list of Links.

        :rtype: list
        """
        return self._links

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
