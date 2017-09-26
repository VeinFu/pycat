#! /usr/bin/python

"""
Test Items for AC Source
"""

from lxml import etree
import os
import tempfile
import copy
import subprocess
import paramiko
import serial

from pycat import log, testcase
from command import *

_LOGGER = log.getLogger("log.tc")

#---------------------------------------------------------------------------
# AC Source
#---------------------------------------------------------------------------
class ACSource(object):
    """
    An ACSource instance connects with a real AC source and supports methods
    to control it.
    """
    cmd_on = "OUTP ON"
    cmd_off = "OUTP OFF"
    cmd_status = "OUTP?"
    baudrate_list = [300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600,
                     115200, 128000, 384000, 2048000]

    def __init__(self, port, baudrate):
        if isinstance(port, str):
            self.port = port
        else:
            raise TypeError("Invalid port: %s." % port)

        if isinstance(baudrate, str):
            baudrate = int(baudrate)
        elif isinstance(baudrate, int):
            pass
        else:
            raise TypeError("Invalid baudrate: %s." % baudrate)

        if baudrate in self.baudrate_list:
            self.baudrate = baudrate
        else:
            raise ValueError("Invalid Baudrate '%d'. Possible value are %s."
                             % (baudrate, self.baudrate_list))

    def __str__(self):
        ret = "%s Uart port: %s, baud rate:%d" % (self.__class__.__name__, self.port, self.baudrate)
        return ret

    def is_on(self):
        """
        Check whether the AC source is on or not.
        If AC Source is on, return True.
        If AC Source is off, return False.
        If Uart isn't available, raise an error.
        """
        raise NotImplementedError

    def is_off(self):
        """
        Check whether the AC source is off or not.
        If AC Source is off, return True.
        If AC Source is on, return False.
        If Uart isn't available, raise an error.
        """
        raise NotImplementedError

    def turn_on(self):
        """
        Turn on AC Source. Return True on success, otherwise return False.
        """
        raise NotImplementedError

    def turn_off(self):
        """
        Turn off AC Source. Return True on success, otherwise return False.
        """
        raise NotImplementedError

class Chroma61500(ACSource):
    """
    Chroma AC Source 61501, 61502, 61503, 61504.
    The options of baudrate is 19200/9600.
    See 'Chroma Programmable AC Source 61501/61502/61503/61504 User's Manual'
    """
    cmd_on = "OUTP ON"
    cmd_off = "OUTP OFF"
    cmd_status = "OUTP?"
    baudrate_list = [9600, 19200]
    def __init__(self, port, baudrate):
        ACSource.__init__(self, port, baudrate)

    def is_on(self):
        """
        Check whether the AC source is on or not.
        """
        cmd = CommandUart(self.cmd_status, self.port, self.baudrate)
        for retry in range(5):
            ret = cmd.apply()
            if ret is "on":
                return True
            elif ret is "off":
                return False
            else:
                _LOGGER.warning("AC Source status '%s'. Retry now.", (ret))
        raise OSError("The uart isn't stable.")

    def is_off(self):
        """
        Check whether the AC source is off or not.
        """
        if self.is_on():
            return False
        return True

    def turn_on(self):
        """
        Turn on AC Source. Return True on success, otherwise return False.
        """
        cmd = CommandUart(self.cmd_on, self.port, self.baudrate, 0.5, 0)
        for retry in range(5):
            cmd.apply()
            if self.is_on():
                return True
        return False

    def turn_off(self):
        """
        Turn off AC Source. Return True on success, otherwise return False.
        """
        cmd = CommandUart(self.cmd_off, self.port, self.baudrate, 0.5, 0)
        for retry in range(5):
            cmd.apply()
            if self.is_on():
                return True
        return False

class Chroma6530(ACSource):
    """
    Chroma AC Source 6530.
    The options of baudrate is 300, 600, 1200, 2400, 4800, 9600, 19200 and 115200.
    See 'Chroma Programmable AC Source 61501/61502/61503/61504 User's Manual'
    """
    cmd_on = "OUTP ON"
    cmd_off = "OUTP OFF"
    cmd_status = "OUTP?"
    baudrate_list = [300, 600, 1200, 2400, 4800, 9600, 19200, 115200]
    def __init__(self, port, baudrate):
        ACSource.__init__(self, port, baudrate)

    def is_on(self):
        """
        Check whether the AC source is on or not.
        """
        cmd = CommandUart(self.cmd_status, self.port, self.baudrate)
        for retry in range(5):
            ret = cmd.apply()
            if ret is "on":
                return True
            elif ret is "off":
                return False
            else:
                _LOGGER.warning("AC Source status '%s'. Retry now.", (ret))
        raise OSError("The uart isn't stable.")

    def is_off(self):
        """
        Check whether the AC source is off or not.
        """
        if self.is_on():
            return False
        return True

    def turn_on(self):
        """
        Turn on AC Source. Return True on success, otherwise return False.
        """
        cmd = CommandUart(self.cmd_on, self.port, self.baudrate, 0.5, 0)
        for retry in range(5):
            cmd.apply()
            if self.is_on():
                return True
        return False

    def turn_off(self):
        """
        Turn off AC Source. Return True on success, otherwise return False.
        """
        cmd = CommandUart(self.cmd_off, self.port, self.baudrate, 0.5, 0)
        for retry in range(5):
            cmd.apply()
            if self.is_on():
                return True
        return False

class Relay(ACSource):
    cmd_on = "OUT ON"
    cmd_off = "OUT OFF"
    cmd_status = None
    baudrate_list = [9600, 19200, 38400, 57600, 115200]
    def __init__(self, port, baudrate):
        ACSource.__init__(self, port, baudrate)
        
    def is_on(self):
        """
        Check whether the AC source is on or not.
        """
        raise NotImplementedError("Relay doesn't support checking status.")

    def is_off(self):
        """
        Check whether the AC source is off or not.
        """
        raise NotImplementedError("Relay doesn't support checking status.")

    def turn_on(self):
        """
        Turn on AC Source. Return True on success, otherwise return False.
        """
        cmd = CommandUart(self.cmd_on, self.port, self.baudrate, 0.1, 0)
        cmd.apply()
        return True

    def turn_off(self):
        """
        Turn off AC Source. Return True on success, otherwise return False.
        """
        cmd = CommandUart(self.cmd_off, self.port, self.baudrate, 0.1, 0)
        cmd.apply()
        return True

class IPS(ACSource):
    def __init__(self):
        pass

#---------------------------------------------------------------------------
# AC Source Test Item
#---------------------------------------------------------------------------
def analyse_ac_source_node(case, source_node, tag):
    """
    Analyse AC Source node defined in XML.
    """
    new_node = etree.Element(tag)
    # Get ref node
    ref = source_node.get("ref")
    ref_node = etree.Element(tag)
    if ref != None:
        ref_node_tmp = case.find(".//%s[@name='%s']" % (tag, ref))
        if ref_node_tmp != None:
            ref_node = analyse_ac_source_node(case, ref_node_tmp, tag)
    # Set attribute
    name = source_node.get("name")
    if name != None:
        new_node.set("name", name)

    ac_type = source_node.get("type")
    if ac_type == None:
        ac_type = ref_node.get("type")
        if ac_type == None:
            raise ValueError("%s node must set or inherit a 'type' attribute." % tag)
    new_node.set("type", ac_type)

    # Combine uart node
    subnode = source_node.find("uart")
    if subnode == None:
        subnode = ref_node.find("uart")
        if subnode == None:
            raise ValueError("%s node must set or inherit a 'uart' node." % tag)
    subnode_tmp = copy.deepcopy(subnode)
    new_node.append(subnode_tmp)

    # Combine action node
    subnode = source_node.find("action")
    if subnode == None:
        subnode = ref_node.find("action")
        if subnode == None:
            raise ValueError("%s node must set or inherit a 'action' node." % tag)
    subnode_tmp = copy.deepcopy(subnode)
    new_node.append(subnode_tmp)

    return new_node

class ACSourceItem(testcase.TestItem):
    """
    A Command instance execute a command through local shell, SSH or uart.
    Supported proxy:
        * local, Execute a command on local shell.
        * ssh, Execute a command through SSH.
        * uart, Execute a command through uart.
    """
    item_type = "ac-source"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.acsource = None
        self.action = None

    def action_init(self, kwargs):
        """
        Initialize command. Analyse command and chose a proxy.
        """
        testcase = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_ac_source_node(testcase, node, self.item_type)
        acsource = node_combined.get("type")
        uart = node_combined.find("uart")
        if acsource in ("Chroma61500", "Chroma61501", "Chroma61502",
                        "Chroma61503", "Chroma61504"):
            self.acsource = Chroma61500(uart.get("port"), uart.get("baudrate"))
        elif acsource in ("Chroma6530"):
            self.acsource = Chroma6530(uart.get("port"), uart.get("baudrate"))
        elif acsource in ("Relay"):
            self.acsource = Relay(uart.get("port"), uart.get("baudrate"))
        else:
            raise ValueError("Unsupported AC Source %s" % acsource)
        action = node_combined.find("action")
        self.action = action.get("type")
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            if self.action == "turn-on":
                value = self.acsource.turn_on()
                return value
            elif self.action == "turn-off":
                value = self.acsource.turn_off()
                return value
            elif self.action == "status":
                value = self.acsource.is_on()
                if value:
                    _LOGGER.info("AC Source is on.")
                else:
                    _LOGGER.info("AC Source is off.")
                return True
            else:
                _LOGGER.warning("Not supported action: %s", self.action)
                return False
        except NotImplementedError, err:
            _LOGGER.error("%s", err)
            return False
        except OSError, err:
            _LOGGER.error("%s", err)
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
        _LOGGER.info("%s", self.acsource)
        _LOGGER.info("Action: %s", self.action)
        return True

