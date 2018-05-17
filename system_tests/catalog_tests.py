import os
import shutil
import tempfile
import unittest

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.exceptions import EntityNotFoundException


class TestCatalog(BaseTestCase):
    """Test catalog functionalities implemented in pyvcloud."""

    _test_runner_role = CommonRoles.CATALOG_AUTHOR
    _client = None

    _test_catalog_name = 'test_cat'
    _test_catalog_description = 'sample description'
    _test_catalog_href = None
    _test_template_name = 'test-template'
    _test_template_file_name = 'test_vapp_template.ova'
    _test_template_with_chunk_size_name = 'template_with_custom_chunk_size'
    _test_template_with_chunk_size_file_name = \
        'template_with_custom_chunk_size.ova'
    _test_folder = None

    def test_0000_setup(self):
        """Setup the catalog and templates for the tests in this module.

        Create a catalog and upload two templates to the catalog.

        This test passes if the catalog is created successfully and the
        templates are uploaded successfully to the catalog / reused.
        """
        TestCatalog._client = Environment.get_client_in_default_org(
            TestCatalog._test_runner_role)
        org = Environment.get_test_org(TestCatalog._client)

        try:
            catalog_resource = org.get_catalog(TestCatalog._test_catalog_name)
            print('Reusing test catalog.')
        except EntityNotFoundException as e:
            catalog_resource = org.create_catalog(
                TestCatalog._test_catalog_name,
                TestCatalog._test_catalog_description)
        TestCatalog._test_catalog_href = catalog_resource.get('href')
        self.assertIsNotNone(TestCatalog._test_catalog_href)

        reused = not self._template_upload_helper(
            org=org,
            catalog_name=TestCatalog._test_catalog_name,
            template_name=TestCatalog._test_template_name,
            template_file_name=TestCatalog._test_template_file_name)
        if reused is False:
            self._template_import_monitor(
                client=TestCatalog._client,
                org=org,
                catalog_name=TestCatalog._test_catalog_name,
                template_name=TestCatalog._test_template_name)

        reused = not self._template_upload_helper(
            org=org,
            catalog_name=TestCatalog._test_catalog_name,
            template_name=TestCatalog._test_template_with_chunk_size_name,
            template_file_name=TestCatalog.
            _test_template_with_chunk_size_file_name)
        if reused is False:
            self._template_import_monitor(
                client=TestCatalog._client,
                org=org,
                catalog_name=TestCatalog._test_catalog_name,
                template_name=TestCatalog._test_template_with_chunk_size_name)

    def _template_upload_helper(self, org, catalog_name, template_name,
                                template_file_name):
        """Helper method to upload a template to a catalog in vCD.

        This method creates the catalog item and uploads the template file
        into the spool area(transfer folder) but it doesn't wait for the
        import of the template as catalog item to finish.

        :param org: An object of :class:`lxml.objectify.StringElement`that
            describes the organization which contains the catalog to which
            the templates will be uploaded to.
        :param catalog_name: (str): Name of the catalog to which the template
            will be uploaded to.
        :param template_name: (str): Name of the catalog item which represents
            the uploaded template
        :param template_file_name: (str): Name of the local template file which
            will be uploaded.

        :return: (bool): True, if the template is uploaded, False if we reuse
            an existing template with the same name.
        """
        try:
            org.get_catalog_item(catalog_name, template_name)
            print('Reusing existing template : ' + template_name)
            return False
        except EntityNotFoundException as e:
            bytes_uploaded = -1
            print('Uploading template : ' + template_name)
            bytes_uploaded = org.upload_ovf(
                catalog_name=catalog_name,
                file_name=template_file_name,
                item_name=template_name)
            self.assertNotEqual(bytes_uploaded, -1)
        return True

    def _template_import_monitor(self, client, org, catalog_name,
                                 template_name):
        """Helper method to block until a template is imported in vCD.

        :param client: An object of :class: `pyvcloud.vcd.client.Client` that
            would be used to make ReST calls to vCD.
        :param org: An object of :class:`lxml.objectify.StringElement`that
            describes the organization, which the templates is being imported
            into.
        :param catalog_name: (str): Name of the catalog to which the template
            is being imported.
        :param template_name: (str): Name of the catalog item which represents
            the uploaded template.

        :return: Nothing
        """
        print('Importing template : ' + template_name + ' in vCD')
        # wait for the catalog item import to finish in vCD
        catalog_item_resource = org.get_catalog_item(catalog_name,
                                                     template_name)
        template_resource = client.get_resource(
            catalog_item_resource.Entity.get('href'))
        client.get_task_monitor().wait_for_success(
            task=template_resource.Tasks.Task[0])

    def test_0010_download(self):
        """Test the method org.download_catalog_item().

        Download the two templates that were uploaded as part of setup.

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

    @developerModeAware
    def test_9998_teardown(self):
        """Test the  method delete_catalog_item() and delete_catalog().

        Invoke the methods for templates and catalogs created by setup.

        This test passes if none of the delete operations generate any
        exceptions.
        """
        org = Environment.get_test_org(TestCatalog._client)
        org.delete_catalog_item(TestCatalog._test_catalog_name,
                                TestCatalog._test_template_name)
        org.delete_catalog_item(
            TestCatalog._test_catalog_name,
            TestCatalog._test_template_with_chunk_size_name)
        org.delete_catalog(TestCatalog._test_catalog_name)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestCatalog._client.logout()


if __name__ == '__main__':
    unittest.main()
