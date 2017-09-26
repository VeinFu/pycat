#! /usr/bin/python

"""
SES Command Test Items.
"""

from lxml import etree
import os
import copy
import re
import time
import sqlalchemy
from serial import Serial

from pycat import log, testcase, status
from command import *

_LOGGER = log.getLogger("log.tc")

#--------------------------------------------------------------------------
#  SES Command Executor
#--------------------------------------------------------------------------
class SESCommandUart(CommandExecutor):
    def __init__(self, cmd, port, baudrate, timeout=None, end_of_line=None, cmd_timeout=None, recv=None, endmarks=None, error_filters=None):
        CommandExecutor.__init__(self, cmd)
        self.port = port
        self.baudrate = baudrate
        if timeout == None or float(timeout) <= 0:
            self.timeout = 0.1
        else:
            self.timeout = float(timeout)
        if cmd_timeout == None or float(cmd_timeout) <= 0:
            self.cmd_timeout = 0.5
        else:
            self.cmd_timeout = float(cmd_timeout)
        if recv == None:
            self.recv = None
            self.read_size = 4096
        else:
            self.recv = int(recv)
            self.read_size = self.recv
        self.endmarks = endmarks
        self.error_filters = error_filters
        if end_of_line == None:
            self.end_of_line = "LF"
        else:
            self.end_of_line = end_of_line
        if self.end_of_line == "LF":
            self.eol = "\n"
        elif self.end_of_line == "CR":
            self.eol = "\r"
        elif self.end_of_line == "CRLF":
            self.eol = "\r\n"
        else:
            raise ValueError("Unknown EOL type: %s" % (self.end_of_line))

    def __str__(self):
        ret = "CMD: '%s' \nUart: port %s, baudrate %s, timeout %ss"\
              % (self.cmd, self.port, self.baudrate, self.timeout)
        return ret

    def show(self):
        _LOGGER.info("CMD: %s", self.cmd)
        _LOGGER.info("Timeout: %s", self.cmd_timeout)
        _LOGGER.info("Receive Bytes: %s", self.recv)
        _LOGGER.info("Uart: port %s, baudrate %s, timeout %ss", self.port, self.baudrate, self.timeout)
        if self.end_of_line == "LF":
            _LOGGER.info(r"End Of Line: LF(\n)")
        elif self.end_of_line == "CR":
            _LOGGER.info(r"End Of Line: CR(\r)")
        elif self.end_of_line == "CRLF":
            _LOGGER.info(r"End Of Line: CRLF(\r\n)")

        for endmark in self.endmarks:
            _LOGGER.info("End Mark: %s", endmark)
        for error_filter in self.error_filters:
            _LOGGER.info("%s" % error_filter)

    def apply(self):
        # Init Uart
        _LOGGER.info("Execute: %s", self.cmd)
        uart = Serial(self.port, self.baudrate, timeout=self.timeout)
        # Execute Command
        time_start = time.time()
        time_escape = time.time() - time_start
        uart.write(self.cmd + self.eol)
        uart.flush()
        rawdata = ""
        while time_escape <= self.cmd_timeout:
            rawdata += uart.read(self.read_size)
            if self.recv != None and len(rawdata) >= self.recv:
                break

            find_endmark = False
            for endmark in self.endmarks:
                sret = re.search(endmark, rawdata)
                if sret != None:
                    find_endmark = True
                    break
            if find_endmark == True:
                break
            time_escape = time.time() - time_start
        uart.close()
        # Print rawdata
        lines = rawdata.split("\n")
        for line in lines:
            _LOGGER.info("%s", line)
        ## Check Error
        find_error = False
        for error_filter in self.error_filters:
            try:
                error_filter.determine(rawdata)
            except ValueError, err:
                _LOGGER.error("%s", err)
                find_error = True
            if find_error == True:
                # Raise this error again so that SESCommandItem can catch it.
                _LOGGER.info("ERROR: read value with error!")
                break 
        return rawdata

#@todo Not Implemented
class SESCommandUartDaemon(CommandExecutor):
    def __init__(self):
        raise NotImplementedError

#--------------------------------------------------------------------------
#  SES Command
#--------------------------------------------------------------------------
def analyse_ses_command_node(case, source_node, tag):
    """
    Analyse ses-command node define in XML.
    """
    new_node = etree.Element(tag)
    # Get ref node
    ref = source_node.get("ref")
    ref_node = etree.Element(tag)
    if ref != None:
        ref_node_tmp = case.find(".//%s[@name='%s']" % (tag, ref))
        if ref_node_tmp != None:
            ref_node = analyse_ses_command_node(case, ref_node_tmp, tag)

    # Set attribute
    combine_attribute(new_node, source_node, ref_node, "name")
    combine_attribute(new_node, source_node, ref_node, "proxy", "uart")
    combine_attribute(new_node, source_node, ref_node, "end-of-line", "\n")

    # Combine uart node or uart-daemon node
    combine_unique_node(new_node, source_node, ref_node, "uart")
    combine_unique_node(new_node, source_node, ref_node, "uart-daemon")
    # Combine cmd node
    combine_unique_node(new_node, source_node, ref_node, "cmd")
    # Combine option nodes.
    combine_sequence_node(new_node, source_node, ref_node, "option", ("args"))
    # Combine end-mark nodes.
    combine_sequence_node(new_node, source_node, ref_node, "end-mark", ("keyword"))
    # Combine error-filter nodes.
    combine_sequence_node(new_node, source_node, ref_node, "error-filter", ("type", "operation", "value"))
    return new_node

class SESCommandItem(testcase.TestItem):
    """
    A SESCommandItem instance executes SES commands. 
    """
    item_type = "ses-command"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_ses_command_node(testcasexml, node, self.item_type)
        # Set command
        cmd_node = node_combined.find("cmd")
        cmd = cmd_node.get("value")
        for optnode in node_combined.findall("option"):
            cmd += " %s" % (optnode.get("args"))
        cmd_timeout = cmd_node.get("timeout")
        cmd_recv = cmd_node.get("recv")

        proxy = node_combined.get("proxy")
        if proxy == "uart":
            uart_node = node_combined.find("uart")
            uart_port = uart_node.get("port")
            uart_baudrate = uart_node.get("baudrate")
            uart_timeout = uart_node.get("timeout")
            uart_end_of_line = uart_node.get("end-of-line")
            endmarks = []
            for endmark_node in node_combined.findall("end-mark"):
                endmark = endmark_node.get("keyword")
                endmarks.append(endmark)
            error_filters = []
            for error_filter_node in node_combined.findall("error-filter"):
                error_filter = ErrorFilters[error_filter_node.get("type")](
                                               error_filter_node.get("operation"),
                                               error_filter_node.get("value"))
                error_filters.append(error_filter)

            self.cmd = SESCommandUart(cmd,
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
        return True

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True

class SESCommandchkfixItem(testcase.TestItem):
    """
    A SESCommandItem instance executes SES commands. 
    """
    item_type = "ses-command-comparefixvalue"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.fixvalue = ""

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_ses_command_node(testcasexml, node, self.item_type)
        # Set command
        cmd_node = node_combined.find("cmd")
        cmd = cmd_node.get("value")
        for optnode in node_combined.findall("option"):
            cmd += " %s" % (optnode.get("args"))
        cmd_timeout = cmd_node.get("timeout")
        cmd_recv = cmd_node.get("recv")
        self.fixvalue = node_combined.find("fixvalue").get("value")

        proxy = node_combined.get("proxy")
        if proxy == "uart":
            uart_node = node_combined.find("uart")
            uart_port = uart_node.get("port")
            uart_baudrate = uart_node.get("baudrate")
            uart_timeout = uart_node.get("timeout")
            uart_end_of_line = uart_node.get("end-of-line")
            endmarks = []
            for endmark_node in node_combined.findall("end-mark"):
                endmark = endmark_node.get("keyword")
                endmarks.append(endmark)
            error_filters = []
            for error_filter_node in node_combined.findall("error-filter"):
                error_filter = ErrorFilters[error_filter_node.get("type")](
                                               error_filter_node.get("operation"),
                                               error_filter_node.get("value"))
                error_filters.append(error_filter)

            self.cmd = SESCommandUart(cmd,
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
        ret = self.compare_fixvalue(value, self.fixvalue)
        if ret == 0:
            return True
        else:
            return False

    def compare_fixvalue(value, fixvalue):
        ret = 0
        if value == fixvalue:
            _LOGGER.info("Check the output value pass")
        else:
            _LOGGER.info("Check the output value fail,the output value:%s,the fixvalue:%s" % (value, fixvalue))
            ret = 1
        return ret

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True

class SESCommandchkfirstItem(testcase.TestItem):
    """
    A SESCommandItem instance executes SES commands. 
    """
    item_type = "ses-command-comparefirstvalue"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.firstvalue = ""
        self.ret = 0

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_ses_command_node(testcasexml, node, self.item_type)
        # Set command
        cmd_node = node_combined.find("cmd")
        cmd = cmd_node.get("value")
        for optnode in node_combined.findall("option"):
            cmd += " %s" % (optnode.get("args"))
        cmd_timeout = cmd_node.get("timeout")
        cmd_recv = cmd_node.get("recv")

        proxy = node_combined.get("proxy")
        if proxy == "uart":
            uart_node = node_combined.find("uart")
            uart_port = uart_node.get("port")
            uart_baudrate = uart_node.get("baudrate")
            uart_timeout = uart_node.get("timeout")
            uart_end_of_line = uart_node.get("end-of-line")
            endmarks = []
            for endmark_node in node_combined.findall("end-mark"):
                endmark = endmark_node.get("keyword")
                endmarks.append(endmark)
            error_filters = []
            for error_filter_node in node_combined.findall("error-filter"):
                error_filter = ErrorFilters[error_filter_node.get("type")](
                                               error_filter_node.get("operation"),
                                               error_filter_node.get("value"))
                error_filters.append(error_filter)

            self.cmd = SESCommandUart(cmd,
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
        if self.ret == 0:
            self.firstvalue = value
            self.ret = 1
        ret = self.compare_firstvalue(value, self.firstvalue)
        if ret == 0:
            return True
        else:
            return False

    def compare_firstvalue(self, value, firstvalue):
        ret = 0
        if value == firstvalue:
            _LOGGER.info("Check the output value pass")
        else:
            _LOGGER.info("Check the output value fail,the output value:%s,the firstvalue:%s" % (value, firstvalue))
            ret = 1
        return ret
    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True


