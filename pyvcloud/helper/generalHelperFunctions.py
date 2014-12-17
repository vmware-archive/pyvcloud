# VMware vCloud Python SDK
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
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

import sys, time
import requests
from pyvcloud.schema.vcd.v1_5.schemas.vcloud import taskType
from StringIO import StringIO
import json
import xmltodict
from tabulate import tabulate

# this method takes in the error message and print the error
# in either table format or json format
def print_error(msg, output_json):
    error = {"Errorcode" : "1", "Details" : msg}
    if output_json:
        print json.dumps(error, sort_keys=True, indent=4, separators=(',', ': '))
    else:
        print tabulate(error.items(), tablefmt="grid")

def remove_error_unwanted_keys(error_dict):
    # if there are more unwanted error keys, add them to this table
    removed_keys = ["@xmlns", "@xmlns:xsi", "@xsi:schemaLocation"]
    for key in error_dict["Error"]:
        if key in removed_keys:
            del error_dict["Error"][key]

# this method takes in the string representation of error (in xml form)
# and print the error in either table format or json format
def print_xml_error(error_xml, output_json):
    error_dict = xmltodict.parse(error_xml)
    remove_error_unwanted_keys(error_dict)
    error_dict["Error"]["Errorcode"] = "1"
    if output_json:
        print json.dumps(error_dict["Error"], sort_keys=True, indent=4, separators=(',', ': '))
    else:
        print tabulate(error_dict["Error"].items(), tablefmt="grid")

# this method takes in headers of a table and a list of table rows
# and print the table in json format
def print_json(obj, headers, table):
    data = [dict(zip(headers, row)) for row in table]
    print json.dumps({"Errorcode" : "0" , obj : data}, sort_keys=True, indent=4, separators=(',', ': '))

# this method remove all uncessary (key, value) pair from task object
def remove_task_unwanted_keys(task_dict):
    # all unwanted keys that we don't want to display for task
    removed_keys = ["expiryTime", "cancelRequested", "id", "name", "operation",
                   "operationName", "serviceNamespace", "type", "xmlns",
                   "xmlns:xsi", "xsi:schemaLocation", "Details",
                   "Organization", "Owner", "User"]
    for removed_key in removed_keys:
        for key in task_dict["Task"]:
            if removed_key in key:
                del task_dict["Task"][key]
                break

# this method takes in a string representation of task (in xml format)
# and return it in json format (with certain unnessary keys removed)
def task_json(task_xml):
    task_dict = xmltodict.parse(task_xml)
    remove_task_unwanted_keys(task_dict)
    # add error message (0 means no error and 1 means error)
    task_dict["Errorcode"] = "0"
    return json.dumps(task_dict, sort_keys=True, indent=4, separators=(',', ': '))

# this method takes in a string representation of task (in xml format)
# and return it in table format (with certain unnessary keys removed)
def task_table(task_xml):
    task_dict = xmltodict.parse(task_xml)
    remove_task_unwanted_keys(task_dict)
    # modify link so that it can be printed on the table
    for key in task_dict["Task"]:
        if "Link" in key:
            rel = [task_dict["Task"][key][link_key] for link_key in task_dict["Task"][key] if "rel" in link_key][0]
            href = [task_dict["Task"][key][link_key] for link_key in task_dict["Task"][key] if "href" in link_key][0]
            task_dict["Task"][rel] = href
            del task_dict["Task"][key]
    # add error message (0 means no error and 1 means error)
    table = task_dict["Task"].items()
    return tabulate(table, tablefmt="grid")
    
# this method converts python object into string
def convertPythonObjToStr(obj, name, namespace = '', namespacedef= ''):
    # Store the reference so that we can show things again in standard output
    old_stdout = sys.stdout
    # This variable will store everything that is sent to the standard output
    result = StringIO()
    sys.stdout = result
    obj.export(sys.stdout, 0, name_ = name, namespace_ = namespace, namespacedef_ = namespacedef ,pretty_print=False)
    # Redirect again the std output to screen
    sys.stdout = old_stdout
    # Then, get the stdout like a string
    return result.getvalue()

# display progress of a task. If json is true then print task in json format
# else print task in table format
def display_progress(task, json, headers):
# def display_progress(task, name, success_msg, headers):
    # If the task state is "running", then this property contains a progress
    # measurement, expressed as percentage completed, from 0 to 100.
    # If this property is not set, then the command does not report progress.
    progress = task.get_Progress()
    # can be: error (When a running task has encountered an error), queued
    # (When there are too many tasks for threads to handle), running (When
    # the busy thread is freed from its current task by finishing the task,
    # it picks a queued task to run. Then the queued tasks are marked as running)
    # and success (When a running task has completed).
    status = task.get_status()
    # number of rounds the while loop repeats
    rnd = 0
    # display progress bar
    while status != "success":
        if status == "error":
            error = task.get_Error()
            print_xml_error(convertPythonObjToStr(error, name = "Error"), json)
            return
        else:
            # some task doesn't not report progress
            if progress:
                sys.stdout.write("\rprogress : ["+"*"*int(progress)+" "*(100-int(progress-1))+"] "+str(progress)+" %")
            else:
                sys.stdout.write("\rprogress : ")
                if rnd % 4 == 0:
                    sys.stdout.write("["+"*"*25+" "*75+"]")
                elif rnd % 4 == 1:
                    sys.stdout.write("["+" "*25+"*"*25+" "*50+"]")
                elif rnd % 4 == 2:
                    sys.stdout.write("["+" "*50+"*"*25+" "*25+"]")
                elif rnd % 4 == 3:
                    sys.stdout.write("["+" "*75+"*"*25+"]")
                rnd += 1
            sys.stdout.flush()
            time.sleep(1)
            response = requests.get(task.get_href(), headers = headers)
            task = taskType.parseString(response.content, True)
            progress = task.get_Progress()
            status = task.get_status()
    # erase progress bar
    sys.stdout.write("\r" + " "*120)
    sys.stdout.flush()
    # display result
    if json:
        sys.stdout.write("\r" + task_json(response.content) + '\n')
    else:
        sys.stdout.write("\r" + task_table(response.content) + '\n')
    sys.stdout.flush()

def statusn1():
    return "Could not be created"
def status0():
    return "Unresolved"
def status1():
    return "Resolved"
def status2():
    return "Deployed"
def status3():
    return "Suspended"
def status4():
    return "Powered on"
def status5():
    return "Waiting for user input"
def status6():
    return "Unknown state"
def status7():
    return "Unrecognized state"
def status8():
    return "Powered off"
def status9():
    return "Inconsistent state"
def status10():
    return "Children do not all have the same status"
def status11():
    return "Upload initiated, OVF descriptor pending"
def status12():
    return "Upload initiated, copying contents"
def status13():
    return "Upload initiated , disk contents pending"
def status14():
    return "Upload has been quarantined"
def status15():
    return "Upload quarantine period has expired"
status = {-1 : statusn1,
           0 : status0,
           1 : status1,
           2 : status2,
           3 : status3,
           4 : status4,
           5 : status5,
           6 : status6,
           7 : status7,
           8 : status8,
           9 : status9,
           10 : status10,
           11 : status11,
           12 : status12,
           13 : status13,
           14 : status14,
           15 : status15,
            }
def get_disk_status_string(code):
    if '1' == code:
        return 'Ready'
    else:
        return 'unknown'
        
def get_disk_bus_type_string(code):
    if '6' == code:
        return 'SCSI'
    else:
        return 'unknown'       
        
def get_disk_bus_sub_type_string(code):
    if 'lsilogic' == code:
        return 'LSI Logic Parallel'
    else:
        return 'unknown'              
        
        
        
