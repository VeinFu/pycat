#! /usr/bin/python

from lxml import etree
import os
import time
import copy
from serial import Serial
import pmcses

from pycat import log, testcase, status
from basicplugin import command

_LOGGER = log.getLogger("log.tc")


def analyse_powercycle_node(case, source_node, tag):
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

class SESComphycheckItem(testcase.TestItem):

    item_type = "check_phy"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.dict = {}
        self.cmd = None

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node = analyse_powercycle_node(testcasexml, node, self.item_type)
        #node_combined = analyse_ses_command_node(testcasexml, node, self.item_type)
        # Set command
        phymaptree = node.find("phy_map")
        for optphy in phymaptree.findall("phy"):
            list_phyresult = []
            va = optphy.get("name")
            phyid_list = optphy.get("phy_id").split(",")
            for i in phyid_list:
                if -1 != i.find("-"):
                    subphyid_list = i.split("-")
                    subphyidrange_list = range(int(subphyid_list[0]), int(subphyid_list[1]) + 1)
                    for j in subphyidrange_list:
                        list_phyresult.append(int(j))
                else:
                    list_phyresult.append(str(i))
            if va == "12G":
                item = {"12G": list_phyresult}
                self.dict.update(item)
            elif va == "6G":
                item = {"6G": list_phyresult}
                self.dict.update(item)
            elif va == "3G":
                item = {"3G": list_phyresult}
                self.dict.update(item)
            elif va == "1.5G":
                item = {"1.5G": list_phyresult}
                self.dict.update(item)
            else:
                raise ValueError("unknow phy rate")
        cmd = node.find("cmd").get("value")
        cmd_timeout = node.find("cmd").get("timeout")
        cmd_recv = node.find("cmd").get("recv")

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


    def parse_phyinfo(self, value):
        phy_dict = {}
        phy_list = []
        for i in value.split("\r\n"):
            if -1 != i.find("Rate=12G"):
                phy_12G = i.strip()
                phy_list.append(phy_12G)
            elif -1 != i.find("Rate=6G"):
                phy_6G = i.strip()
                phy_list.append(phy_6G)
            elif -1 != i.find("Rate=3G"):
                phy_3G = i.strip()
                phy_list.append(phy_3G)
            elif -1 != i.find("Rate=1.5G"):
                phy_1G = i.strip()
                phy_list.append(phy_1G)
        for i in phy_list:
            phy_value_list = []
            phy_result_list = []
            phy_tuple = i.partition(" ")
            phy_value = phy_tuple[2].strip()
            phy_value_list = phy_value.split("  ")
            for opt in range(len(phy_value_list)):
                if phy_value_list[opt] == "*":
                    phy_result_list.append(opt)
            if phy_result_list == []:
                phy_result_list.append("")
            if -1 != i.find("Rate=12G"):
                item = {"12G": phy_result_list}
                phy_dict.update(item)
            elif -1 != i.find("Rate=6G"):
                item = {"6G": phy_result_list}
                phy_dict.update(item)
            elif -1 != i.find("Rate=3G"):
                item = {"3G": phy_result_list}
                phy_dict.update(item)
            else:
                item = {"1.5G": phy_result_list}
                phy_dict.update(item)

        return phy_dict

    def compare_phyinfo(self, phy_dict):
        ret = True
        keys_list = self.dict.keys()
        for i in keys_list:
            if self.dict[i] == phy_dict[i]:
                _LOGGER.info("Check Rate=%s phy pass" % i)
            else:
                _LOGGER.info("Check Rate=%s phy fail,the xml value:%s,the output value:%s" % (i, self.dict[i], phy_dict[i]))
                ret = False
        return ret

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd.apply()
        except ValueError:
            return False
        phy_dict = self.parse_phyinfo(value)
        ret = self.compare_phyinfo(phy_dict)
        if ret:
            return True
        else:
            return False

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True



class SESCommandchkhddtempItem(testcase.TestItem):
    """
    A SESCommandItem instance executes SES commands. 
    """
    item_type = "ses-command-chkhddtemp"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.tempmax = ""
        self.tempmin = ""

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_powercycle_node(testcasexml, node, self.item_type)
        # Set command
        cmd_node = node_combined.find("cmd")
        cmd = cmd_node.get("value")
        for optnode in node_combined.findall("option"):
            cmd += " %s" % (optnode.get("args"))
        cmd_timeout = cmd_node.get("timeout")
        cmd_recv = cmd_node.get("recv")
        self.tempmax = node_combined.find("temp").get("tempmax")
        self.tempmin = node_combined.find("temp").get("tempmin")

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
        ret = self.compare_tempvalue(value)
        if ret == 0:
            return True
        else:
            return False

    def compare_tempvalue(self, value):
        ret = 0
        for line in value.split("\r\n"):
            if -1 != line.find("Drive"):
                templine = line.strip().split(":")
                temp = templine[1].strip().split("'")[0]
                if int(temp) < int(self.tempmin) or int(temp) > int(self.tempmax):
                    slot = templine[0].split(" ")[0]
                    _LOGGER.info("Check the %s temp fail,the output temp:%s,the set temp scope %s-%s" % (slot, temp, self.tempmin, self.tempmax))
                    ret = 1
        if ret == 0:
            _LOGGER.info("Check all temp pass.")
        return ret

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True



class SESCommandchkhddrateItem(testcase.TestItem):
    """
    A SESCommandItem instance executes SES commands. 
    """
    item_type = "ses-command-chkhddrate"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
       # self.ratemax = ""
        self.rate_list = ""

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_powercycle_node(testcasexml, node, self.item_type)
        # Set command
        cmd_node = node_combined.find("cmd")
        cmd = cmd_node.get("value")
        for optnode in node_combined.findall("option"):
            cmd += " %s" % (optnode.get("args"))
        cmd_timeout = cmd_node.get("timeout")
        cmd_recv = cmd_node.get("recv")
      #  self.ratemax = node_combined.find("rate").get("ratemax")
        self.rate_list = node_combined.find("rate").get("rate").split(",")

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
        ret = self.compare_ratevalue(value)
        if ret == 0:
            return True
        else:
            return False

#    def compare_ratevalue(self, value):
#        ret = 0
#        rate_list = []
#        for line in value.split("\r\n"):
#            if -1 != line.find("Drive"):
#                tuple_value = line.partition("[")
#                slot = tuple_value[0].strip()
#                for i in range(5):
#                    tuple_value = tuple_value[2].strip().partition(" ")
#                    if i == 4:
#                        rate = tuple_value[2].strip()
#                        rate_list.append(rate)
#        if len(rate_list) == len(self.rate_list):
#            for i in range(len(rate_list)):
#                if rate_list[i] != self.rate_list[i]:
#                    _LOGGER.info("Check the Drive Slot #%s rate fail,the output:%s,the set:%s." % (i + 1, rate_list[i], self.rate_list[i]))
#                    ret = 1
#        else:
#            _LOGGER.info("Check rate count fail,please check set count.")
#            return -1
#
#        if ret == 0:
#            _LOGGER.info("Check all Drive rate pass.")
#
#        return ret

    def compare_ratevalue(self, value):
        ret = 0
        rate_list = []
        for line in value.split("\r\n"):
            if -1 != line.find("Drive"):
                tuple_value = line.strip().partition(" ")
                slot_id = tuple_value[0]
                for i in range(10):
                    tuple_value = tuple_value[2].strip().partition(" ")
                    if i < 2:
                        slot_id = slot_id + " " + tuple_value[0]
                    if tuple_value[2] == "":
                        rate = tuple_value[0]
                        rate_list.append(rate)
                        break

        if len(rate_list) == len(self.rate_list):
            for i in range(len(rate_list)):
                if rate_list[i] != self.rate_list[i]:
                    _LOGGER.info("Check the Drive Slot #%s rate fail,the output:%s,the set:%s." % (i + 1, rate_list[i], self.rate_list[i]))
                    ret = 1
        else:
            _LOGGER.info("Check rate count fail,please check set count.")
            return -1

        if ret == 0:
            _LOGGER.info("Check all Drive rate pass.")

        return ret

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True



class SESCommandchkfrugetItem(testcase.TestItem):
    """
    A SESCommandItem instance executes SES commands. 
    """
    item_type = "ses-command-chkfruget"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.canafw = ""
        self.canacpld = ""
        self.psafw = ""
        self.psasn = ""
        self.psapn = ""
        self.canbfw = ""
        self.canbcpld = ""
        self.psbfw = ""
        self.psbsn = ""
        self.psbpn = ""        

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_powercycle_node(testcasexml, node, self.item_type)
        # Set command
        cmd_node = node_combined.find("cmd")
        cmd = cmd_node.get("value")
        for optnode in node_combined.findall("option"):
            cmd += " %s" % (optnode.get("args"))
        cmd_timeout = cmd_node.get("timeout")
        cmd_recv = cmd_node.get("recv")
        fruget_node = node_combined.find("fruget")

        self.canafw = fruget_node.get("canafw")
        self.canacpld = fruget_node.get("canacpld")
        self.psafw = fruget_node.get("psafw")
        self.psasn = fruget_node.get("psasn")
        self.psapn = fruget_node.get("psapn")
        self.canbfw = fruget_node.get("canbfw")
        self.canbcpld = fruget_node.get("canbcpld")
        self.psbfw = fruget_node.get("psbfw")
        self.psbsn = fruget_node.get("psbsn")
        self.psbpn = fruget_node.get("psbpn") 


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
        ret = self.compare_frugetvalue(value)
        if ret == 0:
            return True
        else:
            return False

    def compare_frugetvalue(self, value):
        ret = 0
        list_key = ["ESM A", "ESM B", "PS A", "PS B"]
        list_index = []
        for item in list_key:
            i = value.find(item)
            if -1 == i:
                _LOGGER.info("find key %s fail" % item)
                return 1
            list_index.append(i)
        value_esma = value[list_index[0]:list_index[1]]
        value_esmb = value[list_index[1]:list_index[2]]
        value_psa = value[list_index[2]:list_index[3]]
        value_psb = value[list_index[3]:]
        if -1 != value_esma.find("NotIstall"):
            cana_fw = ""
            cana_cpld = ""
        else:
            for line in value_esma.split("\r\n"):
                if -1 != line.find("FW Revision"):
                    cana_fw = line.split(" ")[2].strip()
                elif -1 != line.find("CPLD Revision Code"):
                    cana_cpld = line.split(":")[1].strip()
        if -1 != value_esmb.find("NotIstall"):
            canb_fw = ""
            canb_cpld = ""
        else:
            for line in value_esmb.split("\r\n"):
                if -1 != line.find("FW Revision"):
                    canb_fw = line.split(" ")[2].strip()
                elif -1 != line.find("CPLD Revision Code"):
                    canb_cpld = line.split(":")[1].strip()

        if -1 != value_psa.find("NotIstall"):
            psa_sn = ""
            psa_pn = ""
            psa_fw = ""
        else:
            for line in value_psa.split("\r\n"):
                if -1 != line.find("PS Serial Number"):
                    psa_sn = line.split(":")[1].strip()
                elif -1 != line.find("PS Part Number"):
                    psa_pn = line.split(":")[1].strip()
                elif -1 != line.find("PS Firmware Version"):
                    psa_fw = line.split(":")[1].strip()

        if -1 != value_psb.find("NotIstall"):
            psb_sn = ""
            psb_pn = ""
            psb_fw = ""
        else:
            for line in value_psb.split("\r\n"):
                if -1 != line.find("PS Serial Number"):
                    psb_sn = line.split(":")[1].strip()
                elif -1 != line.find("PS Part Number"):
                    psb_pn = line.split(":")[1].strip()
                elif -1 != line.find("PS Firmware Version"):
                    psb_fw = line.split(":")[1].strip()
        list_title = ["canafw", "canacpld", "canbfw", "canbcpld", "psasn", "psapn", "psafw",
                      "psbsn", "psbpn", "psbfw"]
        list_set = [self.canafw, self.canacpld, self.canbfw, self.canbcpld, self.psasn, 
                    self.psapn, self.psafw, self.psbsn, self.psbpn, self.psbfw]
        list_get = [cana_fw, cana_cpld, canb_fw, canb_cpld, psa_sn, psa_pn, psa_fw,
                    psb_sn, psb_pn, psb_fw]
        for i in range(len(list_set)):
            if list_set[i] != list_get[i]:
                _LOGGER.info("Check %s fail,set:%s,get:%s" % (list_title[i], list_set[i], list_get[i]))
                ret = 1
  #          else:
  #              _LOGGER.info("Check %s pass." % list_title[i])
        if ret == 0:
            _LOGGER.info("Check all fru get info pass.")

        return ret

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True


class SESCommandchkfanspdItem(testcase.TestItem):
    """
    A SESCommandItem instance executes SES commands. 
    """
    item_type = "ses-command-chkfanspd"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
       # self.ratemax = ""
        self.ps_fan_max = ""
        self.ps_fan_min = ""
        self.sys_fan_max = ""
        self.sys_fan_min = ""

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_powercycle_node(testcasexml, node, self.item_type)
        # Set command
        cmd_node = node_combined.find("cmd")
        cmd = cmd_node.get("value")
        for optnode in node_combined.findall("option"):
            cmd += " %s" % (optnode.get("args"))
        cmd_timeout = cmd_node.get("timeout")
        cmd_recv = cmd_node.get("recv")
      #  self.ratemax = node_combined.find("rate").get("ratemax")
        self.ps_fan_max = node_combined.find("fanspd").get("psfanmax")
        self.ps_fan_min = node_combined.find("fanspd").get("psfanmin")
        self.sys_fan_max = node_combined.find("fanspd").get("sysfanmax")
        self.sys_fan_min = node_combined.find("fanspd").get("sysfanmin")


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
        ret = self.compare_speedvalue(value)
        if ret == 0:
            return True
        else:
            return False
#    def compare_ratevalue(self, value):
#        ret = 0
#        fan_list = []
#        speed_list = []
#        for line in value.split("\r\n"):
#            if -1 != line.find("Fan"):
#                fan_list = line.split(" ")
#                for i in range(len(fan_list)):
#                    if -1 != fan_list[i].find("RPM"):
#                        speed_list.append(fan_list[i - 1])
#                        break
#        for i in range(len(speed_list)):
#            if i != 3 and i != 0:
#                if i < 6:
#                    if int(speed_list[i]) < int(self.ps_fan_min) or int(speed_list[i]) > int(self.ps_fan_max):
#                        _LOGGER.info("Check ps fan speed fail,output:%s,set: %s-%s." % (speed_list[i], self.ps_fan_min, self.ps_fan_max))
#                        ret = 1
#                else:
#                    if int(speed_list[i]) < int(self.sys_fan_min) or int(speed_list[i]) > int(self.sys_fan_max):
#                        _LOGGER.info("Check system fan speed fail,output:%s,set: %s-%s." % (speed_list[i], self.sys_fan_min, self.sys_fan_max))
#                        ret = 1
#        if ret == 0:
#            _LOGGER.info("Check all fan speed pass.")
#
#        return ret         
    def compare_speedvalue(self, value):
        ret = 0
        fan_list = []
        fan_speed_list = []
        system_speed_list = []
        for line in value.split("\r\n"):
            if -1 != line.find("Fan"):
                if -1 != line.find("System"):
                    fan_list = line.split(" ")
                    for i in range(len(fan_list)):
                        if -1 != fan_list[i].find("RPM"):
                            system_speed_list.append(fan_list[i - 1])
                            break
                else:
                    fan_list = line.split(" ")
                    for i in range(len(fan_list)):
                        if -1 != fan_list[i].find("RPM"):
                            fan_speed_list.append(fan_list[i - 1])
                            break
        for i in range(len(fan_speed_list)):
            if int(fan_speed_list[i]) < int(self.ps_fan_min) or int(fan_speed_list[i]) > int(self.ps_fan_max):
                        _LOGGER.info("Check ps fan speed fail,output:%s,set: %s-%s." % (fan_speed_list[i], self.ps_fan_min, self.ps_fan_max))
                        ret = 1
        for i in range(len(system_speed_list)):
            if int(system_speed_list[i]) < int(self.sys_fan_min) or int(system_speed_list[i]) > int(self.sys_fan_max):
                        _LOGGER.info("Check system fan speed fail,output:%s,set: %s-%s." % (system_speed_list[i], self.sys_fan_min, self.sys_fan_max))
                        ret = 1
        if ret == 0:
            _LOGGER.info("Check all fan speed pass.")

        return ret         

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True
