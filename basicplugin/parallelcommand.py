#! /usr/bin/python

"""
Command test items.
"""

from lxml import etree
import os
import re
import tempfile
import copy
import subprocess
import paramiko
import serial
import time
import threading
from pycat.cmdexec import CommandSSH

from pycat import log, testcase

_LOGGER = log.getLogger("log.tc")

class SSHThread(threading.Thread):
    def __init__(self, cmd):
        threading.Thread.__init__(self)
        # self.name = name
        self.cmd = cmd
        self.exit_status = True

    def run(self):
        try:
            value = self.cmd.apply()
        except OSError:
            self.exit_status = False

def analyse_node_default(case, source_node, tag):
    """
    Analyse item node define in XML.
    If find 'ref' node, use it. Ohterwise use the current one.
    """
    new_node = etree.Element(tag)
    # Get ref node
    ref = source_node.get("ref")
    ref_node = etree.Element(tag)
    if ref != None:
        ref_node_tmp = case.find(".//%s[@name='%s']" % (tag, ref))
        if ref_node_tmp != None:
            ref_node = analyse_node_default(case, ref_node_tmp, tag)
            new_node = copy.deepcopy(ref_node)
    else:
        new_node = copy.deepcopy(source_node)
    return new_node

class ParrallelCommandItem(testcase.TestItem):
    """
    A Command instance execute a command through local shell, SSH or uart.
    Supported proxy:
        * local, Execute a command on local shell.
        * ssh, Execute a command through SSH.
        * uart, Execute a command through uart.
    """
    item_type = "parallel-command"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.host = None
        self.user = None
        self.passwd = None
        self.cmd_list = []

    def action_init(self, kwargs):
        """
        Initialize command. Analyse command and chose a proxy.
        """
        testcase = kwargs.get("testcase")
        cmd_node = self.parameter.find(self.item_type)
        cmd_node_combined = analyse_node_default(testcase, cmd_node, self.item_type)
        deamon = cmd_node_combined.get("deamon")
        if deamon == "True":
            self.deamon = True
        else:
            self.deamon = False
        proxy = cmd_node_combined.get("proxy")
        if proxy == "ssh":
            ssh = cmd_node_combined.find("ssh")
            self.host = ssh.get("host")
            self.user = ssh.get("user")
            self.passwd = ssh.get("passwd")
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        for node in cmd_node_combined.findall("cmd"):
            value = node.get("value")
            label = node.get("label")
            self.cmd_list.append((value, label))

        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        sshthread_list = []
        for cmd_info in self.cmd_list:
            cmd = CommandSSH(cmd_info[0], self.host, self.user, self.passwd, label=cmd_info[1])
            sshthread = SSHThread(cmd)
            sshthread_list.append(sshthread)
        for sshthread in sshthread_list:
            sshthread.start()
        if self.deamon == False:
            for sshthread in sshthread_list:
                sshthread.join()
        ret = True
        for sshthread in sshthread_list:
            if sshthread.exit_status == True:
                continue
            else:
                ret = False
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
        _LOGGER.info("SSH host: %s, user: %s, passwd: %s", self.host, self.user, self.passwd)
        _LOGGER.info("cmmand list: %s", self.cmd_list)

        return True