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

import os
import shutil
import tempfile
import unittest
from uuid import uuid1

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.exceptions import EntityNotFoundException


class TestCatalog(BaseTestCase):
    """Test catalog functionalities implemented in pyvcloud."""

    _test_runner_role = CommonRoles.CATALOG_AUTHOR
    _client = None

    _non_existent_catalog_name = 'dummy' + str(uuid1())

    _test_catalog_name = 'test_cat_' + str(uuid1())
    _test_catalog_updated_name = _test_catalog_name + '_updated'

    _test_catalog_description = 'sample description'
    _test_catalog_updated_description = 'sample updated description'

    _test_catalog_href = None

    _test_template_name = 'test-template'
    _test_template_file_name = 'test_vapp_template.ova'
    _test_template_with_chunk_size_name = 'template_with_custom_chunk_size'
    _test_template_with_chunk_size_file_name = \
        'template_with_custom_chunk_size.ova'

    def test_0000_setup(self):
        """Setup a catalog for the tests in this module.

        Create a catalog. Test org.create_catalog() function.

        This test passes if the catalog is created successfully.
        """
        logger = Environment.get_default_logger()
        TestCatalog._client = Environment.get_client_in_default_org(
            TestCatalog._test_runner_role)
        org = Environment.get_test_org(TestCatalog._client)

        try:
            catalog_resource = org.get_catalog(TestCatalog._test_catalog_name)
            logger.debug('Reusing test catalog.')
        except EntityNotFoundException as e:
            catalog_resource = org.create_catalog(
                TestCatalog._test_catalog_name,
                TestCatalog._test_catalog_description)
            TestCatalog._client.get_task_monitor().wait_for_success(
                task=catalog_resource.Tasks.Task[0])
        TestCatalog._test_catalog_href = catalog_resource.get('href')
        self.assertIsNotNone(TestCatalog._test_catalog_href)

    def _template_upload_helper(self, org, catalog_name, template_name,
                                template_file_name):
        """Helper method to upload a template to a catalog in vCD.

        This method creates the catalog item and uploads the template file
        into the spool area(transfer folder) but it doesn't wait for the
        import of the template as catalog item to finish.

        :param pyvcloud.vcd.org.Org org: the organization which contains the
            catalog to which the templates will be uploaded to.
        :param str catalog_name: name of the catalog to which the template will
            be uploaded to.
        :param str template_name: name of the catalog item which represents the
            uploaded template
        :param str template_file_name: name of the local template file which
            will be uploaded.

        :raises: EntityNotFoundException: if the catalog is not found.
        :raises: InternalServerException: if template already exists in vCD.
        """
        bytes_uploaded = -1
        logger = Environment.get_default_logger()
        logger.debug('Uploading template : ' + template_name)
        bytes_uploaded = org.upload_ovf(
            catalog_name=catalog_name,
            file_name=template_file_name,
            item_name=template_name)
        self.assertNotEqual(bytes_uploaded, -1)

    def _template_import_monitor(self, client, org, catalog_name,
                                 template_name):
        """Helper method to block until a template is imported in vCD.

        :param pyvcloud.vcd.client.Client client: the client that would be used
            to make ReST calls to vCD.
        :param pyvcloud.vcd.org.Org org: the organization which contains the
            catalog to which the templates will be uploaded to.
        :param str catalog_name: name of the catalog to which the template is
            being imported.
        :param str template_name: (str): Name of the catalog item which
            represents the uploaded template.

        :raises: EntityNotFoundException: if the catalog/item is not found.
        """
        logger = Environment.get_default_logger()
        logger.debug('Importing template : ' + template_name + ' in vCD')
        # wait for the catalog item import to finish in vCD
        catalog_item_resource = org.get_catalog_item(catalog_name,
                                                     template_name)
        template_resource = client.get_resource(
            catalog_item_resource.Entity.get('href'))
        client.get_task_monitor().wait_for_success(
            task=template_resource.Tasks.Task[0])

    def test_0010_upload_template(self):
        """Test the method org.upload_ovf().

        Upload an ova template to catalog. The template doesn't have
        ovf:chunkSize param in it's descriptor(ovf file).

        This test passes if the upload succeeds and no exceptions are raised.
        """
        org = Environment.get_test_org(TestCatalog._client)

        self._template_upload_helper(
            org=org,
            catalog_name=TestCatalog._test_catalog_name,
            template_name=TestCatalog._test_template_name,
            template_file_name=TestCatalog._test_template_file_name)
        self._template_import_monitor(
            client=TestCatalog._client,
            org=org,
            catalog_name=TestCatalog._test_catalog_name,
            template_name=TestCatalog._test_template_name)

    def test_0020_upload_template_with_ovf_chunkSize(self):
        """Test the method org.upload_ovf().

        Upload an ova template to catalog. The template *has* ovf:chunkSize
        param in it's descriptor(ovf file).

        This test passes if the upload succeeds and no exceptions are raised.
        """
        org = Environment.get_test_org(TestCatalog._client)

        self._template_upload_helper(
            org=org,
            catalog_name=TestCatalog._test_catalog_name,
            template_name=TestCatalog._test_template_with_chunk_size_name,
            template_file_name=TestCatalog.
            _test_template_with_chunk_size_file_name)
        self._template_import_monitor(
            client=TestCatalog._client,
            org=org,
            catalog_name=TestCatalog._test_catalog_name,
            template_name=TestCatalog._test_template_with_chunk_size_name)

    def test_0030_download(self):
        """Test the method org.download_catalog_item().

        Download the two templates that were uploaded earlier.

        This test passes if the two download task writes non zero bytes to the
        disk without raising any exceptions.
        """
        org = Environment.get_test_org(TestCatalog._client)
        tempdir = None
        try:
            cwd = os.getcwd()
            tempdir = tempfile.mkdtemp(dir='.')
            os.chdir(tempdir)
            bytes_written = org.download_catalog_item(
                catalog_name=TestCatalog._test_catalog_name,
                item_name=TestCatalog._test_template_name,
                file_name=TestCatalog._test_template_file_name)
            self.assertNotEqual(bytes_written, 0)

            bytes_written = org.download_catalog_item(
                catalog_name=TestCatalog._test_catalog_name,
                item_name=TestCatalog._test_template_with_chunk_size_name,
                file_name=TestCatalog._test_template_with_chunk_size_file_name)
            self.assertNotEqual(bytes_written, 0)
        finally:
            if tempdir is not None:
                os.chdir(cwd)
                shutil.rmtree(tempdir)

    def test_0040_list_catalog(self):
        """Test the method org.list_catalog().

        Fetches all catalogs in the current organization.

        This test passes if the catalog created in test_0000_setup is present
        in the retrieved list of catalogs.
        """
        org = Environment.get_test_org(TestCatalog._client)
        catalog_list = org.list_catalogs()

        retieved_catalog_names = []
        for catalog in catalog_list:
            retieved_catalog_names.append(catalog.get('name'))

        self.assertIn(TestCatalog._test_catalog_name, retieved_catalog_names)

    def test_0050_get_catalog(self):
        """Test the method org.get_catalog().

        Retrieve the catalog created in test_0000_setup.

        This test passes if the catalog created in test_0000_setup is
        retrieved successfully without any errors.
        """
        org = Environment.get_test_org(TestCatalog._client)
        catalog_resource = org.get_catalog(TestCatalog._test_catalog_name)

        self.assertEqual(TestCatalog._test_catalog_name,
                         catalog_resource.get('name'))

    def test_0060_get_nonexistent_catalog(self):
        """Test the method org.get_catalog() for a non existent catalog.

        This test passes if the catalog retrieval operation fails with a
        EntityNotFoundException.
        """
        org = Environment.get_test_org(TestCatalog._client)
        try:
            org.get_catalog(TestCatalog._non_existent_catalog_name)
            self.fail('Should not be able to fetch catalog ' +
                      TestCatalog._non_existent_catalog_name)
        except EntityNotFoundException as e:
            return
        self.fail('Should fail with EntityNotFoundException while fetching'
                  'catalog ' + TestCatalog._non_existent_catalog_name)

    def test_0070_update_catalog(self):
        """Test the method org.update_catalog().

        Update the name and description of the catalog created in
        test_0000_setup. Revert the changes madeto the catalog after we verify
        that the operation is successful.

        This test passes if the catalog updation operation succeeds without
        raising any errors.
        """
        logger = Environment.get_default_logger()
        org = Environment.get_test_org(TestCatalog._client)

        catalog_name = TestCatalog._test_catalog_name
        catalog_description = TestCatalog._test_catalog_description
        new_name = TestCatalog._test_catalog_updated_name
        new_description = TestCatalog._test_catalog_updated_description

        logger.debug('Changing catalog:' + catalog_name + ' \'name\' to ' +
                     new_name + ', and \'description\' to ' + new_description)
        updated_catalog_resource = org.update_catalog(catalog_name, new_name,
                                                      new_description)

        self.assertEqual(updated_catalog_resource.get('name'), new_name)
        self.assertEqual(updated_catalog_resource.Description.text,
                         new_description)

        logger.debug('Changing catalog:' + new_name + ' \'name\' back to ' +
                     catalog_name + ',and \'description\' back to ' +
                     catalog_description)
        org.reload()
        org.update_catalog(new_name, catalog_name, catalog_description)

    def test_0080_change_catalog_ownership(self):
        """Test the method org.change_catalog_owner().

        Change the ownership of the catalog to org administrator and back to
        the original owner.

        This test passes if the catalog owner change operation succeeds without
        raising any errors. And the new owner is able to access the catalog.
        """
        logger = Environment.get_default_logger()
        org_admin_client = Environment.get_client_in_default_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        org = Environment.get_test_org(org_admin_client)

        catalog_name = TestCatalog._test_catalog_name
        original_owner_username = \
            Environment.get_username_for_role_in_test_org(
                TestCatalog._test_runner_role)
        org_admin_username = Environment.get_username_for_role_in_test_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        try:
            logger.debug('Changing owner of catalog:' + catalog_name +
                         ' to ' + org_admin_username)
            org.change_catalog_owner(catalog_name, org_admin_username)
            catalog_admin_resource = org.get_catalog(catalog_name,
                                                     is_admin_operation=True)
            self.assertEqual(catalog_admin_resource.Owner.User.get('name'),
                             org_admin_username)

            logger.debug('Changing owner of catalog ' + catalog_name +
                         ' back to ' + original_owner_username)
            org.change_catalog_owner(catalog_name, original_owner_username)
            catalog_admin_resource = org.get_catalog(catalog_name,
                                                     is_admin_operation=True)
            self.assertEqual(catalog_admin_resource.Owner.User.get('name'),
                             original_owner_username)
        finally:
            org_admin_client.logout()

    def test_0090_list_catalog_items(self):
        """Test the method org.list_catalog_item().

        List all items in the catalog created in setup method.

        This test depends on success of test_0010_upload_tempalte and
        test_0020_upload_template_with_ovf_chunkSize.

        This test passes if both the uploaded templates are in the retrieved
        list of items.
        """
        org = Environment.get_test_org(TestCatalog._client)
        catalog_item_list = org.list_catalog_items(
            TestCatalog._test_catalog_name)

        catalog_item_names = []
        for item in catalog_item_list:
            catalog_item_names.append(item.get('name'))

        self.assertIn(TestCatalog._test_template_name, catalog_item_names)
        self.assertIn(TestCatalog._test_template_with_chunk_size_name,
                      catalog_item_names)

    def test_0100_get_catalog_item(self):
        """Test the method org.get_catalog_item().

        Retrieve the first template uploaded to the catalog created in setup
        method.

        This test depends on the success of test_0010_upload_tempalte.

        This test passes if the first uploaded templates is retrieved
        successfully.
        """
        org = Environment.get_test_org(TestCatalog._client)
        catalog_item_resource = org.get_catalog_item(
            TestCatalog._test_catalog_name, TestCatalog._test_template_name)

        self.assertEqual(TestCatalog._test_template_name,
                         catalog_item_resource.get('name'))

    def _0110_catalog_access_settings(self):
        """Test the access control methods for catalogs.

        This test passes if all the acl operations complete successfully.
        """
        logger = Environment.get_default_logger()
        org = Environment.get_test_org(TestCatalog._client)

        org_name = org.get_name()
        print(org_name)
        catalog_name = TestCatalog._test_catalog_name
        vapp_author_username = Environment.get_username_for_role_in_test_org(
            CommonRoles.VAPP_AUTHOR)
        org_admin_username = Environment.get_username_for_role_in_test_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)

        # remove all access control settings to the catalog
        logger.debug('Removing all access control settings from catalog:' +
                     catalog_name)
        control_access = org.remove_catalog_access_settings(catalog_name,
                                                            remove_all=True)
        self.assertFalse(hasattr(control_access, 'AccessSettings'))

        # add three access control settings to the catalog
        logger.debug('Adding three acl rule to the catalog:' + catalog_name)
        control_access = org.add_catalog_access_settings(
            catalog_name,
            access_settings_list=[{
                'name': vapp_author_username,
                'type': 'user',
                'access_level': 'ReadOnly'
            }, {
                'name': org_admin_username,
                'type': 'user',
                'access_level': 'Change'
            }, {
                'name': org_name,
                'type': 'org',
                'access_level': 'ReadOnly'
            }])
        self.assertEqual(len(control_access.AccessSettings.AccessSetting),
                         3)
        # TODO() : Test that vapp author can actually access the catalog

        # retrieve access control settings of the catalog
        logger.debug('Retrieving acl rule from catalog:' + catalog_name)
        control_access = org.get_catalog_access_settings(catalog_name)
        self.assertEqual(len(control_access.AccessSettings.AccessSetting),
                         3)

        # remove partial access control settings from the catalog
        logger.debug('Removing 2 acl rule from catalog:' + catalog_name)
        control_access = org.remove_catalog_access_settings(
            catalog_name,
            access_settings_list=[{
                'name': org_admin_username,
                'type': 'user'
            }, {
                'name': org_name,
                'type': 'org'
            }])
        self.assertEqual(len(control_access.AccessSettings.AccessSetting),
                         1)

        # test removal of non existing access control settings from the catalog
        logger.debug('Trying to remove non existent acl rule from catalog:' +
                     catalog_name)
        try:
            org.remove_catalog_access_settings(
                catalog_name,
                access_settings_list=[{
                    'name': org_admin_username,
                    'type': 'user'
                }])
            self.fail('Removing non existing acl should fail.')
        except EntityNotFoundException:
            pass

        # remove all access control settings from the catalog
        logger.debug('Removing all access control settings from catalog:' +
                     catalog_name)
        control_access = org.remove_catalog_access_settings(
            catalog_name, remove_all=True)
        self.assertFalse(hasattr(control_access, 'AccessSettings'))

    def _0120_catalog_sharing_accross_org(self):
        pass

    def _0130_catalog_sharing_via_acl(self):
        org = Environment.get_test_org(TestCatalog._client)
        catalog_name = TestCatalog._test_catalog_name

        control_access = org.share_catalog_with_org_members(
            catalog_name, everyone_access_level='ReadOnly')
        self.assertEqual(control_access.IsSharedToEveryone.text, 'true')
        self.assertEqual(control_access.EveryoneAccessLevel.text, 'ReadOnly')
        # TODO(): Access the catalog using a vapp_user user

        control_access = org.share_catalog_with_org_members(
            catalog_name, everyone_access_level='ReadOnly')
        self.assertEqual(control_access.IsSharedToEveryone.text, 'true')
        self.assertEqual(control_access.EveryoneAccessLevel.text, 'ReadOnly')
        # TODO(): Access the catalog using a vapp_user user should cause error

    @developerModeAware
    def test_9998_teardown(self):
        """Test the  method delete_catalog_item() and delete_catalog().

        Invoke the methods for templates and catalogs created by setup. This
        test should be run as org admin, since a failure in any of the previous
        tests might leave the catalog stranded with an user other than the one
        who created the catalog in first place.

        This test passes if none of the delete operations generate any
        exceptions.
        """
        try:
            org_admin_client = Environment.get_client_in_default_org(
                CommonRoles.ORGANIZATION_ADMINISTRATOR)
            org = Environment.get_test_org(org_admin_client)
            logger = Environment.get_default_logger()

            catalog_name = TestCatalog._test_catalog_name
            items_to_delete = [
                TestCatalog._test_template_name,
                TestCatalog._test_template_with_chunk_size_name
            ]

            for item in items_to_delete:
                logger.debug('Deleting catalog item : ' + item)
                try:
                    org.delete_catalog_item(catalog_name, item)
                except EntityNotFoundException as e:
                    logger.debug('Catalog item:' + item + ' not found!')

            try:
                logger.debug('Deleting catalog : ' + catalog_name)
                org.delete_catalog(catalog_name)
            except EntityNotFoundException as e:
                    logger.debug('Catalog :' + catalog_name + ' not found!')
        finally:
            org_admin_client.logout()

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestCatalog._client.logout()


if __name__ == '__main__':
    unittest.main()
