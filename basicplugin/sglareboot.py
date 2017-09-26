#! /usr/bin/python

from lxml import etree
import os
import time
import copy
from serial import Serial

from pycat import log, testcase, status
from command import *

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


class CommandrebootItem(testcase.TestItem):
    """
    A Command instance execute a command through local shell, SSH or uart.
    Supported proxy:
        * local, Execute a command on local shell.
        * ssh, Execute a command through SSH.
        * uart, Execute a command through uart.
    """
    item_type = "reboot-command"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.flag = 0
        self.cmd_value = None
        self.time = None
        self.first_value = None
        self.count = 2


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
        self.cmd_value = cmd
        if -1 != cmd.find("time"):
            self.time = cmd_node_combined.find("condition").get("value")
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
        
        if self.flag == 0:
            self.first_value = value
        if -1 != self.cmd_value.find("time"):
            if self.flag == 1:
                ret = self.check_time(value, self.first_value)
                self.first_value = value
            else:
                ret = 0
                self.count = self.count - 1
                if self.count == 0:
                    self.flag = 1
        else:
            ret = self.compare_firstvalue(value, self.first_value)
            self.flag = 1    

        if ret == 0:
            return True
        else:
            return False

    def compare_firstvalue(self, value, first_value):
        if -1 != self.cmd_value.find("physical"):
            title = "cpu count"
        elif -1 != self.cmd_value.find("cores"):
            title = "cpu cores count"
        elif -1 != self.cmd_value.find("mem"):
            title = "memsize"
        elif -1 != self.cmd_value.find("disk"):
            title = "hdd count"

        ret = 0
        if value == first_value:
            _LOGGER.info("Check %s pass." % title)
        else:
            _LOGGER.info("Check %s fail,first value:%s,output:%s" % (title, first_value, value))
            ret = 1
        return ret


    def check_time(self, value, pretime):
        ret = 0
        period_time = int(value) - int(pretime) 
        if period_time < int(self.time):
            _LOGGER.info("Check time period pass.the output time:%s" % period_time)
        else:
            _LOGGER.info("Check time period fail,set time:%s,output time:%s" % (self.time, period_time))
            ret = 1
        return ret

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



class CommandpingItem(testcase.TestItem):
    """
    A Command instance execute a command through local shell, SSH or uart.
    Supported proxy:
        * local, Execute a command on local shell.
        * ssh, Execute a command through SSH.
        * uart, Execute a command through uart.
    """
    item_type = "ping-command"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.time = None

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
        self.time = cmd_node_combined.find("sleeptime").get("value")
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
        
        while True:
#            try:
            value = self.cmd.apply()
##            except OSError:
#                return False
            if -1 != value.find("req"):
                break
            time.sleep(int(self.time))
        
        return True

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

#class CommandchkpoweroffItem(testcase.TestItem):
class CommandchkpoweroffItem(CommandItem):
    """
    A Command instance execute a command through local shell, SSH or uart.
    Supported proxy:
        * local, Execute a command on local shell.
        * ssh, Execute a command through SSH.
        * uart, Execute a command through uart.
    """
    item_type = "chkpoweroff-command"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None

#    def action_init(self, kwargs):
#        """
#
#        """
#        testcase = kwargs.get("testcase")
#        cmd_node = self.parameter.find(self.item_type)
#        cmd_node_combined = analyse_node(testcase, cmd_node, self.item_type)
#        cmd = cmd_node_combined.find("cmd").get("value")
#        for optnode in cmd_node_combined.findall("option"):
#            cmd += " %s" % (optnode.get("args"))
#        proxy = cmd_node_combined.get("proxy")
#        if proxy == "local":
#            self.cmd = CommandLocalViaPopen(cmd)
#        elif proxy == "ssh":
#            ssh = cmd_node_combined.find("ssh")
#            host = ssh.get("host")
#            user = ssh.get("user")
#            passwd = ssh.get("passwd")
#            self.cmd = CommandSSH(cmd, host, user, passwd)
#        elif proxy == "uart":
#            uart = cmd_node_combined.find("uart")
#            port = uart.get("port")
#            baudrate = uart.get("baudrate")
#            timeout = uart.get("timeout")
#            recv = uart.get("recv")
#            self.cmd = CommandUart(cmd, port, baudrate, timeout, recv)
#        else:
#            raise ValueError("Unknown proxy type '%s'", proxy)
#        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        
#        try:
        while True:
            value = self.cmd.apply()
            if value.strip() != "" and -1 == value.find("Unable"):
                break
        ret = self.check_poweroff(value)
        if ret == 0:
#        except OSError:
#            return False
            return True
        else:
            return False

    def check_poweroff(self, value):
        ret = 0
        data = value.strip().split(" ")[0]
        if int(data, 16) & 0x01 == 0:
            _LOGGER.info("system poweroff pass.")
        else:
            _LOGGER.info("system poweroff fail.")
            ret = 1
        return ret

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

