import os

from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.ui_plugin import UiPlugin


class TestUIPlugin(TestCase):
    def test_0001_list(self):
        ui = UiPlugin(self.client._uri.split("/api")[0],
                      self.client._session.headers['x-vcloud-authorization'])

        try:
            ext_list = ui.getUiExtensions().json()
            assert type(ext_list) is list and len(ext_list) >= 0
        except Exception as e:
            assert type(e) is Exception

    def test_0002_deploy(self):
        ui = UiPlugin(self.client._uri.split("/api")[0],
                      self.client._session.headers['x-vcloud-authorization'])
        ui_ext_list = ui.getUiExtensions().json()

        try:
            if 'VCD_UI_PLUGIN_ROOT' in os.environ:
                ui.deploy(os.environ['VCD_UI_PLUGIN_ROOT'], publishAll=True,
                          preview=True)
            else:
                ui.deploy(os.getcwd(), publishAll=True, preview=True)
            ext_after_deploy = ui.getUiExtensions().json()
            assert len(ui_ext_list) <= len(ext_after_deploy)
        except Exception as e:
            assert type(e) is Exception

    def test_0003_delete_specific(self):
        ui = UiPlugin(self.client._uri.split("/api")[0],
                      self.client._session.headers['x-vcloud-authorization'])
        ui_ext_list = ui.getUiExtensions().json()

        # If UI extension status is not ready class will print -
        # Unable to delete plugin for [EXT_ID]

        try:
            ui.delete(specific=ui_ext_list[0]['id'])
            new_ui_ext_list = ui.getUiExtensions().json()
            assert len(new_ui_ext_list) < len(ui_ext_list)
        except Exception as e:
            assert type(e) is Exception

    def test_0004_delete_all(self):
        ui = UiPlugin(self.client._uri.split("/api")[0],
                      self.client._session.headers['x-vcloud-authorization'])

        # If there is no UI Extensions uploaded the class should print -
        # There is no UI extensions uploaded...
        # If UI extension status is not ready class will print -
        # Unable to delete plugin for [EXT_ID]

        try:
            ui.delete(deleteAll=True)
            new_ui_ext_list = ui.getUiExtensions().json()
            assert len(new_ui_ext_list) == 0
        except Exception as e:
            assert type(e) is Exception

    def test_0005_delete_specific_which_does_not_exist(self):
        ui = UiPlugin(self.client._uri.split("/api")[0],
                      self.client._session.headers['x-vcloud-authorization'])
        ui_ext_list = ui.getUiExtensions().json()

        # If UI extension status is not ready class will print -
        # Unable to delete plugin for [EXT_ID]

        try:
            ui.delete(specific="some_fake_id")
            new_ui_ext_list = ui.getUiExtensions().json()
            assert len(new_ui_ext_list) < len(ui_ext_list)
        except Exception as e:
            assert type(e) is Exception
