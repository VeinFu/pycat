#! /usr/bin/python

"""
Test Item for SES I2C /write/check
"""

from lxml import etree


import copy

import binascii

import os


import time
import sqlalchemy
from serial import Serial
import pmcses
import subprocess

from pycat import log, testcase, status
#from command import *
from basicplugin import command




from pycat import transfer


from pycat import log, testcase

_LOGGER = log.getLogger("log.tc")

#--------------------------------------------------------------------------
#  I2C condition check
#--------------------------------------------------------------------------

class I2CCondition(object):
    def __init__(self, value_type, operation, value):
        self.value_type=value_type
        self.value=value
        self.operation=operation

        if self.operation==None:
            raise ValueError("I2C operation type can't be empty")
        self.operation = self.operation.lower() #"equal","greater-equal","less-equal","constant"
        if self.operation=="equal" or self.operation=="greater-equal" or self.operation=="less-equal" or self.operation=="constant":
            pass
        else:
            raise ValueError("Unknown I2C operation type '%s'", self.operation)

        if self.operation=="constant":
            self.value_type="raw"
            self.value="00"
        self.value_type = self.value_type.lower() #"data","raw","ascii"
        if self.value_type=="data":
            self.value=int(self.value,0)
        elif self.value_type=="raw":
            self.value=self.value.lower()
        elif self.value_type=="ascii":
            self.value_type="raw"
            self.value=binascii.b2a_hex(self.value).lower()
        else:
            raise ValueError("Unknown I2C value type '%s'", self.value_type)



    def __str__(self):
        ret = "Condition: %s, %s, %s" % (self.value_type, self.operation, self.value)
        return ret

    def is_satisfied(self, value):
        new_value=value.lower()
        result=False
        if self.value_type=="data":
            new_value=int(new_value,16)
        if self.operation=="equal":
            result=(new_value==self.value)
        elif self.operation=="greater-equal":
            result=(new_value>=self.value)
        elif self.operation=="less-equal":
            result=(new_value<=self.value)
        elif self.operation=="constant":
            self.operation="equal"
            self.value=new_value
            result=True
        else:
            raise ValueError("Unknown I2C operation type '%s'", self.operation)

        if result:
            _LOGGER.info("Check value PASS: Read value %s %s expected value %s", new_value, self.operation, self.value)
            return True
        else:
            _LOGGER.info("Check value FAIL: Read value %s %s expected value %s", new_value, self.operation, self.value)
            return False

#--------------------------------------------------------------------------
#  I2C command
#--------------------------------------------------------------------------
def analyse_i2c_node(case, source_node, tag):
    """
    Analyse item node define in XML.
    If find 'ref' node, use it. Otherwise use the current one.
    """
    new_node = etree.Element(tag)
    # Get ref node
    ref = source_node.get("ref")
    ref_node = etree.Element(tag)
    if ref != None:
        ref_node_tmp = case.find(".//%s[@name='%s']" % (tag, ref))
        if ref_node_tmp != None:
            ref_node = analyse_i2c_node(case, ref_node_tmp, tag)
            new_node = copy.deepcopy(ref_node)
    else:
        new_node = copy.deepcopy(source_node)
    return new_node

def extract_rawdata(source_str):
    """
    Extract raw data from UART returned string(source string).
    The typical source string is:
    ESM $ rd_seeprom 5 0x54 0 2 8
    seeprom:
    01 01 00 05 00 00 10 e9
    
    """
    if (source_str=="" or source_str==None):
        return ""

    rawdata=""
    strs=source_str.split("\r\n")  
    index=0
    for str in strs:
        index = index+1	    
        if str.find("seeprom")>=0:
            rawdata= strs[index]

            
    raw_len=len(rawdata)
    if raw_len >0:
        if rawdata[raw_len-1]==' ':
            rawdata=rawdata[0:(raw_len-1)]
 
    return rawdata

#--------------------------------------------------------------------------
#  I2C READ CHECK
#--------------------------------------------------------------------------		
class PmcsesI2CReadCheckItem(testcase.TestItem):
    """
    A pmcsesI2CCheck instance execute I2C read commands specially for PMC SES, then parse the returned message.
    """
    item_type="pmc-i2c-read-check"

    	
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.condition_type = None
        self.conditions = []
        self.data_len = 1
        self.item_type="pmc-i2c-read-check"

    def action_init(self, kwargs):

        testcasexml = kwargs.get("testcase")
       
        node = self.parameter.find(self.item_type)
     
        node_combined = analyse_i2c_node(testcasexml, node, self.item_type)

        # Get timeout attribute
        cmd_timeout = int(node_combined.get("timeout"),0)
        proxy = node_combined.get("proxy")

        # Set command
        cmd = "rd_seeprom"
        port_id = int(node_combined.find("port_id").get("value"),0)
        device_addr = node_combined.find("device_addr").get("value")
        offset = int(node_combined.find("offset").get("value"),0)
        offset_width = int(node_combined.find("offset_width").get("value"),0)
        number_bytes_to_read = int(node_combined.find("number_bytes_to_read").get("value"),0)
		
	cmd = cmd + " " + str(port_id) + " " + device_addr + " " + str(offset) + " " + str(offset_width) + " " + str(number_bytes_to_read) +"\r"
         
        # Set condition_type
        self.condition_type = node_combined.get("condition_type").lower()
        if (self.condition_type=="and") or (self.condition_type=="or"):
	   pass
        else:
           raise ValueError("Unknown I2C condition type '%s'",self.condition_type)
		
        #set condition
        for cnode in node_combined.findall("condition"):
            operation = cnode.get("operation")
            value_type = cnode.get("value_type")
            value = cnode.get("value")
            self.conditions.append(I2CCondition(value_type,operation,value))
        #send command
        if proxy == "uart":
            uart_node = node_combined.find("uart")
            uart_port = uart_node.get("port")
            uart_baudrate = uart_node.get("baudrate")
            uart_newline_transmit = uart_node.get("new_line_transmit")
            endmarks = []
            for endmark_node in node_combined.findall("end-mark"):
                endmark = endmark_node.get("keyword")
                endmarks.append(endmark)
            error_filters = []
            for error_filter_node in node_combined.findall("error-filter"):
                error_filter = command.ErrorFilters[error_filter_node.get("type")](
                                               error_filter_node.get("operation"),
                                               error_filter_node.get("value"))
                error_filters.append(error_filter) 
            self.cmd = pmcses.PMCCommand(cmd,
                                      uart_port, uart_baudrate, None,
                                      uart_newline_transmit,
                                      cmd_timeout, None,
                                      endmarks, error_filters)
									  
        elif proxy == "uart-daemon":
            _LOGGER.info("uart-daemon not support")
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True
		
   
		
    def action_run(self, kwargs):
        """
        Execute the command.
        """
        result = False
        value = self.cmd.apply()
        
        value = extract_rawdata(value)
        
        if value == "":
            _LOGGER.info("Error: No value read from UART!") 
            return False

        if self.condition_type == "and":
            result = True
            for con in self.conditions:
                if con.is_satisfied(value) == False:
                    result = False
                    break
        else: #"or"
            result = False
            for con in self.conditions:
                if con.is_satisfied(value):
                    result = True
                    break
        return result

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True

#--------------------------------------------------------------------------
#  I2C Read
#--------------------------------------------------------------------------		
class PmcsesI2CReadItem(testcase.TestItem):
    """
    A pmcsesI2CCheck instance execute I2C read commands specially for PMC SES, then parse the returned message.
    """
    item_type="pmc-i2c-read"
	
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        

    def action_init(self, kwargs):

        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_i2c_node(testcasexml, node, self.item_type)

        # Get timeout attribute
        cmd_timeout = int(node_combined.get("timeout"),0)
        proxy = node_combined.get("proxy")

        # Set command
        cmd = "rd_seeprom"
        port_id = int(node_combined.find("port_id").get("value"),0)
        device_addr= node_combined.find("device_addr").get("value")
        offset = int(node_combined.find("offset").get("value"),0)
        offset_width = int(node_combined.find("offset_width").get("value"),0)
        number_bytes_to_read = int(node_combined.find("number_bytes_to_read").get("value"),0)
		
        cmd = cmd + " " + str(port_id) + " " + device_addr + " " + str(offset) + " " + str(offset_width) + " " + str(number_bytes_to_read) +"\r"

		 
        #send command
        if proxy == "uart":
            uart_node = node_combined.find("uart")
            uart_port = uart_node.get("port")
            uart_baudrate = uart_node.get("baudrate")
            uart_newline_transmit = uart_node.get("new_line_transmit")
            endmarks = []
            for endmark_node in node_combined.findall("end-mark"):
                endmark = endmark_node.get("keyword")
                endmarks.append(endmark)
            error_filters = []
            for error_filter_node in node_combined.findall("error-filter"):
                error_filter = command.ErrorFilters[error_filter_node.get("type")](
                                               error_filter_node.get("operation"),
                                               error_filter_node.get("value"))
                error_filters.append(error_filter) 
            self.cmd = pmcses.PMCCommand(cmd,
                                      uart_port, uart_baudrate, None,
                                      uart_newline_transmit,
                                      cmd_timeout, None,
                                      endmarks, error_filters)
									  
        elif proxy == "uart-daemon":
            _LOGGER.info("uart-daemon not support")
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True
		
  
		
    def action_run(self, kwargs):
        """
        Execute the command.
        """
        
        value = self.cmd.apply()
	value = extract_rawdata(value)
        if value == "":
	    _LOGGER.info("ERROR: read value failed")
            return False
	    _LOGGER.info("Read value PASS: Read value %s", value)
        return True

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True
	
		
		
		
		
class PmcsesI2CWriteItem(testcase.TestItem):
    """
    A pmcsesI2CCheck instance execute I2C read commands specially for PMC SES, then parse the returned message.
    """
    item_type="pmc-i2c-write"
	
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
       

    def action_init(self, kwargs):

        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_i2c_node(testcasexml, node, self.item_type)

        # Get timeout attribute
        cmd_timeout = int(node_combined.get("timeout"),0)
        proxy = node_combined.get("proxy")

        # Set command
        cmd = "wr_seeprom"
        port_id = int(node_combined.find("port_id").get("value"),0)
        device_addr= node_combined.find("device_addr").get("value")
        offset = int(node_combined.find("offset").get("value"),0)
        offset_width = int(node_combined.find("offset_width").get("value"),0)
        data_to_write = node_combined.find("data_to_write").get("value")
        cmd=cmd + " " + str(port_id) + " " + device_addr + " " + str(offset) + " " + str(offset_width) + " " + data_to_write +"\r"

		 
        #send command
        if proxy == "uart":
            uart_node = node_combined.find("uart")
            uart_port = uart_node.get("port")
            uart_baudrate = uart_node.get("baudrate")
            uart_newline_transmit = uart_node.get("new_line_transmit")
            endmarks = []
            for endmark_node in node_combined.findall("end-mark"):
                endmark = endmark_node.get("keyword")
                endmarks.append(endmark)
            error_filters = []
            for error_filter_node in node_combined.findall("error-filter"):
                error_filter = command.ErrorFilters[error_filter_node.get("type")](
                                               error_filter_node.get("operation"),
                                               error_filter_node.get("value"))
                error_filters.append(error_filter) 
            self.cmd = pmcses.PMCCommand(cmd,
                                      uart_port, uart_baudrate, None,
                                      uart_newline_transmit,
                                      cmd_timeout, None,
                                      endmarks, error_filters)
									  
        elif proxy == "uart-daemon":
#            self.cmd = sescmd.SESCommandUartDaemon()
             print "Has not supported uart-daemon\n"
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True
		
  
		
    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd()
        except ValueError:
            return False
        return True

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True



	
