#! /usr/bin/python

"""
I2C Test Items on OS.
"""

from lxml import etree
import copy
import binascii

from pycat import log, testcase
from command import CommandLocalViaPopen

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
def analyse_i2c_command_node(case, source_node, tag):
    """
    Analyse i2c_command node define in XML.
    """
    new_node = etree.Element(tag)
    # Get ref node
    ref = source_node.get("ref")
    ref_node = etree.Element(tag)
    if ref != None:
        ref_node_tmp = case.find(".//%s[@name='%s']" % (tag, ref))
        if ref_node_tmp != None:
            ref_node = analyse_i2c_command_node(case, ref_node_tmp, tag)
            new_node = copy.deepcopy(ref_node)
    else:
        new_node = copy.deepcopy(source_node)
    return new_node


#--------------------------------------------------------------------------
#  I2C READ CHECK
#--------------------------------------------------------------------------
class I2CReadCheckItem(testcase.TestItem):
    """
    A I2CReadCheckItem instance checks I2C data. 
    """
    item_type = "i2c-read-check"

    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.condition_type = None
        self.conditions = []
        self.data_len = 1
        self.data_offset = 0

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_i2c_command_node(testcasexml, node, self.item_type)
        #print(etree.tostring(node_combined))#ZYZ
        # Set command
        bus = node_combined.find("bus").get("value")
        chip = node_combined.find("chip").get("value")
        self.data_offset = int(node_combined.find("data").get("value"),0)
        self.data_len = int(node_combined.find("num-bytes-to-read").get("value"),0)
        cmd = "i2cdump -f -y "+bus+" "+chip+" i"
        proxy = node_combined.get("proxy")
        if proxy == "local":
            self.cmd = CommandLocalViaPopen(cmd)
        elif proxy == "ssh":
            ssh = node_combined.find("ssh")
            host = ssh.get("host")
            user = ssh.get("user")
            passwd = ssh.get("passwd")
            self.cmd = CommandSSH(cmd, host, user, passwd)
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        # Set condition_type
        self.condition_type = node_combined.get("condition_type").lower()
        if (self.condition_type=="and") or (self.condition_type=="or"):
            pass
        else:
            raise ValueError("Unknown I2C condition type '%s'", self.condition_type)

        # Set conditions
        for cnode in node_combined.findall("condition"):
            operation=cnode.get("operation")
            value_type=cnode.get("value_type")
            value=cnode.get("value")	    
            self.conditions.append(I2CCondition(value_type,operation,value))
	return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        data_arr=[]
        rawdata=""
        result=False
        try:
            value = self.cmd.apply()
        except OSError:
            return False
        value = value.split("\n")
        for i in range(1,17):
            data = value[i].split(" ",17)
            for j in range(1,17):
                data_arr.append(data[j])
        for i in range(self.data_offset, self.data_offset+self.data_len):
            rawdata=rawdata+data_arr[i]
        if self.condition_type=="and":
            result=True
            for con in self.conditions:
                if con.is_satisfied(rawdata)==False:
                    result=False
                    break
        else: #"or"
            result=False
            for con in self.conditions:
                if con.is_satisfied(rawdata):
                    result=True
                    break
        return result

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcasexml = kwargs.get("testcase")
        self.cmd.show()
        return True
