#! /usr/bin/python

"""
SES Command Test Items For FW_CHECK.
"""

from lxml import etree
import os
import copy
#import re
import time
import sqlalchemy
from serial import Serial
import pmcses
import subprocess

from pycat import log, testcase, status
#from command import *
from basicplugin import command

_LOGGER = log.getLogger("log.tc")

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

class CommandLocalexc(command.CommandLocalViaPopen):
    def __init__(self, cmd):
	command.CommandLocalViaPopen.__init__(self, cmd)
    
    def apply(self):

#        Execute the command.

        _LOGGER.info("Execute '%s'" % (self.cmd))
        cmd = tuple(self.cmd.split(' '))
        for i in range(2):
            cmdexec = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            value = ""
            last_clear = False
            while True:
                line = cmdexec.stdout.readline()
                while line != "":
                    value += line
                    if line[-1] == "\n":
                        _LOGGER.info("%s", line[:-1])
                    else:
                        _LOGGER.info("%s", line)
                    line = cmdexec.stdout.readline()
                line = cmdexec.stderr.readline()
                while line != "":
                    _LOGGER.warning("%s", line[:-1])
                    line = cmdexec.stderr.readline()
                ret = cmdexec.poll()
                if ret != None:
                    if last_clear == True:
                        break
                    last_clear = True
            if -1 != value.find("successfully"):
                break 
        return value
 

class Diagfwprogram(testcase.TestItem):

 #   A PMCfwprogram instance executes fw program
    
    item_type = "fw_program"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)

    def action_init(self, kwargs):
        self.pathlist = []
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node = analyse_fw_node(testcasexml, node, self.item_type)
        self.cmd = "diag_ui"
        for pathopt in node.findall("path"):
            path = pathopt.get("file")
            self.pathlist.append(path)
        vend_node = node.find("vend_id")
        self.vend_id = vend_node.get("name")
        product_node = node.find("product_id")
        self.product_id = product_node.get("name")

        cmd = "ls /dev/sg*"
       # self.cmd_detect = command.CommandLocalViaPopen(cmd)
        self.cmd_detect = command.CommandLocalViaSystem(cmd)
        self.cmd_sg = "sg_inq"
        return True

    def action_run(self, kwargs):
        cmdlist = []
        cmd_programlist = []
        unit = []
        unit = self.detect_ses_dev()
        for i in unit:
            for pathopt in self.pathlist:
                cmd = self.cmd + " -d " + "13.4." + i +".0" + " -x -f " + "\"" + pathopt + "\"" + " -d 1 -v " + "\"" + self.vend_id + "\"" + " -p " + "\"" + self.product_id + "\"" + " -r 0" 
                cmdlist.append(cmd)
        for cmdopt in cmdlist:
            cmd_program = command.CommandLocalViaSystem(cmdopt)
            cmd_programlist.append(cmd_program)
        for cmd_program in cmd_programlist:
            try:
                value = cmd_program.apply()
            except OSError:
                return False
            i = value.find("Fail")
            if -1 != i:
                _LOGGER.info("fail to program fw")
                return False

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
                unit = hex(int(item))[2:]
                unit = str(unit)
                unitdev_list.append(unit)
        return unitdev_list
 
    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd_detect.show()
        return True

"""
class Diagfwprogram(testcase.TestItem):
    
    A LSIfwprogram instance executes fw program
    
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
"""
        
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
        for optnode in node.findall("version"):
            i = len(optnode.items())
            if i == 2:
                name = optnode.get("name")
                ver = optnode.get("ver")
                item = {name: (ver)}
            else:
                name = optnode.get("name")
                ver = optnode.get("ver")
                misc = optnode.get("misc")
                item = {name: (ver, misc)}
            self.dict.update(item)

        cmd_node = node.find("cmd")
        cmd = cmd_node.get("value")
        for optnode in node.findall("option"):
            cmd += " %s" % (optnode.get("args"))
        cmd_timeout = cmd_node.get("timeout")
        cmd_recv = cmd_node.get("recv")

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

            self.cmd = pmcses.PMCCommand(cmd,
                                      uart_port, uart_baudrate, uart_timeout,
                                      uart_end_of_line,
                                      cmd_timeout, cmd_recv,
                                      endmarks, error_filters)
        elif proxy == "uart-daemon":
            self.cmd = SESCommandUartDaemon()
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd.apply()
        except ValueError:
            return False
        ret = self.compare_info(value)
        if ret:
            return True
        else:
            return False

    def parse_info_dict(self, value):
        result_dict = {}
        value_list = value.split("\r\n")
        value_list_len = len(value_list)
        new_value_list = []
        for i in range(4, value_list_len - 1):
            new_value_list.append(value_list[i])
        for item in new_value_list:
            item_list = item.split("(")
            if len(item_list) == 2:
                item_key = item_list[0].strip().split(" ")[1]
                item_value = item_list[1].strip().split(")")[0].split(".")[2]
                item_dict = {item_key: item_value}
                result_dict.update(item_dict)
            else:
                item_key = item_list[0].strip().split(" ")[1]
                tuple_value1 = item_list[1].strip().split(")")[0].split(".")[2]
                tuple_value2 = item_list[2].strip().split(")")[0]
                item_value = (tuple_value1, tuple_value2)
                item_dict = {item_key: item_value}
                result_dict.update(item_dict)
        return result_dict

    def compare_info(self, value):
        ret = True
        result_dict = {}
        result_dict = self.parse_info_dict(value)
        for opt in self.dict.keys():
            if opt in result_dict.keys():
                if self.dict[opt] == result_dict[opt]:
                    _LOGGER.info("Check %s version and status Pass" % opt)
                else:
                    _LOGGER.info("Check %s version and status Fail,Out version:%s,XML version:%s" % (opt, result_dict[opt], self.dict[opt]))
                    ret = False
            else:
                _LOGGER.info("Unknown the %s key in the output value" % opt)
                ret = False
        return ret

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True

class SESComcpldcheckItem(testcase.TestItem):
    """
    A SESCommandItem instance executes SES commands. 
    """
    item_type = "check_cpld"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.cpld = ""

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node = analyse_fw_node(testcasexml, node, self.item_type)
        #node_combined = analyse_ses_command_node(testcasexml, node, self.item_type)
        # Set command
        self.cpld = node.find("cpld_ver").get("value")

        cmd_node = node.find("cmd")
        cmd = cmd_node.get("value")
        for optnode in node.findall("option"):
            cmd += " %s" % (optnode.get("args"))
        cmd_timeout = cmd_node.get("timeout")
        cmd_recv = cmd_node.get("recv")

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

            self.cmd = pmcses.PMCCommand(cmd,
                                      uart_port, uart_baudrate, uart_timeout,
                                      uart_end_of_line,
                                      cmd_timeout, cmd_recv,
                                      endmarks, error_filters)
        elif proxy == "uart-daemon":
            self.cmd = SESCommandUartDaemon()
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd.apply()
        except ValueError:
            return False
        out_cpld = self.get_cpld_value(value)
        ret = self.compare_cpld_value(out_cpld, self.cpld)
        if ret:
            return True
        else:
            return False

    def get_cpld_value(self, value):
        value_list = value.split("\r\n")
        for line in value_list:
            if -1 != line.find("CPLD"):
                out_cpld = line.split(":")[1].strip()
                break
        if out_cpld == "":
            _LOGGER.info("Can`t get cpld value")
        return out_cpld

    def compare_cpld_value(self, out_cpld, xml_cpld):
        ret = True
        if out_cpld == xml_cpld:
            _LOGGER.info("Check the cpld version pass")
        else:
            _LOGGER.info("Check the cpld version fail,the output cpld:%s,the xml cpld:%s" % (out_cpld, xml_cpld))
            ret = False
        return ret

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True
