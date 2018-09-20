import base64
import json
import os
import pprint

import requests


class UiPlugin(object):
    """A helper class to work with UI Extensions."""

    def __init__(self, vcduri, token):
        """Constructor for UiPlugin object.

        :param str vcduri: vCloud Director url
            where requests will be sent.
        :param str token: Authorization token
        """
        self._token = token
        self.vcduri = vcduri
        self.current_ui_extension = {}

    def __request(self, method, path=None, data=None, uri=None, auth=None,
                  content_type="application/json", accept="application/json"):
        """Make requests to vCloud Director with given method.

        If response status code is not in range 200 - 299 - raise Exception.

        :param str method: Request method
        :param str path: vCloud Director REST API route
        :param str data: Body of the request
        :param str uri: Exact url where the request will be made,
            note that uri is with secondary priority,
            if path is provided, uri will be ignored.
        :param str auth: Authorization token
        :param str content_type: Request content-type header,
            defaults to "application/json"
        :param str accept: Request accept header, defaults
            to "application/json"

        :return: response from the server.
        """
        headers = {}
        if self._token:
            headers['x-vcloud-authorization'] = self._token
        if auth:
            headers['Authorization'] = auth
        if content_type:
            headers['Content-Type'] = content_type
        if accept:
            headers['Accept'] = accept

        if path:
            uri = self.vcduri + path

        r = requests.request(method,
                             uri,
                             headers=headers,
                             data=data,
                             verify=False)
        if 200 <= r.status_code <= 299:
            return r
        raise Exception("""
        Unsupported HTTP status code (%d) encountered""" % (r.status_code))

    def getToken(self, username, org, password):
        """Make request to vCloud Director to get auth token.

        :param str username: vCloud Director username
        :param str org: vCloud Director org name
        :param str password: vCloud Director user password
        """
        r = self.__request('POST', '/api/sessions',
                           auth='Basic %s' % base64
                           .b64encode('%s@%s:%s' % (username, org, password)),
                           accept='application/*+xml;version=29.0')
        self._token = r.headers['x-vcloud-authorization']

    def getUiExtensions(self):
        """Get all UI extension.

        :return: Response with list of extensions
        """
        return self.__request('GET', '/cloudapi/extensions/ui/')

    def getUiExtension(self, eid):
        """Get specific UI extension.

        :param str eid: Extension id

        :return: UI extension metadata
        """
        return self.__request('GET', '/cloudapi/extensions/ui/%s' % (eid))

    def postUiExtension(self, data):
        """Register UI extension.

        :param str data: Data extracted from the extension manifest file (JSON)

        :return: UI extension metadata
        """
        return self.__request('POST', '/cloudapi/extensions/ui/',
                              json.dumps(data))

    def putUiExtension(self, eid, data):
        """Update UI extension manifest data.

        :param str eid: Extension id
        :param str data: New extension metadata (JSON)

        :return: UI extension metadata
        """
        return self.__request('PUT', '/cloudapi/extensions/ui/%s' % (eid),
                              json.dumps(data))

    def deleteUiExtension(self, eid):
        """Delete specific UI extension.

        :param str eid: Extension id
        :return: No Content
        """
        return self.__request('DELETE', '/cloudapi/extensions/ui/%s' % (eid))

    def postUiExtensionPlugin(self, eid, data):
        """Register UI extension zip file.

        :param str eid: Extension id
        :param str data: Data extracted from the
            extension manifest file (JSON)

        :return: Trnasfer Link in "Link" header
        """
        return self.__request('POST', '/cloudapi/extensions/ui/%s/plugin' %
                              (eid),
                              json.dumps(data))

    def putUiExtensionPlugin(self, uri, data):
        """Upload UI extension zip file.

        :param str uri: Uri where the request will be made
        :param File data: Extension zip file

        :return response from the server
        """
        return self.__request('PUT', uri=uri, content_type="application/zip",
                              accept=None, data=data)

    def deleteUiExtensionPlugin(self, eid):
        """Delete specific UI extension.

        :param str eid: Extension id

        :return: No Content
        """
        return self.__request('DELETE', '/cloudapi/extensions/ui/%s/plugin' %
                              (eid))

    def getUiExtensionTenants(self, eid):
        """Get all UI extensions available for tenants.

        :param str eid: Extension id

        :return: response from the server
        """
        return self.__request('GET', '/cloudapi/extensions/ui/%s/tenants' %
                              (eid))

    def postUiExtensionTenantsPublishAll(self, eid):
        """Publish UI extension for all tenants.

        :param str eid: Extension id

        :return: List of tenants where UI extension was published
        """
        return self.__request('POST',
                              '/cloudapi/extensions/ui/%s/tenants/publishAll' %
                              (eid))

    def postUiExtensionTenantsPublish(self, eid, data):
        """Publish UI extension for specific tenants.

        :param str eid: Extension id
        :param str data: List of dict with tenant id and name (JSON)

        :return: List of tenants where UI extension was published
        """
        return self.__request('POST',
                              '/cloudapi/extensions/ui/%s/tenants/publish' %
                              (eid), data)

    def postUiExtensionTenantsUnPublishAll(self, eid):
        """Unpublish UI extension for all tenants.

        :param str eid: Extension id

        :return: List of tenants where UI extension was unpublished
        """
        return self.__request('POST',
                              '/cloudapi/extensions/ui/%s/tenants/unpublishAll'
                              % (eid))

    def postUiExtensionTenantsUnPublish(self, eid, data):
        """Unpublish UI extension for specific tenants.

        :param str eid: Extension id
        :param str data: List of dict with tenant id and name (JSON)

        :return: List of tenants where UI extension was unpublished
        """
        return self.__request('POST',
                              '/cloudapi/extensions/ui/%s/tenants/unpublish' %
                              (eid), data)

    def postUiExtensionPluginFromFile(self, eid, fn):
        """Register UI extension zip file.

        :param str eid: Extension id
        :param str fn: File absolute path

        :return: response from the server
        """
        data = {
            "fileName": fn.split('/')[-1],
            "size": os.stat(fn).st_size
        }
        return self.postUiExtensionPlugin(eid, data)

    def putUiExtensionPluginFromFile(self, eid, fn):
        """Read UI extension zip file and upload it.

        :param str eid: Extension id
        :param str fn: File absolute path

        :return: response from the server
        """
        with open(fn, "rb") as f:
            return_data = self.putUiExtensionPlugin(eid, f.read())
            f.close()
            return return_data

    def deleteUiExtensionPluginSafe(self, eid):
        """Delete specific UI extension.

        If his extension status is ready,
        if not the action is denied.

        :param str eid: Extension id

        :return: response from the server
        """
        if self.current_ui_extension.get('plugin_status', None) == 'ready':
            return self.deleteUiExtensionPlugin(eid)
        else:
            print('Unable to delete plugin for %s' % eid)
            return None

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

        :param str data: Extension configuration. (JSON)
        :param str fn: File absolute path.
        :param boolean publishAll: Flag which determinate
            that extension will be published
            for all tenants after upload.
            False by default.
        """
        r = self.postUiExtension(data).json()
        eid = r['id']
        self.addPlugin(eid, fn, publishAll=publishAll)

    def addPlugin(self, eid, fn, publishAll=False):
        """Register extension zip file.

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

        :param str eid: Extension id
        """
        self.removePlugin(eid)
        self.deleteUiExtension(eid)

    def removePlugin(self, eid):
        """Remove specific UI Extension safely.

        :param str eid: Extension id
        """
        self.deleteUiExtensionPluginSafe(eid)

    def replacePlugin(self, eid, fn, publishAll=False):
        """Remove specific UI Extension and add new on his place.

        :param str eid: Extension id
        :param str fn: File absolute path.
        :param boolean publishAll: Flag which determinate
            that extension will be published
            for all tenants after upload.
            False by default.
        """
        self.removePlugin(eid)
        self.addPlugin(eid, fn, publishAll=publishAll)

    def deploy(self, basedir, publishAll=False, preview=False):
        """Starting UI Extension deploy process.

        While deploying if preview
        is turned on the UI Extension configuration
        will be shown in the terminal,
        after upload the extension will be
        published if publishAll flag is true.

        :param str basedir: Base directory of the extension.
        :param boolean publishAll: Flag which determinate that
            extension will be published
            for all tenants after upload.
        :param boolean preview: If true will show preview
            of the UI extension configuration.
        """
        manifest = self.parseManifest('%s/src/public/manifest.json' % basedir,
                                      enabled=True)

        if preview is True:
            pprint.pprint(manifest)

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

    def delete(self, specific=None, deleteAll=False,
               get_ext_id_dynamically=None):
        """Starting UI Extension delete process.

        If delete all flag
        is True all UI Extensions will be deleted,
        else the user will be promped which
        one he wants to delete.

        :param str specific: UI extension id
        :param boolean deleteAll: Flag which determines
            that all extensions will be deleted.
        :param function get_ext_id_dynamically: If
            UI extension id is not provided this function
            will be executed to get the id. I can
            prompt user for example.
        """
        if specific:
            self.removeExtension(specific)
            return

        if deleteAll is True:
            for ext in self.walkUiExtensions():
                try:
                    self.removeExtension(ext['id'])
                except Exception as e:
                    raise e
            return

        print("You have to specify which UI extension you want to delete.")
