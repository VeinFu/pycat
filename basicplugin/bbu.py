#! /usr/bin/python

"""
BBU Test Items.
"""

from lxml import etree
import os
import copy
import re
import time
import sqlalchemy

from pycat import log, testcase, status
from command import *

_LOGGER = log.getLogger("log.tc")



class BBUMonitor(object):
    def __init__(self, bbu, name, value_type, units):
        self.bbu = bbu
        self.name = name
        self.monitor_name = bbu + '-' + name
        self.value_type = value_type
        self.units = units
        dbsession = status.get_session()
        try:
            monitor = status.Monitor(name=self.monitor_name,
                                     value_type=self.value_type,
                                     units=self.units)
            dbsession.add(monitor)
            dbsession.commit()
        except sqlalchemy.exc.IntegrityError, err:
            pass

    def __str__(self):
        ret = "Monitor %s, %s, %s, %s" % (self.bbu, self.name, self.value_type, self.units)
        return ret

    def update(self, value, units):
        if units != self.units:
            _LOGGER.warning("Unexpected units %s, should be %s.", units, self.units)
        dbsession = status.get_session()
        monitor_data = status.MonitorData(monitor=self.monitor_name,
                                          data=value)
        dbsession.add(monitor_data)
        dbsession.commit()

def int_less_than(vala, valb):
    vala = int(vala)
    valb = int(valb)
    if vala < valb:
        return True
    else:
        return False

def int_less_equal(vala, valb):
    vala = int(vala)
    valb = int(valb)
    if vala <= valb:
        return True
    else:
        return False

def int_equal(vala, valb):
    vala = int(vala)
    valb = int(valb)
    if vala == valb:
        return True
    else:
        return False

def int_not_equal(vala, valb):
    vala = int(vala)
    valb = int(valb)
    if vala != valb:
        return True
    else:
        return False

def int_greater_than(vala, valb):
    vala = int(vala)
    valb = int(valb)
    if vala > valb:
        return True
    else:
        return False

def int_greater_equal(vala, valb):
    vala = int(vala)
    valb = int(valb)
    if vala >= valb:
        return True
    else:
        return False

def float_less_than(vala, valb):
    vala = float(vala)
    valb = float(valb)
    if vala < valb:
        return True
    else:
        return False

def float_less_equal(vala, valb):
    vala = float(vala)
    valb = float(valb)
    if vala <= valb:
        return True
    else:
        return False

def float_equal(vala, valb):
    vala = float(vala)
    valb = float(valb)
    if vala == valb:
        return True
    else:
        return False

def float_not_equal(vala, valb):
    vala = float(vala)
    valb = float(valb)
    if vala != valb:
        return True
    else:
        return False

def float_greater_than(vala, valb):
    vala = float(vala)
    valb = float(valb)
    if vala > valb:
        return True
    else:
        return False

def float_greater_equal(vala, valb):
    vala = float(vala)
    valb = float(valb)
    if vala >= valb:
        return True
    else:
        return False

def string_equal(vala, valb):
    assert isinstance(vala, str)
    assert isinstance(valb, str)
    if vala == valb:
        return True
    else:
        return False

def string_not_equal(vala, valb):
    assert isinstance(vala, str)
    assert isinstance(valb, str)
    if vala != valb:
        return True
    else:
        return False

def binary_equal(vala, valb):
    """
        Example:
        vala:   0b00010101
        valb:   0b00x101xx
        mask:     11011100
        expect:   00010100
        vala & mask == expect
    """
    assert isinstance(vala, str)
    assert isinstance(valb, str)
    mask = valb[2:].replace("0", "1").replace("x", "0")
    highbits = len(vala) - 2 - len(mask)
    if highbits > 0:
        mask = "1" * highbits + mask
    mask = int(mask, 2)
    expect = int(valb[2:].replace("x", "0"), 2)
    vala = int(vala, 2)
    if vala & mask == expect:
        return True
    else:
        return False

def binary_not_equal(vala, valb):
    assert isinstance(vala, str)
    assert isinstance(valb, str)
    mask = valb[2:].replace("0", "1").replace("x", "0")
    highbits = len(vala) - 2 - len(mask)
    if highbits > 0:
        mask = "1" * highbits + mask
    mask = int(mask, 2)
    expect = int(valb[2:].replace("x", "0"), 2)
    vala = int(vala, 2)
    if vala & mask != expect:
        return True
    else:
        return False

compare_funcs = {
    ("int", "less-than"): int_less_than,
    ("int", "less-equal"): int_less_equal,
    ("int", "equal"): int_equal,
    ("int", "not-equal"): int_not_equal,
    ("int", "greater-than"): int_greater_than,
    ("int", "greater-equal"): int_greater_equal,
    ("float", "less-than"): float_less_than,
    ("float", "less-equal"): float_less_equal,
    ("float", "equal"): float_equal,
    ("float", "not-equal"): float_not_equal,
    ("float", "greater-than"): float_greater_than,
    ("float", "greater-equal"): float_greater_equal,
    ("string", "equal"): string_equal,
    ("string", "not-euqal"): string_not_equal,
    ("binary", "equal"): binary_equal,
    ("binary", "not-equal"): binary_not_equal
}

class BBUCondition(object):
    def __init__(self, name, value_type, operation, value, units):
        self.name = name
        self.value_type = value_type
        self.operation = operation
        self.value = value
        self.units = units
        self.compare = compare_funcs[(self.value_type, self.operation)]

    def __str__(self):
        ret = "Condition: %s, %s, %s %s %s" % (self.name, self.value_type, self.operation, self.value, self.units)
        return ret

    def is_satisfied(self, value, units):
        if self.compare(value, self.value):
            _LOGGER.info("%s is %s %s %s", self.name, self.operation, self.value, self.units)
            return True
        else:
            return False

class BBUDevice(object):
    def __init__(self, name):
        self.name = name
        self.cmd = None
        self.monitors = {}
        self.conditions = {}
        self.condition_type = None
        self.error_filters = {}

    def split_bbu_property(self, value):
        ret = {}
        lines = value.split('\n')
        for line in lines:
            if len(line) == 0:
                continue
            sp = re.split("\(|\)", line)
            data = sp[0].split()
            try:
                raw_data = sp[1]
            except Exception, err:
                raw_data = None
            name = data[0][:-1]
            value = data[1]
            try:
                units = data[2]
            except Exception, err:
                units = None
            ret[name] = (value, units, raw_data)
        return ret
    
    def is_satisfied(self):
        _LOGGER.info("BBU: %s", self.name)
        value = self.cmd.apply()

        properties = self.split_bbu_property(value)
        for name in self.monitors:
            proper = properties[name]
            self.monitors[name].update(proper[0], proper[1])

        # Check Errors
        for name in self.error_filters:
            proper = properties[name]
            if self.error_filters[name].is_satisfied(proper[0], proper[1]) == True:
                raise ValueError("Invalid BBU %s" % (name))

        # Check Conditions
        if self.condition_type == "or":        
            satisfied = False
            for name in self.conditions:
                proper = properties[name]
                if self.conditions[name].is_satisfied(proper[0], proper[1]) == True:
                    satisfied = True
        elif self.condition_type == "and":
            satisfied = True
            for name in self.conditions:
                proper = properties[name]
                if self.conditions[name].is_satisfied(proper[0], proper[1]) == False:
                    satisfied = False
        else:
            raise ValueError("Unknown condition type: %s", self.condition_type)
        return satisfied

    def show(self):
        _LOGGER.info("%s", self.name)
        mesgs = str(self.cmd).split('\n')
        for mesg in mesgs:
            _LOGGER.info("%s", mesg)
        for name in self.monitors.keys():
            _LOGGER.info("%s", self.monitors[name])
        _LOGGER.info("Condition Type: %s", self.condition_type)
        for name in self.conditions:
            _LOGGER.info("%s", self.conditions[name])

#---------------------------------------------------------------------------
# BBU Monitor Item
#---------------------------------------------------------------------------

def analyse_bbu_monitor_node(case, source_node, tag):
    """
    Analyse BBU Monitor node define in XML.
    """
    new_node = etree.Element(tag)
    # Get ref node
    ref = source_node.get("ref")
    ref_node = etree.Element(tag)
    if ref != None:
        ref_node_tmp = case.find(".//%s[@name='%s']" % (tag, ref))
        if ref_node_tmp != None:
            ref_node = analyse_bbu_monitor_node(case, ref_node_tmp, tag)
            new_node = copy.deepcopy(ref_node)
    else:
        new_node = copy.deepcopy(source_node)
    return new_node




class BBUMonitorItem(testcase.TestItem):
    """
    A BBUMonitorItem instance checks BBU status.
    """
    item_type = "bbu-monitor"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.interval = None
        self.monitor_type = None
        self.bbus = []

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_bbu_monitor_node(testcasexml, node, self.item_type)
        # Get monitor_type attribute
        self.monitor_type = node_combined.get("monitor_type")
        if self.monitor_type == "and":
            self.update_action("run", self.action_run_monitor_and)
        elif self.monitor_type == "or":
            self.update_action("run", self.action_run_monitor_or)
        else:
            _LOGGER.error("Unknown monitor type: %s", self.monitor_type)
        # Get interval attribute
        self.interval = float(node_combined.get("interval"))
        # Get BBUs
        for bbu_node in node_combined.findall("bbu"):
            bbu = BBUDevice(bbu_node.get("name"))
            self.bbus.append(bbu)
            # Set Command
            cmd = bbu_node.find("cmd").get("value")
            for optnode in bbu_node.findall("option"):
                cmd += " %s" % (optnode.get("args"))
            proxy = bbu_node.get("proxy")
            if proxy == "local":
                bbu.cmd = CommandLocalViaPopen(cmd)
            elif proxy == "ssh":
                ssh = bbu_node.find("ssh")
                host = ssh.get("host")
                user = ssh.get("user")
                passwd = ssh.get("passwd")
                bbu.cmd = CommandSSH(cmd, host, user, passwd)
            else:
                raise ValueError("Unknown proxy type '%s'", proxy)
            # Set Monitor 
            for mnode in bbu_node.findall("monitor"):
                bbu.monitors[mnode.get("property")] = BBUMonitor(bbu.name,
                                                                  mnode.get("property"),
                                                                  mnode.get("value_type"),
                                                                  mnode.get("units"))
            # Set Condition
            bbu.condition_type = bbu_node.get("condition_type")
            for cnode in bbu_node.findall("condition"):
                bbu.conditions[cnode.get("property")] = BBUCondition(cnode.get("property"),
                                                                      cnode.get("value_type"),
                                                                      cnode.get("operation"),
                                                                      cnode.get("value"),
                                                                      cnode.get("units"))
            # Set error filter
            for cnode in bbu_node.findall("error-filter"):
                bbu.error_filters[cnode.get("property")] = BBUCondition(cnode.get("property"),
                                                                      cnode.get("value_type"),
                                                                      cnode.get("operation"),
                                                                      cnode.get("value"),
                                                                      cnode.get("units"))
        return True

    def action_run_monitor_and(self, kwargs):
        _LOGGER.info("Monitor type: and")
        satisfied = False
        while satisfied == False:
            satisfied = True
            for bbu in self.bbus:
                try:
                    if bbu.is_satisfied() == False:
                        satisfied = False
                except Exception, err:
                    _LOGGER.error("%s", err)
                    retry_succ = False
                    for retry in range(5):
                        _LOGGER.info("Retry again.")
                        try:
                            if bbu.is_satisfied() == False:
                                satisfied = False
                            retry_succ = True
                        except Exception, err:
                             _LOGGER.error("%s", err)
                             time.sleep(0.1)
                             continue
                    if retry_succ == True:
                        continue
                    else:
                        return False
            time.sleep(self.interval)
        return True


    def action_run_monitor_or(self, kwargs):
        _LOGGER.info("Monitor type: or")
        satisfied = False
        while satisfied == False:
            for bbu in self.bbus:
                try:
                    if bbu.is_satisfied() == True:
                        satisfied = True
                except Exception, err:
                    _LOGGER.error("%s", err)
                    retry_succ = False
                    for retry in range(5):
                        _LOGGER.info("Retry again.")
                        try:
                            if bbu.is_satisfied() == True:
                                satisfied = True
                            retry_succ = True
                        except Exception, err:
                             _LOGGER.error("%s", err)
                             time.sleep(0.1)
                             continue
                    if retry_succ == True:
                        continue
                    else:
                        return False
            time.sleep(self.interval)
        return True

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcasexml = kwargs.get("testcase")
        _LOGGER.info("Monitor Type: %s", self.monitor_type)
        _LOGGER.info("Interval: %f s", self.interval)
        for bbu in self.bbus:
            bbu.show()
        return True

