#! /usr/bin/python

"""
Test Item for VPD read/write/check
"""
from lxml import etree
import sys
import os
import tempfile
import copy
import subprocess
import paramiko
import math
from serial import Serial
#sys.path.append("..\\basicplugin\\")
import pmcses

from pycat import log, testcase, status
from basicplugin import bbu
#from command import *

_LOGGER = log.getLogger("log.tc")

def analyse_vpd_node(case, source_node, tag):
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
            ref_node = analyse_vpd_node(case, ref_node_tmp, tag)
            new_node = copy.deepcopy(ref_node)
    else:
        new_node = copy.deepcopy(source_node)
    return new_node

class PmcsesVpdReadItem(testcase.TestItem):
    """
    A PmcsesVpdRead instance execute VPD read commands specially for PMC SES.
    """
    item_type="vpd-read"

    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd           = None
        self.cmdstr        = "rd_seeprom"
        self.cmd_timeout   = "1"
        self.port_id       = "0x00"
        self.device_addr   = "0x52"
        self.offset        = "0x00"
        self.offset_width  = "2"
        self.block_size    = 8
        self.binary_file   = "/tmp/vpd.txt"
        self.proxy         = "uart"
        self.uart_node     = ""
        self.uart_port     = "/dev/ttyUSB0"
        self.uart_baudrate = "115200"
        self.uart_timeout  = "1"
        self.number_bytes_to_read = 8

    def build_cmd_string(self):
        if self.number_bytes_to_read >= self.block_size:
            self.cmdstr = "rd_seeprom" + " " + self.port_id + " " + self.device_addr + " " + self.offset + " " + self.offset_width + " " + (str(self.block_size)) +"\n"
            self.offset = hex(int(self.offset,16) + self.block_size)
        else:
            self.cmdstr = "rd_seeprom" + " " + self.port_id + " " + self.device_addr + " " + self.offset + " " + self.offset_width + " " + (str(self.number_bytes_to_read)) +"\n"
        _LOGGER.info("%s " % self.cmdstr)
        self.cmd = pmcses.PMCCommand( self.cmdstr, self.uart_port,
                                      self.uart_baudrate, self.uart_timeout,
                                      None, self.cmd_timeout,
                                      None,
                                      None,
                                      None)

    def action_init(self, kwargs):
        testcasexml   = kwargs.get("testcase")
        node          = self.parameter.find(self.item_type)
        node_combined = analyse_vpd_node(testcasexml, node, self.item_type)

        self.port_id              = node_combined.find("port-id").get("value")
        self.device_addr          = node_combined.find("device-addr").get("value")
        self.offset               = node_combined.find("offset").get("value")
        self.offset_width         = node_combined.find("offset-width").get("value")
        self.block_size           = int(node_combined.find("block-size").get("value"))
        self.binary_file          = node_combined.find("binary-file").get("value")
        self.number_bytes_to_read = int(node_combined.find("number-bytes-to-read").get("value"))
        self.cmd_timeout          = node_combined.get("timeout")
        self.proxy                = node_combined.get("proxy")
        if self.proxy == "uart":
            self.uart_node        = node_combined.find("uart")
            self.uart_port        = self.uart_node.get("port")
            self.uart_baudrate    = self.uart_node.get("baudrate")
            self.uart_timeout     = self.uart_node.get("timeout")
            PmcsesVpdReadItem.build_cmd_string(self)
        elif self.proxy == "uart-daemon":
            print "Has not supported uart-daemon\n"
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value1 =""
            display_block =0
            f = open(self.binary_file,'w')
            while True:
                value = self.cmd.apply()
                print "self.number_bytes_to_read=%d\n" % self.number_bytes_to_read
                self.number_bytes_to_read -= self.block_size
                start = 13
                end = start + 32*3 -1;
                value1 = ""
                if self.block_size <= 32 or self.number_bytes_to_read+self.block_size <= 32:
                    if self.number_bytes_to_read >= 0 :
                        end = start+self.block_size*3-1
                    else:
                        end = start+(self.number_bytes_to_read+self.block_size)*3-1
                    value1 = value[start:end]
                    #print "value1=%s" %(value1)
                else:
                    #self.cmd.apply return string need to be parse -- 32 bytes in a line
                    if self.number_bytes_to_read>= 0:  
                        display_block = self.block_size
                    else:
                        display_block = self.number_bytes_to_read+ self.block_size
                    end = start + 32*3 -1
                    while display_block > 0:
                        display_block -= 32
                        value1 += value[start:end]
                        if display_block > 0:
                            value1 += " "
                        #ignore return and backspace char 
                        start += 32*3 + 2
                        if display_block < 32:
                           end = start + display_block*3 -1
                        else:
                           end = start + 32*3 - 1
                print "str=\n%s\nvalue1=\n%s" % (str,value1)
                _LOGGER.info("Read %s from eeprom & write to file %s" % (value1, self.binary_file))
                f.write(value1)
                if self.number_bytes_to_read <= 0:
                    f.write("\n")
                    break
                else:
                    f.write(" ")
                PmcsesVpdReadItem.build_cmd_string(self)
            f.close()
        except ValueError:
            return False
        PmcsesVpdReadItem.action_init(self, kwargs)
        _LOGGER.info("Read data from eeprom and save succesfully!")
        print "Read data from eeprom and save successfully"
        return True

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True



class PmcsesVpdWriteItem(testcase.TestItem):
    """
    A PmcsesVpdWriteItem instance execute Vpd write commands specially for PMC SES.
    """
    item_type          = "vpd-write"

    def build_cmd_string(self):
        self.cmdstr= "wr_seeprom" + " " + self.port_id + " " + self.device_addr + " " + self.offset + " " + self.offset_width + " " + self.data_to_write +"\n"
        _LOGGER.info("cmdstr = %s" % self.cmdstr)
        print "cmdstr = %s" % self.cmdstr
        self.cmd = pmcses.PMCCommand( self.cmdstr, self.uart_port,
                                      self.uart_baudrate, self.uart_timeout,
                                      None, self.cmd_timeout,
                                      None,
                                      None,
                                      None)

    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd           = None
        self.cmdstr        = ""
        self.cmd_timeout   = "1"
        self.port_id       = "0x00"
        self.device_addr   = "0x01"
        self.offset        = "0x00"
        self.offset_width  = "2"
        self.block_size    = 8
        self.binary_file   = "/tmp/vpd.txt"
        self.uart_node     = ""
        self.proxy         = "uart"
        self.uart_port     = "/dev/ttyUSB0"
        self.uart_baudrate = "115200"
        self.uart_timeout  = "1"
        self.binary_data   = ""
        self.data_to_write = ""
        self.number_bytes_to_write = 16


    def action_init(self, kwargs):
        # Set command
        cmd           = "wr_seeprom"
        testcasexml   = kwargs.get("testcase")
        node          = self.parameter.find(self.item_type)
        node_combined = analyse_vpd_node(testcasexml, node, self.item_type)

        self.port_id               = node_combined.find("port-id").get("value")
        self.device_addr           = node_combined.find("device-addr").get("value")
        self.offset                = node_combined.find("offset").get("value")
        self.offset_width          = node_combined.find("offset-width").get("value")
        self.block_size            = int(node_combined.find("block-size").get("value"))
        self.binary_file           = node_combined.find("binary-file").get("value")
        self.number_bytes_to_write = int(node_combined.find("number-bytes-to-write").get("value"))
        self.binary_data           = node_combined.find("binary-data").get("value")
        self.cmd_timeout           = node_combined.get("timeout")
        self.proxy                 = node_combined.get("proxy")
        self.data_to_write         = self.binary_data

        if self.proxy == "uart":
            self.uart_node         = node_combined.find("uart")
            self.uart_port         = self.uart_node.get("port")
            self.uart_baudrate     = self.uart_node.get("baudrate")
            self.uart_timeout      = self.uart_node.get("timeout")
            PmcsesVpdWriteItem.build_cmd_string(self)
        elif self.proxy == "uart-daemon":
            _LOGGER.info("Has not supported uart-daemon\n")
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            _LOGGER.info("binary_data = %s,binary_file = %s"  %(self.binary_data, self.binary_file))
            print self.binary_data
            print self.binary_file
            if self.binary_data == "":
                f = open(self.binary_file)
                str = f.read(2)
                if str == "":
                   _LOGGER.info("Binary file %s is null" , self.binary_file)
                   print "Binary file %s is null" %self.binary_file
                   return False
                f.read(1)
                self.data_to_write = str
                PmcsesVpdWriteItem.build_cmd_string(self)
                while str:
                    self.cmd.apply()
                    self.number_bytes_to_write -= 1
                    if self.number_bytes_to_write <= 0:
                        break
                    else:
                        self.data_to_write = f.read(2)
                        f.read(1)
                    self.offset = hex(int(self.offset,16) + 0x01)
                    PmcsesVpdWriteItem.build_cmd_string(self)
                f.close()
            else:
                self.data_to_write = self.binary_data
                while True:
                    self.cmd.apply()
                    self.number_bytes_to_write -= 1
                    if self.number_bytes_to_write <= 0:
                        break
                    self.offset = hex(int(self.offset,16) + 0x01)
                    PmcsesVpdWriteItem.build_cmd_string(self)
        except ValueError:
            return False
        PmcsesVpdWriteItem.action_init(self, kwargs)
        _LOGGER.info("Write to eeprom successfully!")
        print "Write to eeprom successfully!"
        return True

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True



class PmcsesVpdCheckItem(testcase.TestItem):
    """
    A PmcsesVpdCheck instance execute vpd read commands specially for PMC SES, then parse the returned message.
    """
    item_type = "vpd-check"
    constant_value = None

    def build_cmd_string(self):
        if self.number_bytes_to_check >= self.block_size:
            self.cmdstr = "rd_seeprom" + " " + self.port_id + " " + self.device_addr + " " + self.offset + " " + self.offset_width + " " + (str(self.block_size)) +"\r\n"
            self.offset = hex(int(self.offset,16) + self.block_size)
        else:
            self.cmdstr = "rd_seeprom" + " " + self.port_id + " " + self.device_addr + " " + self.offset + " " + self.offset_width + " " + (str(self.number_bytes_to_check)) +"\r\n"
        _LOGGER.info("cmdstr = %s" % self.cmdstr)
        #print "cmdstr =%s" % self.cmdstr
        self.cmd = pmcses.PMCCommand( self.cmdstr, self.uart_port,
                                      self.uart_baudrate, self.uart_timeout,
                                      None, self.cmd_timeout,
                                      None,
                                      None,
                                      None)

    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd                   = None
        self.cmdstr                = "rd_seeprom"
        self.cmd_timeout           = "1"
        self.port_id               = "0x00"
        self.device_addr           = "0x01"
        self.offset                = "0x00"
        self.offset_width          = "1"
        self.block_size            = 128
        self.binary_file           = "/tmp/vpd.txt"
        self.proxy                 = "uart"
        self.uart_node             = ""
        self.uart_port             = "/dev/ttyUSB0"
        self.uart_timeout          = "1"
        self.uart_baudrate         = "115200"
        self.number_bytes_to_check = 4096

    def action_init(self, kwargs):
        cmd                        = None
        testcasexml                = kwargs.get("testcase")
        node                       = self.parameter.find(self.item_type)
        node_combined              = analyse_vpd_node(testcasexml, node, self.item_type)
        self.port_id               = node_combined.find("port-id").get("value")
        self.device_addr           = node_combined.find("device-addr").get("value")
        self.offset                = node_combined.find("offset").get("value")
        self.offset_width          = node_combined.find("offset-width").get("value")
        self.block_size            = int(node_combined.find("block-size").get("value"))
        self.binary_file           = node_combined.find("binary-file").get("value")
        self.number_bytes_to_check = int(node_combined.find("number-bytes-to-check").get("value"))
        self.binary_data           = node_combined.find("binary-data").get("value")
        self.proxy                 = node_combined.get("proxy")
        self.cmd_timeout           = node_combined.get("timeout")
        if self.proxy == "uart":
            self.uart_node         = node_combined.find("uart")
            self.uart_port         = self.uart_node.get("port")
            self.uart_baudrate     = self.uart_node.get("baudrate")
            self.uart_timeout      = self.uart_node.get("timeout")
            PmcsesVpdCheckItem.build_cmd_string(self)
        elif self.proxy == "uart-daemon":
            _LOGGER.info( "Has not supported uart-daemon\n")
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True


    def action_run(self, kwargs):
        """
        Execute the command.
        """
        ret = True
        count = 0
        display_block = 0
        bdata = 0
        str=""
        try:
            if self.binary_data == "":
                f = open(self.binary_file)
                if self.number_bytes_to_check <= self.block_size :
                   str = f.read(self.number_bytes_to_check*3-1)
                else:
                   str = f.read(self.block_size*3-1)
                if str == "":
                   _LOGGER.info("biniary file is null , please check it")
                   print "biniary file is null , please check it"
                   return False
            else:
                if self.binary_data[1] == "x":
                   bdata = self.binary_data[2:4]
                   bdata = bdata+" "
                else:
                   bdata = self.binary_data+" "
                str = bdata
            while str:
                if self.binary_data != "":
                    if self.number_bytes_to_check <= self.block_size:
                       str = data*self.number_bytes_to_check
                    else:
                       str =bdata*self.block_size
                    length = len(str)-1
                    str = str[0:length]
                value = self.cmd.apply()
                start = 13
                end = start + 32*3 -1;
                value1 = ""
                self.number_bytes_to_check -= self.block_size
                #print "block_size=%d, number_bytes_to_check=%d" %(self.block_size, self.number_bytes_to_check)
                if self.block_size <= 32 or (self.number_bytes_to_check + self.block_size) <= 32:
                    if self.number_bytes_to_check >= 0:
                        end = start + self.block_size*3 - 1
                    else:
                        end = start + (self.number_bytes_to_check+self.block_size)*3 - 1
                    value1 = value[start:end]
                else:
                    if self.number_bytes_to_check >= 0:  
                        display_block = self.block_size
                    else:
                        display_block = self.number_bytes_to_check + self.block_size
                    while display_block > 0:
                        display_block -= 32
                        value1 += value[start:end]
                        if display_block > 0:
                            value1 += " "
                        start += 32*3 + 2
                        if display_block < 32:
                            end = start + display_block*3 -1
                        else:
                            end = start + 32*3 -1
                print "\nvalue1=%s\nstr=%s\n" %(value1, str)
                if value1 != str:
                   _LOGGER.info("Block %d is not match!" %(count))
                   print "Block %d is not match!" %(count)
                   if self.binary_data == "":
                      f.close()
                   return False
                _LOGGER.info("Block %d is match..." %(count))
                count += 1
                if self.binary_data == "":
                   f.read(1)
                   if self.number_bytes_to_check <= self.block_size:
                      str = f.read(self.number_bytes_to_check*3-1)
                   else:
                      str = f.read(self.block_size*3-1)

                if self.number_bytes_to_check <= 0:
                   break
                PmcsesVpdCheckItem.build_cmd_string(self)
            if self.binary_data == "":
                f.close()
            else:
                pass
        except ValueError:
            return False
        PmcsesVpdCheckItem.action_init(self, kwargs)
        _LOGGER.info("In total, %d blocks are match successfully!" %(count))
        print "%d blocks are match successfully" % count
        return ret

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True
