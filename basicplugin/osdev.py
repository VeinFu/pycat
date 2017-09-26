#! /usr/bin/python

"""
OS and Device Test Items.
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


#--------------------------------------------------------------------------
#  Device Memory
#--------------------------------------------------------------------------
class DeviceMemItem(testcase.TestItem):
    """
    A DeviceHddItem instance checks HDD devices on OS. 
    """
    item_type = "device-mem"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.capacity = 0

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_node_default(testcasexml, node, self.item_type)
        # Set command
        os = node_combined.get("os")
        if os is None or os == "linux":
            cmd = "cat /proc/meminfo | grep MemTotal | awk '{print $2}'"
        elif os == "soloris":
            cmd = "prtconf | grep ^M | awk '{print $3}'"
        else:
            raise ValueError("Unknown OS type '%s'", os)        
        
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

        # Set capacity
        self.capacity = int(node_combined.find("capacity").get("value"))
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
	value = 0
        try:
            value = int(self.cmd.apply())
        except OSError:
            return False
        except ValueError:
            return False
        if value == self.capacity:
            _LOGGER.info("Find %d kB memory.", value)
            return True
        else:
            _LOGGER.error("Find %d disks, expect %d.", value, self.capacity)
            return False

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcasexml = kwargs.get("testcase")
        self.cmd.show()
        _LOGGER.info("Memory: %d", self.capacity)
        return True


#--------------------------------------------------------------------------
#  Device HDD
#--------------------------------------------------------------------------
def analyse_device_hdd_node(case, source_node, tag):
    """
    Analyse device-hdd node define in XML.
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

class DeviceHddItem(testcase.TestItem):
    """
    A DeviceHddItem instance checks HDD devices on OS. 
    """
    item_type = "device-hdd"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.number = 0
        self.os = None

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_device_hdd_node(testcasexml, node, self.item_type)
        # Set command
        # Set command
        self.os = node_combined.get("os")
        if self.os is None or self.os == "linux":
            self.os = "linux"
            cmd = "fdisk -l"
        elif self.os == "soloris":
            cmd = "iostat -nE | grep ^c | wc -l"
        else:
            raise ValueError("Unknown OS type '%s'", self.os)            
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
        # Set number
        self.number = int(node_combined.find("number").get("value"))
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd.apply()
        except OSError:
            return False
        if self.os == "linux":
            value = value.split("\n")
            count = 0
            for line in value:
                #print "'%s'" % line
                if len(line) == 0 or line.isspace():
                    continue
                mat = re.match("Disk /dev", line)
                #print mat.group()
                if mat != None:
                    count += 1
        elif self.os == "soloris":
            count = int(value)
        if count == self.number:
            _LOGGER.info("Find %d disks.", count)
            return True
        else:
            _LOGGER.error("Find %d disks, expect %d.", count, self.number)
            return False

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcasexml = kwargs.get("testcase")
        self.cmd.show()
        _LOGGER.info("Device Number: %d", self.number)
        return True

#--------------------------------------------------------------------------
#  Device Netif
#--------------------------------------------------------------------------
def analyse_device_netif_node(case, source_node, tag):
    """
    Analyse device-netif node define in XML.
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

class DeviceNetifItem(testcase.TestItem):
    """
    A DeviceNetItem instance checks network interface on OS. 
    """
    item_type = "device-netif"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.number = 0

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_device_hdd_node(testcasexml, node, self.item_type)
        # Set command
        cmd = "ifconfig -a"
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
        # Set number
        self.number = int(node_combined.find("number").get("value"))
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd.apply()
        except OSError:
            return False
        value = value.split("\n")
        count = 0
        for line in value:
            if len(line) == 0 or line.isspace():
                continue
            mat = re.match("[a-zA-Z0-9_]*:?[ \t]*", line)
            if mat != None:
                count += 1
        if count == self.number:
            _LOGGER.info("Find %d network interface.", count)
            return True
        else:
            _LOGGER.error("Find %d network interface, expect %d.", count, self.number)
            return False

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcasexml = kwargs.get("testcase")
        self.cmd.show()
        _LOGGER.info("Device Number: %d", self.number)
        return True

#--------------------------------------------------------------------------
#  Device PCI
#--------------------------------------------------------------------------
def analyse_device_pci_node(case, source_node, tag):
    """
    Analyse device-pci node define in XML.
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

class DevicePciItem(testcase.TestItem):
    """
    A DevicePciItem instance checks PCI devices on OS. 
    """
    item_type = "device-pci"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.number = 0

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_device_hdd_node(testcasexml, node, self.item_type)
        # Set command
        cmd = "lspci"
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
        # Set number
        self.number = int(node_combined.find("number").get("value"))
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd.apply()
        except OSError:
            return False
        value = value.split("\n")
        count = 0
        for line in value:
            if len(line) == 0 or line.isspace():
                continue
            count += 1
        if count == self.number:
            _LOGGER.info("Find %d PCI devices.", count)
            return True
        else:
            _LOGGER.error("Find %d PCI devices, expect %d.", count, self.number)
            return False

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcasexml = kwargs.get("testcase")
        self.cmd.show()
        _LOGGER.info("Device Number: %d", self.number)
        return True


#--------------------------------------------------------------------------
#  Device SCSI
#--------------------------------------------------------------------------
def analyse_device_scsi_node(case, source_node, tag):
    """
    Analyse device-scsi node define in XML.
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

class DeviceScsiItem(testcase.TestItem):
    """
    A DeviceScsiItem instance checks SCSI devices on OS. 
    """
    item_type = "device-scsi"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.number = 0

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_device_hdd_node(testcasexml, node, self.item_type)
        # Set command
        cmd = "lsscsi"
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
        # Set number
        self.number = int(node_combined.find("number").get("value"))
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd.apply()
        except OSError:
            return False
        value = value.split("\n")
        count = 0
        for line in value:
            if len(line) == 0 or line.isspace():
                continue
            count += 1
        if count == self.number:
            _LOGGER.info("Find %d SCSI devices.", count)
            return True
        else:
            _LOGGER.error("Find %d SCSI devices, expect %d.", count, self.number)
            return False

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcasexml = kwargs.get("testcase")
        self.cmd.show()
        _LOGGER.info("Device Number: %d", self.number)
        return True

#--------------------------------------------------------------------------
#  Memory Dump
#--------------------------------------------------------------------------
def analyse_memory_dump_node(case, source_node, tag):
    """
    Analyse memory-dump node define in XML.
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

class MemoryDumpItem(testcase.TestItem):
    """
    A MemoryDumpItem instance copy data from /dev/zero to disk. 
    """
    item_type = "memory-dump"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.cmd_show_file = None
        self.size = None
        self.units = None
        self.output = None

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_device_hdd_node(testcasexml, node, self.item_type)
        # Set size
        self.size = float(node_combined.find("size").get("value"))
        self.units = node_combined.find("size").get("units")
        if self.units == "KB":
            nkb = 1
        elif self.units == "MB":
            nkb = 1000
        elif self.units == "GB":
            nkb = 1000*1000
        size = int(self.size * nkb)

        # Set output
        self.output = node_combined.find("output").get("path")

        # Set command
        cmd = "dd if=/dev/zero of=%s bs=1000 count=%d" % (self.output, size)
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
            return False

        cmd = "ls -l %s" % (self.output)
        if proxy == "local":
            self.cmd_show_file = CommandLocalViaPopen(cmd)
        elif proxy == "ssh":
            ssh = node_combined.find("ssh")
            host = ssh.get("host")
            user = ssh.get("user")
            passwd = ssh.get("passwd")
            self.cmd_show_file = CommandSSH(cmd, host, user, passwd)
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
            return False
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd.apply()
        except OSError:
            return False
        try:
            value = self.cmd_show_file.apply()
        except OSError:
            return False
        return True

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcasexml = kwargs.get("testcase")
        self.cmd.show()
        _LOGGER.info("Dump %f%s data from /dev/zero to %s.", self.size, self.units, self.output)
        return True

#--------------------------------------------------------------------------
#  File Check MD5 Sum
#--------------------------------------------------------------------------
def analyse_file_check_sum_node(case, source_node, tag):
    """
    Analyse file-check-sum node define in XML.
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

class FileCheckSumItem(testcase.TestItem):
    """
    A FileCheckSumItem instance check file's MD5. 
    """
    item_type = "file-check-sum"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.cmd_show_file = None
        self.path = None
        self.md5 = None
        self.remove_file = None

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_device_hdd_node(testcasexml, node, self.item_type)
        # Set path
        self.path = node_combined.find("path").get("value")
        # Set MD5
        self.md5 = node_combined.find("md5").get("value")
        # Set remove_file flag
        remove_file = node_combined.find("remove-file").get("value")
        if remove_file == "true":
            self.remove_file = True
        else:
           self.remove_file == False

        # Set command
        cmd = "md5sum %s" % (self.path)
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
            return False
        cmd = "ls -l %s" % (self.path)
        if proxy == "local":
            self.cmd_show_file = CommandLocalViaPopen(cmd)
        elif proxy == "ssh":
            ssh = node_combined.find("ssh")
            host = ssh.get("host")
            user = ssh.get("user")
            passwd = ssh.get("passwd")
            self.cmd_show_file = CommandSSH(cmd, host, user, passwd)
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
            return False
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd_show_file.apply()
        except OSError:
            return False

        ret = False
        try:
            value = self.cmd.apply()
        except OSError:
            return False
        value = value.split(" ")
        if self.md5 == value[0]:
            ret = True
        else:
            _LOGGER.warning("Expect value is %s", self.md5)
            ret = False
        if self.remove_file == True:
            _LOGGER.info("Remove %s", self.path)
            try:
                os.remove(self.path)
            except OSError, err:
                _LOGGER.warn("%s", err)
                return False
        return ret

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcasexml = kwargs.get("testcase")
        self.cmd.show()
        _LOGGER.info("Check %s MD5, expect value is %s.", self.path, self.md5)
        if self.remove_file == True:
            _LOGGER.info("Remove file after the file's MD5 is checked.")
        return True

