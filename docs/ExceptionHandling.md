Exception handling
==================

## Exception class hierarchy![Exception Class Hierarchy.jpg](Exception%20Class%20Hierarchy.jpg)

All exceptions thrown from pyvcloud are of type SDKExceptions or a subclass of it. 

### SDKException: ###
   Base class for all exceptions thrown from pyvcloud. The exceptions can either originate from the client (ClientException) or from the VCD server(VcdException). 
   
   ---
   
### VcdException: ###
   Base class of all exceptions related to vcd. It can be either due to the error response code from the vcd server or due to the state of the vcd entities. Retrying on a VcdException exception might work if the underlying issue in vcd is resolved.


#### VcdResponseException: ####
   Base class for all exception raised due to an error response code from vcd. This exception gives information about status_code, vcd_error and request_id. Depending on the status_code, subclass of VcdResponseException is thrown as below.
   
| status_code   | Exception Type                 |
| ------------- | -------------------------------|
| 400           | BadRequestException            |
| 401           | UnauthorizedException          |
| 403           | AccessForbiddenException       |
| 404           | NotFoundException              |
| 405           | MethodNotAllowedException      |
| 406           | NotAcceptableException         |
| 408           | RequestTimeoutException        |
| 409           | ConflictException              |
| 415           | UnsupportedMediaTypeException  |
| 416           | InvalidContentLengthException  |
| 500           | InternalServerException        |
| unknown       | UnknownApiException            |
 
 
#### LinkException: ####
   Base class for vcd links related Exceptions.

#### MultipleLinksException: ####
   Raised when multiple link of same type is present in vcd response.

#### MissingLinkException: ####
   Raised when a link is missing from the vcd response.

#### RecordException: ####
   Base class for vcd records related exceptions.

#### MissingRecordException: ####
   Raised when a record is missing in vcd.

#### MultipleRecordsException: ####
   Raised when multiple records are present in vcd.

#### VcdTaskException: ####
   Exception related to tasks in vcd.

#### EntityNotFoundException: ####
   Raised when an entity is not found in vcd.

#### UploadException: ####
   Raised when upload of an entity fails in vcd.

#### DownloadException: ####
   Raised when download of an entity fails in vcd.

#### InvalidStateException: ####
   Raised when the state of an entity in vcd is not valid.

#### OperationNotSupportedException: ####
   Raised when a particular operation is not supported in vcd.

#### AuthenticationException: ####
   Raised when authentication fails in vcd.  

#### AlreadyExistsException: ####
   Raised when an entity already exists in vcd.
   
   ---


### ClientException: ###
   Base class for all exceptions arising in the client(pyvcloud). Retrying on a ClientException will not work.
   
#### TaskTimeoutException: ####
   Raised when a task in vcd times out.

#### SDKRequestException:  ####
   Raised when an exception occurs during vcd request.

#### ValidationError:    ####
   Raised when validation error occurs in pyvcloud.

#### MissingParametersError:  ####
   Raised when a parameter is missing in pyvcloud.

#### InvalidParameterException:  ####
   Raised when a parameter is invalid in pyvcloud.

#### SessionException:  ####
   Raised for any session related exceptions in pyvcloud.


   
