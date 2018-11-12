import json
import os

from pyvcloud.vcd.exceptions import InvalidParameterException


def validateExtId(eid):
    if eid is None:
        raise InvalidParameterException("Extension id is required.")

    if isinstance(eid, str) is not True:
        raise InvalidParameterException("Extension id has to be str.")


class UiPlugin(object):
    """A helper class to work with UI Extensions."""

    def __init__(self, client):
        """Constructor for UiPlugin object.

        :param str vcduri: vCloud Director uri
            where requests will be sent.
        :param object client: pyvcloud Client
        """
        self.client = client
        self.vcduri = self.client.get_api_uri().split("/api")[0]
        self.current_ui_extension = {}

    def getUiExtensions(self):
        """Get all UI extension.

        :return: Response list of extensions
        """
        uri = '%s/cloudapi/extensions/ui/' % (self.vcduri)

        return self.client.get_ui_extension(uri, None, 'application/json',
                                            'application/json')

    def getUiExtension(self, eid):
        """Get specific UI extension.

        Raise InvalidParameterException
        if eid is not provided or it isn't str.

        :param str eid: Extension id

        :return: UI extension metadata
        """
        validateExtId(eid)

        uri = '%s/cloudapi/extensions/ui/%s' % (self.vcduri, eid)

        return self.client.get_ui_extension(uri, None, 'application/json',
                                            'application/json')

    def postUiExtension(self, data):
        """Register UI extension.

        Raise InvalidParameterException
        if data is not provided or it isn't dict.

        :param dict data: Data extracted from the extension manifest
        file (JSON)

        :return: UI extension metadata in json
        """
        if data is None or \
           isinstance(data, dict) is not True:
            raise InvalidParameterException(
                "Register ui extension expect data to be dict."
            )

        uri = '%s/cloudapi/extensions/ui/' % (self.vcduri)

        return self.client.post_ui_extension(uri,
                                             json.dumps(data),
                                             'application/json',
                                             'application/json')

    def putUiExtension(self, eid, data):
        """Update UI extension manifest data.

        Raise InvalidParameterException
        if eid is not provided or it isn't str and if data is not
        provided or it isn't dict.

        :param str eid: Extension id
        :param dict data: New extension metadata

        :return: UI extension metadata
        """
        validateExtId(eid)

        if data is None or \
           isinstance(data, dict) is not True:
            raise InvalidParameterException(
                """Update UI extension manifest data
                expect all params to be provided."""
            )

        uri = '%s/cloudapi/extensions/ui/%s' % (self.vcduri, eid)

        return self.client.put_ui_extension(uri,
                                            json.dumps(data),
                                            'application/json',
                                            'application/json')

    def deleteUiExtension(self, eid):
        """Delete specific UI extension.

        Raise InvalidParameterException
        if eid is not provided or it isn't str.

        :param str eid: Extension id
        :return: No Content
        """
        validateExtId(eid)

        uri = '%s/cloudapi/extensions/ui/%s' % (self.vcduri, eid)

        return self.client.delete_ui_extension(uri,
                                               None,
                                               'application/json',
                                               'application/json')

    def postUiExtensionPlugin(self, eid, data):
        """Register UI extension zip file.

        Raise InvalidParameterException
        if eid is not provided or it isn't str and if data is
        not dict.

        :param str eid: Extension id
        :param dict data: Data extracted from the
            extension manifest file

        :return: Response object with Trnasfer Link header with name "Link"
        """
        validateExtId(eid)

        if data is None or \
           isinstance(data, dict) is not True:
            raise InvalidParameterException(
                """Register UI extension zip file
                expect all params to be provided."""
            )

        uri = '%s/cloudapi/extensions/ui/%s/plugin' % (self.vcduri, eid)

        return self.client.post_ui_extension(uri,
                                             json.dumps(data),
                                             'application/json',
                                             'application/json')

    def putUiExtensionPlugin(self, uri, data):
        """Upload UI extension zip file.

        Raise InvalidParameterException
        if uri is not provided or it isn't str and if
        data is not provided or from bytes datatype.

        :param str uri: Uri where the request will be made
        :param File data: Extension zip file

        :return Response object
        """
        if uri is None or \
           isinstance(uri, str) is not True or \
           data is None or \
           isinstance(data, bytes) is not True:
            raise InvalidParameterException(
                """Upload UI extension zip file expect
                all params to be provided."""
            )

        return self.client.put_ui_extension(uri,
                                            data,
                                            'application/zip',
                                            'application/json')

    def deleteUiExtensionPlugin(self, eid):
        """Delete specific UI extension.

        Raise InvalidParameterException
        if eid is not provided or it isn't str.

        :param str eid: Extension id

        :return: No Content
        """
        validateExtId(eid)

        uri = '%s/cloudapi/extensions/ui/%s/plugin' % (self.vcduri, eid)

        return self.client.delete_ui_extension(uri,
                                               None,
                                               'application/json',
                                               'application/json')

    def getUiExtensionTenants(self, eid):
        """Get all UI extensions available for tenants.

        Raise InvalidParameterException
        if eid is not provided or it isn't str.

        :param str eid: Extension id

        :return: response from the server
        """
        validateExtId(eid)

        uri = '%s/cloudapi/extensions/ui/%s/tenants' % (self.vcduri, eid)

        return self.client.get_ui_extension(uri, None, 'application/json',
                                            'application/json')

    def postUiExtensionTenantsPublishAll(self, eid):
        """Publish UI extension for all tenants.

        Raise InvalidParameterException
        if eid is not provided or it isn't str.

        :param str eid: Extension id

        :return: List of tenants where UI extension was published
        """
        validateExtId(eid)

        uri = '%s/cloudapi/extensions/ui/%s/tenants/publishAll' % \
              (self.vcduri, eid)

        return self.client.post_ui_extension(uri,
                                             None,
                                             'application/json',
                                             'application/json')

    def postUiExtensionTenantsPublish(self, eid, data):
        """Publish UI extension for specific tenants.

        Raise InvalidParameterException
        if eid is not provided or it isn't str and
        if data is not from dict datatype.

        :param str eid: Extension id
        :param str data: List of dict with tenant id and name

        :return: List of tenants where UI extension was published
        """
        validateExtId(eid)

        if isinstance(data, dict) is not True:
            raise InvalidParameterException(
                """Publish UI extension for specific
                tenants expect data to be dict."""
            )

        uri = '%s/cloudapi/extensions/ui/%s/tenants/publish' % \
              (self.vcduri, eid)

        return self.client.post_ui_extension(uri,
                                             json.dumps(data),
                                             'application/json',
                                             'application/json')

    def postUiExtensionTenantsUnPublishAll(self, eid):
        """Unpublish UI extension for all tenants.

        Raise InvalidParameterException
        if eid is not provided or it isn't str.

        :param str eid: Extension id

        :return: List of tenants where UI extension was unpublished
        """
        validateExtId(eid)

        uri = '%s/cloudapi/extensions/ui/%s/tenants/unpublishAll' % \
              (self.vcduri, eid)

        return self.client.post_ui_extension(uri,
                                             None,
                                             'application/json',
                                             'application/json')

    def postUiExtensionTenantsUnPublish(self, eid, data):
        """Unpublish UI extension for specific tenants.

        Raise InvalidParameterException
        if eid is not provided or it isn't str and
        if data is not from dict datatype.

        :param str eid: Extension id
        :param dict data: List of dict with tenant id and name

        :return: List of tenants where UI extension was unpublished
        """
        validateExtId(eid)

        if isinstance(data, dict) is not True:
            raise InvalidParameterException(
                """Unpublish UI extension for specific
                tenants expect data to be dict."""
            )

        uri = '%s/cloudapi/extensions/ui/%s/tenants/unpublish' % \
              (self.vcduri, eid)

        return self.client.post_ui_extension(uri,
                                             json.dumps(data),
                                             'application/json',
                                             'application/json')

    def postUiExtensionPluginFromFile(self, eid, fn):
        """Register UI extension zip file.

        Raise InvalidParameterException
        if eid is not provided or it isn't str.

        :param str eid: Extension id
        :param str fn: File absolute path

        :return: response from the server
        """
        validateExtId(eid)

        data = {
            "fileName": fn.split('/')[-1],
            "size": os.stat(fn).st_size
        }
        return self.postUiExtensionPlugin(eid, data)

    def putUiExtensionPluginFromFile(self, eid, fn):
        """Read UI extension zip file and upload it.

        Raise InvalidParameterException
        if eid is not provided or it isn't str.

        :param str eid: Extension id
        :param str fn: File absolute path

        :return: response from the server
        """
        validateExtId(eid)

        with open(fn, "rb") as f:
            return_data = self.putUiExtensionPlugin(eid, f.read())
            f.close()
            return return_data

    def deleteUiExtensionPluginSafe(self, eid):
        """Delete specific UI extension.

        Raise InvalidParameterException
        if eid is not provided or it isn't str.
        If his extension status is ready,
        if not the action is denied.

        :param str eid: Extension id

        :return: Response object
        """
        validateExtId(eid)

        if self.current_ui_extension.get('plugin_status', None) == 'ready':
            return self.deleteUiExtensionPlugin(eid)
        else:
            raise Exception('Unable to delete plugin for %s' % eid)

    def walkUiExtensions(self):
        """Loop through list of UI extension.

        Yield on each of them.

        :return: UI extension object
        """
        for ext in self.getUiExtensions().json():
            self.current_ui_extension = ext
            yield ext

    def parseManifest(self, fn, enabled=True):
        """Read UI Extension manifest json file.

        Populate date which is used to register
        the extension.

        :param str fn: File absolute path
        :param boolean enabled: Define extension as enabled.

        :return: UI extension register dict
        """
        with open(fn, "r") as f:
            data = json.load(f)
            result = {
                "pluginName": data['name'],
                "vendor": data['vendor'],
                "description": data['description'],
                "version": data['version'],
                "license": data['license'],
                "link": data['link'],
                "tenant_scoped": "tenant" in data['scope'],
                "provider_scoped": "service-provider" in data['scope'],
                "enabled": enabled
            }
            f.close()
            return result

    def addExtension(self, data, fn, publishAll=False):
        """Register and upload UI extension.

        Raise InvalidParameterException
        if data is not provided or it isn't from dict datatype.

        :param dict data: Extension configuration.
        :param str fn: File absolute path.
        :param boolean publishAll: Flag which determinate
            that extension will be published
            for all tenants after upload.
            False by default.
        """
        if data is None or \
           isinstance(data, dict) is not True:
            raise InvalidParameterException(
                """Register and upload UI extension expect data to be dict."""
            )

        r = self.postUiExtension(data).json()
        eid = r['id']
        self.addPlugin(eid, fn, publishAll=publishAll)

    def addPlugin(self, eid, fn, publishAll=False):
        """Register extension zip file.

        Raise InvalidParameterException
        if eid is not provided or it isn't str.
        Get transfer link, upload file
        and ublish the ui extension for all,
        if it's specified.

        :param str eid: Extension id
        :param str fn: File absolute path.
        :param boolean publishAll: Flag which determinate
            that extension will be published
            for all tenants after upload.
            False by default.
        """
        validateExtId(eid)

        r = self.postUiExtensionPluginFromFile(eid, fn)
        link = r.headers["Link"].split('>')[0][1:]

        self.putUiExtensionPluginFromFile(link, fn)

        if publishAll:
            self.postUiExtensionTenantsPublishAll(eid)

    def removeAllUiExtensions(self):
        """Delete all UI Extensions."""
        for ext in self.walkUiExtensions():
            self.removeExtension(ext['id'])

    def removeExtension(self, eid):
        """Remove specific UI Extension.

        Raise InvalidParameterException
        if eid is not provided or it isn't str.

        :param str eid: Extension id
        """
        validateExtId(eid)

        self.removePlugin(eid)
        self.deleteUiExtension(eid)

    def removePlugin(self, eid):
        """Remove specific UI Extension safely.

        Raise InvalidParameterException
        if eid is not provided or it isn't str.

        :param str eid: Extension id
        """
        validateExtId(eid)

        self.deleteUiExtensionPluginSafe(eid)

    def replacePlugin(self, eid, fn, publishAll=False):
        """Remove specific UI Extension and add new on his place.

        Raise InvalidParameterException if eid is not provided or it isn't str.

        :param str eid: Extension id
        :param str fn: File absolute path.
        :param boolean publishAll: Flag which determinate
            that extension will be published
            for all tenants after upload.
            False by default.
        """
        validateExtId(eid)

        self.removePlugin(eid)
        self.addPlugin(eid, fn, publishAll=publishAll)

    def deploy(self, basedir, publishAll=False, preview=False):
        """Starting UI Extension deploy process.

        While deploying if preview
        is turned on the UI Extension configuration
        will be returned, after upload the extension will be
        published if publishAll flag is true.

        :param str basedir: Base directory of the extension.
        :param boolean publishAll: Flag which determinate that
            extension will be published
            for all tenants after upload.
        :param boolean preview: If true will return preview
            of the UI extension configuration otherwise None will be returned.
        """
        manifest = self.parseManifest('%s/src/public/manifest.json' % basedir,
                                      enabled=True)

        eid = None
        for ext in self.walkUiExtensions():
            is_with_same_name = manifest['pluginName'] == ext['pluginName']
            if is_with_same_name and manifest['version'] == ext['version']:
                eid = ext['id']
                break

        if not eid:
            self.addExtension(manifest, '%s/dist/plugin.zip' % basedir,
                              publishAll=publishAll)
        else:
            self.replacePlugin(eid, '%s/dist/plugin.zip' % basedir,
                               publishAll=publishAll)

        return manifest if preview is True else None

    def delete(self, specific=None, deleteAll=False):
        """Starting UI Extension delete process.

        If delete all flag is True all
        UI Extensions will be deleted,
        else the user will be promped which
        one he wants to delete.

        :param str specific: UI extension id
        :param boolean deleteAll: Flag which determines
            that all extensions will be deleted.
        """
        if specific:
            self.current_ui_extension = self.getUiExtension(specific).json()
            self.removeExtension(self.current_ui_extension['id'])
            return

        if deleteAll is True:
            for ext in self.walkUiExtensions():
                try:
                    self.removeExtension(ext['id'])
                except Exception as e:
                    raise e
            return

        raise Exception(
            "You have to specify which UI extension you want to delete."
        )
