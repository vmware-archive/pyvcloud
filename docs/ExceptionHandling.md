Exception handling
==================

## Exception class hierarchy![Exception Class Hierarchy.jpg](Exception%20Class%20Hierarchy.jpg)

All exceptions thrown from pyvcloud is of type SDKExceptions or a subclass of it. 

#### SDKException: ####
   Base class for all exceptions thrown from pyvcloud. The exceptions can either originate from the client (ClientException) or from the VCD server(VcdException). 
   
#### VcdException: ####
   Base class of all exceptions related to vcd. It can be either due to the error response code from the vcd server or due to the state of the vcd entities. Retrying on a VcdException exception might work if the underlying issue in vcd is resolved.


#### VcdResponseException: ####
   Base class for all exception raised due to an error response code from vcd. This exception gives information about status_code, vcd_error and request_id. Depending on the status_code, subclass of VcdResponseException is thrown as below.
   
| status_code   | Exception Type                |
| ------------- | ------------------------------|
| 400           | BadRequestException           |
| 401           | UnauthorizedException           |
| 403           | AccessForbiddenException           |
| 404           | NotFoundException           |
| 405           | MethodNotAllowedException           |
| 406           | NotAcceptableException           |
| 408           | RequestTimeoutException           |
| 409           | ConflictException           |
| 415           | UnsupportedMediaTypeException           |
| 416           | InvalidContentLengthException           |
| 500           | InternalServerException           |
| unknown       | UnknownApiException           |
         
        
         
         
             

#### : ####

#### ClientException: ####
   Base class for all exceptions arising in the client(pyvcloud). Retrying on a ClientException will not work.



   
