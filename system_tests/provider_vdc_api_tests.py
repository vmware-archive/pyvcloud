# VMware vCloud Director Python SDK
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

import unittest
from uuid import uuid1

from vcloud.rest.openapi.apis.provider_vdc_api import ProviderVdcApi
from vcloud.api.rest.schema_v1_5.extension.vmw_provider_vdc_params_type \
    import VMWProviderVdcParamsType
from vcloud.api.rest.schema_v1_5.extension.vim_server_type import VimServerType
from vcloud.api.rest.schema_v1_5.extension.resource_pool_list_type import \
    ResourcePoolListType
from vcloud.api.rest.schema_v1_5.extension.vim_object_ref_type \
    import VimObjectRefType
from vcloud.api.rest.schema_v1_5.extension.vim_object_refs_type \
    import VimObjectRefsType
from vcloud.api.rest.schema_v1_5.provider_vdc_type import ProviderVdcType
from vcloud.api.rest.schema_v1_5.references_type import \
    ReferencesType

from pyvcloud.system_test_framework.api_base_test import ApiBaseTestCase
from pyvcloud.vcd.vcd_client import QueryParamsBuilder
from pyvcloud.vcd.client import ResourceType


class TestApiClient(ApiBaseTestCase):
    """Test API client module functions.
    Test cases in this module have ordering dependencies.
    """

    # Test configuration parameters and logger for output.
    _config = None
    _user = None
    _pass = None

    _logger = None

    # Client to be used by all tests.
    _client = None

    _test_pvdc_name = 'test_pvdc-' + str(uuid1())
    _test_pvdc_desc = 'Provider VDC created by Python API client'
    _pvdc_href = None
    _pvdc = None


    def test_0010_create_pvdc(self):
        """Create an pvdc using generated model class.
        This test passes if the pvdc is created successfully and details of
        the pvdc are correct.
        """
        virtual_center_ref, resource_pool = TestApiClient._get_resource_pool()
        provider_vdc_params = VMWProviderVdcParamsType()
        provider_vdc_params.name = TestApiClient._test_pvdc_name
        provider_vdc_params.highest_supported_hardware_version = 'vmx-14'
        provider_vdc_params.storage_profile = ['*']
        provider_vdc_params.vim_server = [virtual_center_ref]

        vim_object_ref = VimObjectRefType()
        vim_object_ref.mo_ref = resource_pool.mo_ref
        vim_object_ref.vim_object_type = resource_pool.vim_object_type
        vim_object_ref.vim_server_ref = virtual_center_ref
        vim_object_refs = VimObjectRefsType()
        vim_object_refs.vim_object_ref = [vim_object_ref]
        provider_vdc_params.resource_pool_refs = vim_object_refs

        provider_vdc = TestApiClient._client.call_legacy_api(
            method='POST',
            uri=TestApiClient._client.build_api_uri('/admin/extension/providervdcsparams'),
            contents=provider_vdc_params,
            media_type='application/vnd.vmware.admin.createProviderVdcParams+json',
            response_type=ProviderVdcType)
        TestApiClient._client.wait_for_last_task()
        TestApiClient._pvdc = provider_vdc
        TestApiClient._pvdc_href = provider_vdc.href

    def test_0020_query_pvdc(self):
        """Query an pvdc.
        Queries an pvdc by name filter.
        This test passes if the query result consists exactly one record.
        """
        self.assertIsNotNone(TestApiClient._pvdc, msg="Previous TestCase to create pvdc FAILED, "
                                                     "so cannot perform query operation")

        name_filter = 'name==%s' % TestApiClient._test_pvdc_name
        page_no = 1
        page_size = 5

        TestApiClient._logger.debug('Executing query on orgs with params page=%s, '
                                    'page_size=%s, filter=%s' % (page_no, page_size, name_filter))
        pvdc_api = ProviderVdcApi(api_client=TestApiClient._client)
        provider_vdc = pvdc_api.get_all_provider_vd_cs(page=page_no, page_size=page_size, filter=name_filter)
        self.assertEqual(provider_vdc.result_total, 1)
        TestApiClient._pvdc = provider_vdc.values[0]

    def test_0030_query_pvdc_resource_pool(self):
        """Query an pvdc resource pool.
        This test passes if the query result status code is 200.
        """
        self.assertIsNotNone(TestApiClient._pvdc, msg="Previous TestCase to create pvdc FAILED, "
                                                      "so cannot perform query operation")

        name_filter = 'name==%s' % TestApiClient._test_pvdc_name
        page_no = 1
        page_size = 5
        pvdc_urn = TestApiClient._pvdc.id
        TestApiClient._logger.debug('Executing query on orgs with params page=%s, '
                                    'page_size=%s, filter=%s' % (page_no, page_size, name_filter))

        pvdc_api = ProviderVdcApi(api_client=TestApiClient._client)
        provider_vdc_resource_pool = pvdc_api.get_root_resource_pools(pvdc_urn=pvdc_urn, page=page_no, page_size=page_size)
        self.assertEqual(TestApiClient._client.get_last_status(), 200)

    def test_0040_delete_pvdc(self):
        """Create an pvdc using generated model class.
        This test passes if the pvdc is created successfully and details of
        the pvdc are correct.
        """
        self.assertIsNotNone(TestApiClient._pvdc, msg="Previous testcase to create pvdc FAILED, "
                                                      "so cannot perform delete operation")
        pvdc_href = TestApiClient._pvdc_href
        TestApiClient._client.call_legacy_api(
            method='DELETE',
            uri=pvdc_href)
        TestApiClient._client.wait_for_last_task()


    @classmethod
    def _get_resource_pool(cls):
        """Get Resource Pool Required for PVDC"""
        virtual_center_ref = TestApiClient.query_reference_by_type(TestApiClient._client,
                                                     ResourceType.VIRTUAL_CENTER)[0]
        virtual_center = TestApiClient._client.call_legacy_api(method='GET',
                                                uri=virtual_center_ref.href,
                                                response_type=VimServerType)
        resource_pool_link = TestApiClient._client.find_first_link(
            rel='down', type='application/vnd.vmware.admin.resourcePoolList+xml')

        resource_pool_list = TestApiClient._client.call_legacy_api(method='GET',
                                                    uri=resource_pool_link.href,
                                                    response_type=ResourcePoolListType)
        if not resource_pool_list.resource_pool:
            raise Exception("No Resource pool present to create provider vdc.")
        resource_pool = resource_pool_list.resource_pool[0]
        return virtual_center_ref, resource_pool

    @classmethod
    def query_reference_by_type(cls, client, type: ResourceType):
        """Query using resource type"""
        query_params = QueryParamsBuilder().set_type(type.value).set_format(
            QueryParamsBuilder.REFERENCES).set_page(1).set_page_size(
                5).set_sort_asc('name').build()
        query_uri = client.build_api_uri('/query')
        result = client.call_legacy_api(method='GET',
                                        uri=query_uri,
                                        params=query_params,
                                        response_type=ReferencesType)
        return result.reference


if __name__ == '__main__':
    unittest.main()