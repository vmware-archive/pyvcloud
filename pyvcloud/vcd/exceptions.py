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


class SDKException(Exception):
    """Base class for all pyvcloud Exceptions."""


class VcdException(SDKException):
    """Base class for all vcd related Exceptions."""


class ClientException(SDKException):
    """Base class for all exceptions arising in the client(pyvcloud)."""


class VcdResponseException(VcdException):
    """Base class for all vcd response related Exceptions."""

    def __init__(self, status_code, request_id, vcd_error):
        self.status_code = status_code
        self.vcd_error = vcd_error
        self.request_id = request_id

    def __str__(self):
        return \
            'Status code: ' + \
            (('%d, <empty response body>' % self.status_code)
             if self.vcd_error is None else
             ('%d/%s, %s' %
              (self.status_code,
               self.vcd_error.get('minorErrorCode'),
               self.vcd_error.get('message')))) + \
            (' (request id: %s)' % self.request_id)


class LinkException(VcdException):
    """Base class for vcd links related Exceptions."""

    def __init__(self, href, rel, media_type):
        self.href = href
        self.rel = rel
        self.media_type = media_type

    def __str__(self):
        return '%s; href: %s, rel: %s, mediaType: %s' % \
               (super(LinkException, self).__str__(),
                self.href,
                self.rel,
                self.media_type)


class MultipleLinksException(LinkException):
    """Raised when multiple links are present in vcd response."""

    def __init__(self, href, rel, media_type):
        super(MultipleLinksException, self).__init__(href, rel, media_type)


class MissingLinkException(LinkException):
    """Raised when a link is missing from the vcd response."""

    def __init__(self, href, rel, media_type):
        super(MissingLinkException, self).__init__(href, rel, media_type)


class RecordException(VcdException):
    """Base class for vcd records related exception."""


class MissingRecordException(RecordException):
    """Raised when a record is missing in vcd."""


class MultipleRecordsException(RecordException):
    """Raised when multiple records are present in vcd."""


class VcdTaskException(VcdException):
    """Exception related to tasks in vcd."""

    def __init__(self, error_message, vcd_error):
        self.error_message = error_message
        self.vcd_error = vcd_error

    def __str__(self):
        return \
            'VcdTaskException; %s/%s: %s (%s)' % \
            (self.vcd_error.get('majorErrorCode'),
             self.vcd_error.get('minorErrorCode'),
             self.error_message,
             self.vcd_error.get('message'))


class EntityNotFoundException(VcdException):
    """Raised when an entity is not found in vcd."""


class UploadException(VcdException):
    """Raised when upload of an entity fails in vcd."""


class DownloadException(VcdException):
    """Raised when download of an entity fails in vcd."""


class InvalidStateException(VcdException):
    """Raised when the state of an entity in vcd is not valid."""


class OperationNotSupportedException(VcdException):
    """Raised when a particular operation is not supported in vcd."""


class AuthenticationException(VcdException):
    """Raised when authentication fails in vcd."""


class AlreadyExistsException(VcdException):
    """Raised if we try to create an already existing entity in vcd."""


class BadRequestException(VcdResponseException):
    """Raised when vcd returns 400 response code."""

    def __init__(self, status_code, request_id, vcd_error):
        super(BadRequestException, self).__init__(status_code, request_id,
                                                  vcd_error)


class UnauthorizedException(VcdResponseException):
    """Raised when vcd returns 401 response code."""

    def __init__(self, status_code, request_id, vcd_error):
        super(UnauthorizedException, self).__init__(status_code, request_id,
                                                    vcd_error)


class AccessForbiddenException(VcdResponseException):
    """Raised when vcd returns 403 response code."""

    def __init__(self, status_code, request_id, vcd_error):
        super(AccessForbiddenException, self).__init__(status_code,
                                                       request_id,
                                                       vcd_error)


class NotFoundException(VcdResponseException):
    """Raised when vcd returns 404 response code."""

    def __init__(self, status_code, request_id, vcd_error):
        super(NotFoundException, self).__init__(status_code, request_id,
                                                vcd_error)


class MethodNotAllowedException(VcdResponseException):
    """Raised when vcd returns 405 response code."""

    def __init__(self, status_code, request_id, vcd_error):
        super(MethodNotAllowedException, self).__init__(status_code,
                                                        request_id,
                                                        vcd_error)


class NotAcceptableException(VcdResponseException):
    """Raised when vcd returns 406 response code."""

    def __init__(self, status_code, request_id, vcd_error):
        super(NotAcceptableException, self).__init__(status_code, request_id,
                                                     vcd_error)


class RequestTimeoutException(VcdResponseException):
    """Raised when vcd returns 408 response code."""

    def __init__(self, status_code, request_id, vcd_error):
        super(RequestTimeoutException, self).__init__(status_code, request_id,
                                                      vcd_error)


class ConflictException(VcdResponseException):
    """Raised when vcd returns 409 response code."""

    def __init__(self, status_code, request_id, vcd_error):
        super(ConflictException, self).__init__(status_code,
                                                request_id,
                                                vcd_error)


class UnsupportedMediaTypeException(VcdResponseException):
    """Raised when vcd returns 415 response code."""

    def __init__(self, status_code, request_id, vcd_error):
        super(UnsupportedMediaTypeException, self).__init__(status_code,
                                                            request_id,
                                                            vcd_error)


class InvalidContentLengthException(VcdResponseException):
    """Raised when vcd returns 416 response code."""

    def __init__(self, status_code, request_id, vcd_error):
        super(InvalidContentLengthException, self).__init__(status_code,
                                                            request_id,
                                                            vcd_error)


class InternalServerException(VcdResponseException):
    """Raised when vcd returns 500 response code."""

    def __init__(self, status_code, request_id, vcd_error):
        super(InternalServerException, self).__init__(status_code, request_id,
                                                      vcd_error)


class UnknownApiException(VcdResponseException):
    """Raised when vcd returns an unknown response code."""

    def __init__(self, status_code, request_id, vcd_error):
        super(UnknownApiException, self).__init__(status_code, request_id,
                                                  vcd_error)


class TaskTimeoutException(ClientException, TimeoutError):
    """Raised when a task in vcd timeout."""


class SDKRequestException(ClientException, IOError):
    """Raised when an exception occurred during vcd request."""


class ValidationError(ClientException):
    """Raised when validation error occurs in pyvcloud."""


class MissingParametersError(ClientException):
    """Raised when a parameter is missing in pyvcloud."""


class InvalidParameterException(ClientException):
    """Raised when a parameter is invalid in pyvcloud."""


class SessionException(ClientException):
    """Raised for any session related exceptions in pyvcloud."""
