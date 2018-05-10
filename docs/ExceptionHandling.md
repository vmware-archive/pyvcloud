Exception handling
==================

## Exception class hierarchy![Exception Class Hierarchy.jpg](Exception%20Class%20Hierarchy.jpg)

All exceptions thrown from pyvcloud is of type SDKExceptions or a subclass of it. 

#### SDKException: ####
   Base class for all exceptions thrown from pyvcloud. The exceptions can either originate from the client or from the VCD server.
   
#### VcdException: ####
   Base class of all exceptions related to vcd. It can be either due to the error response code of the vcd server or the 

#### ClientException: ####

#### VcdResponseException: ####

#### : ####



   
