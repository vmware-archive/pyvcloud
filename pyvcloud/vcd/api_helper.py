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

from datetime import date
from datetime import datetime
from enum import Enum
from importlib import import_module
import inspect
import json
import os
import re
import tempfile

from dateutil.parser import parse
from six import integer_types
from six import iteritems
from six import text_type
from vcloud.api.rest import schema_v1_5
from vcloud.api.rest.schema import ovf  # noqa: H306
from vcloud.api.rest.schema import versioning
from vcloud.api.rest.schema.ovf import environment  # noqa: H306
from vcloud.api.rest.schema.ovf import vmware  # noqa: H306
from vcloud.api.rest.schema_v1_5 import extension
from vcloud.api.rest.schema_v1_5.query_result_record_type import \
    QueryResultRecordType
from vcloud.rest.openapi import models
from vcloud.rest.openapi.models import session

from pyvcloud.vcd.client import ClientException


class ApiHelper(object):
    """Helper class to serialize and deserialize model objects.

    Model classes are in a thirt party library, vcd-api-schemas-type. REST API
    model classes are under vcloud.api.rest.* module. CloudAPI model classes
    are under vcloud.rest.openapi.models module. Both modules are scanned to
    find the right class for a given response type.
    """

    PRIMITIVE_TYPES = (float, bool, bytes, text_type) + integer_types
    NATIVE_TYPES_MAPPING = {
        'int': int,
        'long': int,
        'float': float,
        'str': str,
        'bool': bool,
        'date': date,
        'datetime': datetime,
        'object': object,
    }

    def __init__(self):
        """Constructor of the class."""
        # Load all cloudapi model classes in models
        for file in os.listdir(os.path.dirname(session.__file__)):
            mod_name = file[:-3]
            if mod_name.startswith('__'):
                continue
            module = import_module('vcloud.rest.openapi.models.' + mod_name)
            setattr(models, mod_name, module)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if inspect.isclass(obj):
                    setattr(models, name, obj)

    def sanitize_for_serialization(self, obj):
        """Builds a JSON POST object.

        If obj is None, return None.
        If obj is str, int, long, float, bool, return directly.
        If obj is datetime.datetime, datetime.date
            convert to string in iso8601 format.
        If obj is list, sanitize each element in the list.
        If obj is dict, return the dict.
        If obj is model, return the properties dict.

        :param obj: The data to serialize.
        :return: The serialized form of data.
        """
        if obj is None:
            return None
        elif isinstance(obj, self.PRIMITIVE_TYPES):
            return obj
        elif isinstance(obj, list):
            return [
                self.sanitize_for_serialization(sub_obj) for sub_obj in obj
            ]
        elif isinstance(obj, tuple):
            return tuple(
                self.sanitize_for_serialization(sub_obj) for sub_obj in obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()

        if isinstance(obj, dict):
            obj_dict = obj
        else:
            # Convert model obj to dict except
            # attributes `swagger_types`, `attribute_map`
            # and attributes which value is not None.
            # Convert attribute name to json key in
            # model definition for request.
            if isinstance(obj, Enum):
                return obj.value

            obj_dict = {}
            cls_tree = list(inspect.getmro(obj.__class__))
            cls_tree.remove(object)
            for cls in cls_tree:
                current_dict = {
                    cls.attribute_map[attr]: getattr(obj, attr)
                    for attr, _ in iteritems(cls.swagger_types)
                    if hasattr(obj, attr) and getattr(obj, attr) is not None
                }
                obj_dict.update(current_dict)

        return {
            key: self.sanitize_for_serialization(val)
            for key, val in iteritems(obj_dict)
        }

    def deserialize(self, response, response_type):
        """Deserializes response into an object.

        :param response: Response object to be deserialized.
        :param response_type: class literal for
            deserialized object, or string of class name.

        :return: deserialized object.
        """
        # handle file downloading
        # save response body into a tmp file and return the instance
        if response_type == "file":
            return self.__deserialize_file(response)

        # fetch data from response object
        try:
            data = json.loads(response.content)
        except ValueError:
            data = response.content

        return self.__deserialize(data, response_type)

    def __deserialize(self, data, klass):
        """Deserializes dict, list, str into an object.

        :param data: dict, list or str.
        :param klass: class literal, or string of class name.

        :return: object.
        """
        if data is None:
            return None

        if type(klass) == str:
            if klass.startswith('list['):
                sub_kls = re.match(r'list\[(.*)\]', klass).group(1)
                return [
                    self.__deserialize(sub_data, sub_kls) for sub_data in data
                ]

            if klass.startswith(r'dict('):
                sub_kls = re.match(r'dict\(([^,]*), (.*)\)', klass).group(2)
                return {
                    k: self.__deserialize(v, sub_kls)
                    for k, v in iteritems(data)
                }

            # convert str to class
            if klass in self.NATIVE_TYPES_MAPPING:
                klass = self.NATIVE_TYPES_MAPPING[klass]
            else:
                if hasattr(models, klass):
                    klass = getattr(models, klass)
                elif hasattr(schema_v1_5, klass):
                    klass = getattr(schema_v1_5, klass)
                elif hasattr(extension, klass):
                    klass = getattr(extension, klass)
                elif hasattr(ovf, klass):
                    klass = getattr(ovf, klass)
                elif hasattr(versioning, klass):
                    klass = getattr(versioning, klass)
                elif hasattr(environment, klass):
                    klass = getattr(environment, klass)
                elif hasattr(vmware, klass):
                    klass = getattr(vmware, klass)

        if klass in self.PRIMITIVE_TYPES:
            return self.__deserialize_primitive(data, klass)
        elif klass == object:
            return self.__deserialize_object(data)
        elif klass == date:
            return self.__deserialize_date(data)
        elif klass == datetime:
            return self.__deserialize_datatime(data)
        else:
            return self.__deserialize_model(data, klass)

    def __deserialize_file(self, response):
        """Saves response body into a file.

        Saves response in a temporary folder, using the filename from the
        `Content-Disposition` header if provided.

        :param response:  RESTResponse.
        :return: file path.
        """
        fd, path = tempfile.mkstemp()
        os.close(fd)
        os.remove(path)

        content_disposition = response.getheader("Content-Disposition")
        if content_disposition:
            filename = re.search(r'filename=[\'"]?([^\'"\s]+)[\'"]?',
                                 content_disposition).group(1)
            path = os.path.join(os.path.dirname(path), filename)

        with open(path, "w") as f:
            f.write(response.data)

        return path

    def __deserialize_primitive(self, data, klass):
        """Deserializes string to primitive type.

        :param data: str.
        :param klass: class literal.

        :return: int, long, float, str, bool.
        """
        try:
            return klass(data)
        except UnicodeEncodeError:
            return str(data)
        except TypeError:
            return data

    def __deserialize_object(self, value):
        """Return a original value.

        :return: object.
        """
        return value

    def __deserialize_date(self, string):
        """Deserializes string to date.

        :param string: str.
        :return: date.
        """
        try:
            return parse(string).date()
        except ImportError:
            return string
        except ValueError:
            raise ClientException(
                "Failed to parse `{0}` into a date object".format(string))

    def __deserialize_datatime(self, string):
        """Deserializes string to datetime.

        The string should be in iso8601 datetime format.

        :param string: str.
        :return: datetime.
        """
        try:
            return parse(string)
        except ImportError:
            return string
        except ValueError:
            raise ClientException(
                "Failed to parse `{0}` into a datetime object".format(string))

    def __deserialize_model(self, data, klass):
        """Deserializes list or dict to model.

        :param data: dict, list.
        :param klass: class literal.
        :return: model object.
        """
        if 'EnumMeta' == type(klass).__name__:
            return klass(data)
        if not klass.swagger_types:
            return data

        if klass == QueryResultRecordType:
            record_type = data.get('_type')
            klass = getattr(schema_v1_5, record_type)

        kwargs = {}
        cls_tree = list(inspect.getmro(klass))
        cls_tree.remove(object)
        for cls in cls_tree:
            for attr, attr_type in iteritems(cls.swagger_types):
                if data is not None and cls.attribute_map[
                        attr] in data and isinstance(data, (list, dict)):
                    value = data[cls.attribute_map[attr]]
                    kwargs[attr] = self.__deserialize(value, attr_type)

        instance = None
        if hasattr(models, klass.__name__):
            instance = klass(**kwargs)
        else:
            instance = klass()
            for key in kwargs:
                setattr(instance, key, kwargs[key])

        return instance
