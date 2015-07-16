# VMware vCloud Python SDK
# Copyright (c) 2015 VMware, Inc. All Rights Reserved.
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

"""
Exception definitions.
"""


class ClientException(Exception):
    """
    The base exception class for all exceptions this library raises.
    """
    message = 'Unknown Error'

    def __init__(self, code, message=None, details=None,
                 url=None, method=None):
        self.code = code
        self.message = message or self.__class__.message
        self.details = details
        self.url = url
        self.method = method

    def __str__(self):
        formatted_string = "%s (HTTP %s)" % (self.message, self.code)
        return formatted_string


class BadRequest(ClientException):
    """
    HTTP 400 - Bad request: you sent some malformed data.
    """
    http_status = 400
    message = "Bad request"


class Unauthorized(ClientException):
    """
    HTTP 401 - Unauthorized: bad credentials.
    """
    http_status = 401
    message = "Unauthorized"


class Forbidden(ClientException):
    """
    HTTP 403 - Forbidden: your credentials don't give you access to this
    resource.
    """
    http_status = 403
    message = "Forbidden"


class NotFound(ClientException):
    """
    HTTP 404 - Not found
    """
    http_status = 404
    message = "Not found"


class MethodNotAllowed(ClientException):
    """
    HTTP 405 - Method Not Allowed
    """
    http_status = 405
    message = "Method Not Allowed"


class Conflict(ClientException):
    """
    HTTP 409 - Conflict
    """
    http_status = 409
    message = "Conflict"


# NotImplemented is a python keyword.
class HTTPNotImplemented(ClientException):
    """
    HTTP 501 - Not Implemented: the server does not support this operation.
    """
    http_status = 501
    message = "Not Implemented"


# In Python 2.4 Exception is old-style and thus doesn't have a __subclasses__()
# so we can do this:
#     _code_map = dict((c.http_status, c)
#                      for c in ClientException.__subclasses__())
#
# Instead, we have to hardcode it:
_error_classes = [BadRequest, Unauthorized, Forbidden, NotFound,
                  MethodNotAllowed, Conflict, HTTPNotImplemented]
_code_map = dict((c.http_status, c) for c in _error_classes)


def from_response(response):
    """
    Return an instance of an ClientException or subclass
    based on an requests response.
    Usage::
        resp, body = requests.request(...)
        if resp.status_code != 200:
            raise exception_from_response(resp, rest.text)
    """
    cls = _code_map.get(response.status_code, ClientException)

    kwargs = {
        'code': response.status_code,
        'method': response.request.method,
        'url': response.url,
    }
    return cls(**kwargs)
