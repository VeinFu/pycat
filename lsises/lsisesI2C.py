#! /usr/bin/python

"""
Test Item for LSI SES CLI I2C read-check/write-read-check
"""

from lxml import etree
import copy
import binascii
import lsises
from basicplugin import command 

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
     Data [0] = 54 \r
     Data [1] = 61 \r
   \r
   \r
    cmd >
    """
    rawdata=""
    if (source_str=="" or source_str==None):
        return ""
    value_lines = source_str.split("\r")
    for line in value_lines:
        if line.find("Data")>=0:
            str_data = line.split("=")[1].strip()
            try:
                int_data = int("0x" + str_data, 0)
            except ValueError:
                return ""
            str_data = "%02x" % (int_data)
            rawdata = rawdata + str_data
    return rawdata

#--------------------------------------------------------------------------
#  I2C READ CHECK
#--------------------------------------------------------------------------		
class LsisesI2CReadCheckItem(testcase.TestItem):
    """
    A LsisesI2CReadCheck instance execute I2C read commands specially for LSI SES, then parse the returned message.
    """
    item_type="lsi-i2c-read-check"

    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.condition_type = None
        self.conditions = []
        self.data_len = 1

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_i2c_node(testcasexml, node, self.item_type)

        cmd_timeout = int(node_combined.get("timeout"))
        proxy = node_combined.get("proxy")

        # Set command
        bus = int(node_combined.find("ChannelNumber").get("value"),0)
        chip = hex(int(node_combined.find("SlaveAddress").get("value"),0))
        self.data_len = int(node_combined.find("number_bytes_to_read").get("value"),0)
        cmd = "iicr " + chip + " " + str(bus) + " " + str(self.data_len)
        # Set condition_type
        self.condition_type = node_combined.get("condition_type").lower()
        if (self.condition_type=="and") or (self.condition_type=="or"):
            pass
        else:
            raise ValueError("Unknown I2C condition type '%s'", self.condition_type)
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
            self.cmd = lsises.LSICommand(cmd,
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
#  I2C WRITE READ CHECK
#--------------------------------------------------------------------------		
class LsisesI2CWriteReadCheckItem(testcase.TestItem):
    """
    A LsisesI2CWriteReadCheck instance execute I2C write read commands specially for LSI SES, then parse the returned message.
    """
    item_type="lsi-i2c-write-read-check"

    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.condition_type = None
        self.conditions = []
        self.data_len = 1

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_i2c_node(testcasexml, node, self.item_type)

        cmd_timeout = int(node_combined.get("timeout"))
        proxy = node_combined.get("proxy")

        # Set command
        bus = int(node_combined.find("ChannelNumber").get("value"),0)
        chip = hex(int(node_combined.find("SlaveAddress").get("value"),0))
        self.data_len = int(node_combined.find("number_bytes_to_read").get("value"),0)
        writedata=node_combined.find("WriteData").get("value")
        cmd = "iicwr " + chip + " " + str(bus) + " " + str(self.data_len) + " " + writedata
        # Set condition_type
        self.condition_type = node_combined.get("condition_type").lower()
        if (self.condition_type=="and") or (self.condition_type=="or"):
            pass
        else:
            raise ValueError("Unknown I2C condition type '%s'", self.condition_type)
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
            self.cmd = lsises.LSICommand(cmd,
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
