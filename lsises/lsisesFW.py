#! /usr/bin/python

"""
SES Command Test Items For FW_CHECK.
"""

from lxml import etree
import os
import time
import copy
from serial import Serial
import lsises

from pycat import log, testcase, status
from basicplugin import command

_LOGGER = log.getLogger("cat.tc")

def analyse_fw_node(case, source_node, tag):
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
            ref_node = analyse_fw_node(case, ref_node_tmp, tag)
            new_node = copy.deepcopy(ref_node)
    else:
        new_node = copy.deepcopy(source_node)
    return new_node
 
class Diagfwprogram(testcase.TestItem):
    """
    A LSIfwprogram instance executes fw program
    """
    item_type = "fw_program"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)

    def action_init(self, kwargs):
        self.pathlist = []
        self.cmd = []
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node = analyse_fw_node(testcasexml, node, self.item_type)
        for cmdopt in node.findall("cmd"):
            self.cmd.append(cmdopt.get("value"))
        vend_node = node.find("vend_id")
        self.vend_id = vend_node.get("name")
        product_node = node.find("product_id")
        self.product_id = product_node.get("name")

        cmd = "ls /dev/sg*"
        self.cmd_detect = command.CommandLocalViaSystem(cmd)
        self.cmd_sg = "sg_inq"
        return True

    def action_run(self, kwargs):
        cmdlist = []
        cmd_programlist = []
        unitdev_list = self.detect_ses_dev()
        if len(unitdev_list) == 0:
            _LOGGER.info("Don not find the sg dev")
            return False
        _LOGGER.info("the unit is %s" % unitdev_list)
        for devopt in unitdev_list:
            for cmdopt in self.cmd: 
                cmd = cmdopt + devopt 
                cmdlist.append(cmd)
        for cmdopt in cmdlist:
            cmd_program = command.CommandLocalViaSystem(cmdopt)
            cmd_programlist.append(cmd_program)
        _LOGGER.info("the cmdlist is %s" % cmdlist)
        for opt in cmd_programlist:
            try:
                value = opt.apply()
                time.sleep(4)
            except OSError:
                return False
            i = value.find("fail")
            if -1 != i:
                _LOGGER.info("fail to program fw")
                return False
            time.sleep(4)
        return True

    def detect_ses_dev(self):
        try:
            value = self.cmd_detect.apply()
        except OSError:
            return False
        unitdev_list = []
        value = value.strip()
        list_item = value.split("\n")
        for item in list_item:
            item_tmp = item.strip()
            item = item_tmp[7:]
            cmd = self.cmd_sg + " " + "/dev/sg" + item
            cmd_det = command.CommandLocalViaSystem(cmd)
            value = cmd_det.apply()
            if -1 != value.find(self.product_id):
                unit = item
                unit = str(unit)
                unitdev_list.append(unit)
        return unitdev_list
 
    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd_detect.show()
        return True

class SESComfwcheckItem(testcase.TestItem):
    """
    A SESCommandItem instance executes SES commands. 
    """
    item_type = "check_fw"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.dict = {}

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node = analyse_fw_node(testcasexml, node, self.item_type)
        #node_combined = analyse_ses_command_node(testcasexml, node, self.item_type)
        # Set command
        name = node.find("version").get("name")
        version = node.find("version").get("ver")
        item = {name: version}
        self.dict.update(item)
        cmd_node = node.find("cmd")
        cmd = cmd_node.get("value")
        cmd_timeout = cmd_node.get("timeout")
        cmd_recv = cmd_node.get("recv")
        self.product_id = node.find("product_id").get("name")

        proxy = node.get("proxy")
        if proxy == "uart":
            uart_node = node.find("uart")
            uart_port = uart_node.get("port")
            uart_baudrate = uart_node.get("baudrate")
            uart_timeout = uart_node.get("timeout")
            uart_end_of_line = uart_node.get("end-of-line")
            endmarks = []
            for endmark_node in node.findall("end-mark"):
                endmark = endmark_node.get("keyword")
                endmarks.append(endmark)
            error_filters = []
            for error_filter_node in node.findall("error-filter"):
                error_filter = command.ErrorFilters[error_filter_node.get("type")](
                                               error_filter_node.get("operation"),
                                               error_filter_node.get("value"))
                error_filters.append(error_filter) 

            self.cmd = lsises.LSICommand(cmd,
                                      uart_port, uart_baudrate, uart_timeout,
                                      uart_end_of_line,
                                      cmd_timeout, cmd_recv,
                                      endmarks, error_filters)
        elif proxy == "uart-daemon":
            self.cmd = SESCommandUartDaemon()
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        list_cmd = ["cmdsvr_mode 0", "dbg set on", "dd_dbg -gpio r 9", "dd_dbg -gpio r 10", "cmdsvr_mode 1"]
        self.list = []
        for opt in list_cmd:
            cmd_opt = lsises.LSICommand(opt,
                                      uart_port, uart_baudrate, uart_timeout,
                                      uart_end_of_line,
                                      cmd_timeout, cmd_recv,
                                      endmarks, error_filters)
            self.list.append(cmd_opt)
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        for i in range(2):
            try:
                value = self.cmd.apply()
            except ValueError:
                return False
            if len(value) > 100:
                break
#        value = self.switch_file(value)
        ret = self.compare_info(value)
        if ret:
            return True
        else:
            return False

    def switch_file(self, value):
        list = value.split("\n")
        fd = open("/root/value.txt", "a+")
        for i in list:
            fd.write(i + "\n")
        fd.close()
        cmd = "dos2unix " + "/root/value.txt" + " " + ">/dev/null 2>&1"
        ret = os.system(cmd)
        if ret != 0:
            return None
        value = ""
        fd = open("/root/value.txt", "r+")
        for i in fd.readlines():
            value += i
        fd.close()
        os.remove("/root/value.txt")	
        return value

    def compare_info(self, value):
        fw_id = ""
        value_list = value.split("\r\n")
        for i in value_list:
            if -1 != i.find("Active Firmware: Firmware Copy"):
                fw_id = i[len("Active Firmware: Firmware Copy") + 1:]
                break
        if fw_id == "":
            _LOGGER.info("Don't find Active Firmware")
            return False
        for j in range(len(value_list)):
            if -1 != value_list[j].find("Firmware Copy " + fw_id + ":"):
                goal_str = value_list[ j + 1 ]
                new_goal_str = goal_str.strip()
                new_list = new_goal_str.split(" ")
                fw_ver = new_list[1].strip()
        if fw_ver == "":
            _LOGGER.info("Don't find Active Firmware value")
            return False
#        i = value.find('Active Firmware: ')
#        if -1 == i:
#            return None
#        i = i + len('Active Firmware: ')
#        fw_name_id = value[i+14:i+15]
#        i = new_str.find("Firmware Copy " + str(fw_name_id))
#        if -1 == i:
#            return None
#        i = i + len("Firmware Copy " + str(fw_name_id)) + 15
#        fw_ver = new_str[i:i+8]
        if fw_ver == self.dict['Active Firmware']:
            if self.product_id == "Atlas":
                cmd_count = len(self.list)
                for i in range(cmd_count):
                    try:
                        value = self.list[i].apply()
                    except ValueError:
                        return False
                    if i == 2:
                        v1 = value.split("\r\n")[1].strip()
                    elif i == 3:
                        v2 = value.split("\r\n")[1].strip()
                if v1 == "0x00" and v2 == "0x00":
                    sxp = "lsi0"
                elif v1 == "0x01" and v2 =="0x00":
                    sxp = "lsi1"
                else:
                    sxp = "lsi2"
                _LOGGER.info("Check Active Firmware version Pass,Active Firmware:%s,xml Firmware:%s,expander:%s." % (fw_ver, self.dict['Active Firmware'], sxp))
                return True
            else:
                _LOGGER.info("Check Active Firmware version Pass,Active Firmware:%s,xml Firmware:%s." % (fw_ver, self.dict['Active Firmware']))
                return True
        else:
#	    _LOGGER.info("Check Active Firmware version Fail,Active Firmware:%s,xml Firmware:%s" % (fw_ver, self.dict['Active Firmware']))
            if self.product_id == "Atlas":
                cmd_count = len(self.list)
                for i in range(cmd_count):
                    try:
                        value = self.list[i].apply()
                    except ValueError:
                        return False
                    if i == 2:
                        v1 = value.split(" ")[0]
                    elif i == 3:
                        v2 = value.split(" ")[0]
                if v1 == "0x00" and v2 == "0x00":
                    sxp = "lsi0"
                elif v1 == "0x01" and v2 =="0x00":
                    sxp = "lsi1"
                else:
                    sxp = "lsi2"
                _LOGGER.info("Check Active Firmware version Fail,Active Firmware:%s,xml Firmware:%s,expander:%s." % (fw_ver, self.dict['Active Firmware'], sxp))
                return False
            else:
                _LOGGER.info("Check Active Firmware version Fail,Active Firmware:%s,xml Firmware:%s." % (fw_ver, self.dict['Active Firmware']))
                return False	    

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True
