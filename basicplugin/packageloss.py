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

# class SSHThread(threading.Thread):
#     def __init__(self, cmd):
#         threading.Thread.__init__(self)
#         # self.name = name
#         self.cmd = cmd
#         self.exit_status = True

#     def run(self):
#         try:
#             value = self.cmd.apply()
#         except OSError:
#             self.exit_status = False

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

class PackageLossItem(testcase.TestItem):
    item_type = "package-loss"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.host = None
        self.user = None
        self.passwd = None
        self.p2p_list = []

    def action_init(self, kwargs):
        """
        Initialize command. Analyse command and chose a proxy.
        """
        testcase = kwargs.get("testcase")
        cmd_node = self.parameter.find(self.item_type)
        cmd_node_combined = analyse_node_default(testcase, cmd_node, self.item_type)
        proxy = cmd_node_combined.get("proxy")
        if proxy == "ssh":
            ssh = cmd_node_combined.find("ssh-a")
            self.host_a = ssh.get("host")
            self.user_a = ssh.get("user")
            self.passwd_a = ssh.get("passwd")
            ssh = cmd_node_combined.find("ssh-b")
            self.host_b = ssh.get("host")
            self.user_b = ssh.get("user")
            self.passwd_b = ssh.get("passwd")
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        for node in cmd_node_combined.findall("p2p"):
            port_a = node.get("port-a")
            eth_a = node.get("eth-a")
            port_b = node.get("port-b")
            eth_b = node.get("eth-b")
            self.p2p_list.append((port_a, eth_a, port_b, eth_b))

        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        for p2p in self.p2p_list:
            cmd_str = "ifconfig %s" % (p2p[1])
            porta_cmd = CommandSSH(cmd_str, self.host_a, self.user_a, self.passwd_a, label=p2p[0])
            cmd_str = "ifconfig %s" % (p2p[3])
            portb_cmd = CommandSSH(cmd_str, self.host_b, self.user_b, self.passwd_b, label=p2p[2])
            try:
                value = porta_cmd.apply()
                match = re.search("RX packets[: ][0123456789]*", value)
                porta_rx = int(match.group(0)[11:])
                match = re.search("TX packets[: ][0123456789]*", value)
                porta_tx = int(match.group(0)[11:])
                _LOGGER.info("<%s> RX: %d, TX: %d", p2p[0], porta_rx, porta_tx)

                value = portb_cmd.apply()
                match = re.search("RX packets[: ][0123456789]*", value)
                portb_rx = int(match.group(0)[11:])
                match = re.search("TX packets[: ][0123456789]*", value)
                portb_tx = int(match.group(0)[11:])
                _LOGGER.info("<%s> RX: %d, TX: %d", p2p[0], portb_rx, portb_tx)

                loss_b_to_a = ((portb_tx - porta_rx) * 1.0 / portb_tx) * 100
                loss_a_to_b = ((porta_tx - portb_rx) * 1.0 / porta_tx) * 100
                _LOGGER.info("%s TX to %s RX: %0.3f%%", p2p[2], p2p[0], loss_b_to_a)
                _LOGGER.info("%s TX to %s RX: %0.3f%%", p2p[0], p2p[2], loss_a_to_b)

            except OSError:
                return False
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
        _LOGGER.info("SSH-A host: %s, user: %s, passwd: %s", self.host_a, self.user_a, self.passwd_a)
        _LOGGER.info("SSH-B host: %s, user: %s, passwd: %s", self.host_b, self.user_b, self.passwd_b)
        _LOGGER.info("P2P list: %s", self.p2p_list)

        return True












