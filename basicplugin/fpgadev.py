#! /usr/bin/python

from lxml import etree
import acsource
import sescmd
import os
import copy
import time
from command import *
from pycat import testcase, log, status

_LOGGER = log.getLogger("log.tc")

def analyse_node(case, source_node, tag):
    """
    Analyse node define in XML.
    """
    new_node = etree.Element(tag)
    # Get ref node
    ref = source_node.get("ref")
    ref_node = etree.Element(tag)
    if ref != None:
        ref_node_tmp = case.find(".//%s[@name='%s']" % (tag, ref))
        if ref_node_tmp != None:
            ref_node = analyse_device_hdd_node(case, ref_node_tmp, tag)
            new_node = copy.deepcopy(ref_node)
    else:
        new_node = copy.deepcopy(source_node)
    return new_node

class CommandsensorItem(testcase.TestItem):
    """
    A Command instance execute a command through local shell, SSH or uart.
    Supported proxy:
        * local, Execute a command on local shell.
        * ssh, Execute a command through SSH.
        * uart, Execute a command through uart.
    """
    item_type = "device-sensor"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.maxvalue = None
        self.minvalue = None

    def action_init(self, kwargs):
        """
        Initialize command. Analyse command and chose a proxy.
        """
        testcase = kwargs.get("testcase")
        cmd_node = self.parameter.find(self.item_type)
        cmd_node_combined = analyse_node(testcase, cmd_node, self.item_type)
        cmd = cmd_node_combined.find("cmd").get("value")
        for optnode in cmd_node_combined.findall("option"):
            cmd += " %s" % (optnode.get("args"))

        self.maxvalue = cmd_node_combined.find("condition").get("maxvalue")
        self.minvalue = cmd_node_combined.find("condition").get("minvalue")

        proxy = cmd_node_combined.get("proxy")
        if proxy == "local":
            self.cmd = CommandLocalViaPopen(cmd)
        elif proxy == "ssh":
            ssh = cmd_node_combined.find("ssh")
            host = ssh.get("host")
            user = ssh.get("user")
            passwd = ssh.get("passwd")
            self.cmd = CommandSSH(cmd, host, user, passwd)
        elif proxy == "uart":
            uart = cmd_node_combined.find("uart")
            port = uart.get("port")
            baudrate = uart.get("baudrate")
            timeout = uart.get("timeout")
            recv = uart.get("recv")
            self.cmd = CommandUart(cmd, port, baudrate, timeout, recv)
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd.apply()
        except OSError:
            return False
        value = self.parse_info(value)
        ret = self.compare_info(value)
        if ret:
            return True
        else:
            return False

    def parse_info(self, value):
        value_list = []
        if -1 != value.find("is"):
            value_tuple = value.partition("is")
            new_value = value_tuple[2].strip()
            value_list = new_value.split(" ")
            result = value_list[0].strip()
            return result
        else:
            _LOGGER.info("the output value is valid.")
            raise("the output value is valid.")

    def compare_info(self, result_value):
        if self.minvalue != "":
            if int(float(result_value)) < int(self.maxvalue) and int(float(result_value)) > int(self.minvalue):
                _LOGGER.info("Check output value pass")
                return True
            else:
                _LOGGER.info("Check output value fail.the maxvalue:%s,the minvalue:%s,the output value:%s" % (self.maxvalue,self.minvalue,result_value)) 
                return False
        else:
            if result_value == self.maxvalue:
                _LOGGER.info("Check the output value pass")
                return True
            else:
                _LOGGER.info("Check the output value fail.the setvalue:%s,the output value:%s" % (self.maxvalue, result_value))
                return False

    def action_clear(self, kwargs):
        """
        No thing to do.
        """
        return True

    def action_print_parameter(self, kwargs):
        """
        Print the command to be executed.
        """
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True


class CommandpcieItem(testcase.TestItem):
    """
    A Command instance execute a command through local shell, SSH or uart.
    Supported proxy:
        * local, Execute a command on local shell.
        * ssh, Execute a command through SSH.
        * uart, Execute a command through uart.
    """
    item_type = "device-pcie"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.speed = None
        self.wide = None

    def action_init(self, kwargs):
        """
        Initialize command. Analyse command and chose a proxy.
        """
        testcase = kwargs.get("testcase")
        cmd_node = self.parameter.find(self.item_type)
        cmd_node_combined = analyse_node(testcase, cmd_node, self.item_type)
        cmd = cmd_node_combined.find("cmd").get("value")
        for optnode in cmd_node_combined.findall("option"):
            cmd += " %s" % (optnode.get("args"))

        self.speed = cmd_node_combined.find("speedwide").get("speedvalue")
        self.wide = cmd_node_combined.find("speedwide").get("widevalue")

        proxy = cmd_node_combined.get("proxy")
        if proxy == "local":
            self.cmd = CommandLocalViaPopen(cmd)
        elif proxy == "ssh":
            ssh = cmd_node_combined.find("ssh")
            host = ssh.get("host")
            user = ssh.get("user")
            passwd = ssh.get("passwd")
            self.cmd = CommandSSH(cmd, host, user, passwd)
        elif proxy == "uart":
            uart = cmd_node_combined.find("uart")
            port = uart.get("port")
            baudrate = uart.get("baudrate")
            timeout = uart.get("timeout")
            recv = uart.get("recv")
            self.cmd = CommandUart(cmd, port, baudrate, timeout, recv)
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd.apply()
        except OSError:
            return False
        speed_value, width_value = self.parse_info(value)
        ret = self.compare_info(speed_value, width_value)
        if ret:
            return True
        else:
            return False

    def parse_info(self, value):
        value_list = []
        lnkcap_list = []
        value_list = value.split("\n")
        for line in value_list:
            if -1 != line.find("LnkCap"):
                goal_line = line.strip()
                break
        lnkcap_list = goal_line.split(",")
        for line in lnkcap_list:
            if -1 != line.find("Speed"):
                speed_value = line.strip().split(" ")[1].strip()
            elif -1 != line.find("Width"):
                width_value = line.strip().split(" ")[1].strip()
            else:
                continue
        return speed_value, width_value

    def compare_info(self, speed_value, width_value):
        if speed_value == self.speed and width_value == self.wide:
            _LOGGER.info("Check pcie speed and width pass")
            return True
        else:
            _LOGGER.info("Check pcie speed and width fail.the setspeed:%s,the setwidth:%s,the output speed:%s,the output width:%s" % (self.speed, self.wide, speed_value, width_value))
            return False

    def action_clear(self, kwargs):
        """
        No thing to do.
        """
        return True

    def action_print_parameter(self, kwargs):
        """
        Print the command to be executed.
        """
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True

class CommandmemItem(testcase.TestItem):
    """
    A Command instance execute a command through local shell, SSH or uart.
    Supported proxy:
        * local, Execute a command on local shell.
        * ssh, Execute a command through SSH.
        * uart, Execute a command through uart.
    """
    item_type = "device-memory"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None

    def action_init(self, kwargs):
        """
        Initialize command. Analyse command and chose a proxy.
        """
        testcase = kwargs.get("testcase")
        cmd_node = self.parameter.find(self.item_type)
        cmd_node_combined = analyse_node(testcase, cmd_node, self.item_type)
        cmd = cmd_node_combined.find("cmd").get("value")
        for optnode in cmd_node_combined.findall("option"):
            cmd += " %s" % (optnode.get("args"))
        proxy = cmd_node_combined.get("proxy")
        if proxy == "local":
            self.cmd = CommandLocalViaPopen(cmd)
        elif proxy == "ssh":
            ssh = cmd_node_combined.find("ssh")
            host = ssh.get("host")
            user = ssh.get("user")
            passwd = ssh.get("passwd")
            self.cmd = CommandSSH(cmd, host, user, passwd)
        elif proxy == "uart":
            uart = cmd_node_combined.find("uart")
            port = uart.get("port")
            baudrate = uart.get("baudrate")
            timeout = uart.get("timeout")
            recv = uart.get("recv")
            self.cmd = CommandUart(cmd, port, baudrate, timeout, recv)
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd.apply()
        except OSError:
            return False
        time.sleep(3)
        ret = self.parse_info(value)
        if ret:
            return True
        else:
            return False

    def parse_info(self, value):
        if -1 == value.find("failed"):
            _LOGGER.info("Check the memory size pass")
            return True
        else:
            _LOGGER.info("Check the memory size fail")
            return False

    def action_clear(self, kwargs):
        """
        No thing to do.
        """
        return True

    def action_print_parameter(self, kwargs):
        """
        Print the command to be executed.
        """
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True




