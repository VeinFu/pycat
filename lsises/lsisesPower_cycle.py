#!/usr/bin/python

"""
@todo by Grace, to Chuanjian, too many useless import modules.
SES Command Test Items For POWER_CYCLE.
"""

from lxml import etree
import os
import time
import copy
from serial import Serial
import lsises

from pycat import log, testcase, status
from basicplugin import command

_LOGGER = log.getLogger("log.tc")

def analyse_powercycle_node(case, source_node, tag):
    """
    @todo by Grace, to Chuanjian, The function name *_fw_* is inappropriate for power cycle testing.
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

def detect_ses_dev(product_id):
    cmd = "ls /dev/sg*"
    cmd_detect = command.CommandLocalViaSystem(cmd)
    cmd_sg = "sg_inq"
    try:
        value = cmd_detect.apply()
    except OSError:
        return False
    unitdev_list = []
    value = value.strip()
    list_item = value.split("\n")
    for item in list_item:
        item_tmp = item.strip()
        item = item_tmp[7:]
        cmd = cmd_sg + " " + "/dev/sg" + item
        cmd_det = command.CommandLocalViaSystem(cmd)
        value = cmd_det.apply()
        if -1 != value.find(product_id):
            unit = item
            unit = str(unit)
            unitdev_list.append(unit)
    return unitdev_list

def match_ses_dev(dev_list, sg_id):
    cmd = "sg_ses --page=0x01 /dev/sg"
    flag = 0
    for i in dev_list:
        cmd_match = command.CommandLocalViaSystem(cmd + str(i))
        value = cmd_match.apply()
        if -1 != value.find("relative ES process id:"):
            num = value.find("relative ES process id:") + len("relative ES process id:") + 1
            dev_id = value[num:num+1]
            if dev_id == sg_id:
                flag = 1
                break
    if flag == 1:
        return i
    else:
        _LOGGER.info("Don't find the match sg id")
        raise ValueError("Don't find the match sg id %s" % sg_id)

class SESComphycheckItem(testcase.TestItem):
    """
    @todo by Grace, to Chuanjian, 1. the naming of the variable should be meaningful. 2. The python internal name shouldn't be used as variable name, such as "list" "dict". 3. "ErrorFilters" should has runtime error
    A SESCommandItem instance executes SES commands. 
    """
    item_type = "check_phy"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None
        self.list_xmlphyd = []
        self.sg_id = None
        self.product_id = None

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node = analyse_powercycle_node(testcasexml, node, self.item_type)
        #node_combined = analyse_ses_command_node(testcasexml, node, self.item_type)
        # Set command
        phymaptree = node.find("phy_map")
        for optphy in phymaptree.findall("phy"):
            phyid_list = []
            list_phyresult = []
            va = optphy.get("PHY_ID")
            phyid_list = va.split(",")
            for i in phyid_list:
                if -1 != i.find("-"):
                    subphyid_list = i.split("-")
                    subphyidrange_list = range(int(subphyid_list[0]), int(subphyid_listl[1]) + 1)
                    for j in subphyidrange_list:
                        list_phyresult.append(str(j))
                else:
                    list_phyresult.append(str(i))
            phy_dict = {}
            flag = 0
            for i in list_phyresult:
                item = {"PHY_ID": i}
                phy_dict.update(item)
                if flag == 0:
                    for opt in optphy.findall("phy_info"):
                        name = opt.get("name")
                        value = opt.get("value")
                        item_info = {name: value}
                        phy_dict.update(item_info)
                    flag = 1
                self.list_xmlphyd.append(phy_dict)
        
        self.sg_id = node.find("sg-id").get("value")
        self.product_id = node.find("product_id").get("name")
        cmd_timeout = "1"
        cmd_recv = "4096"
#        dev_list = detect_ses_dev(self.product_id)
#        dev_id = match_ses_dev(dev_list, self.sg_id)
#	dev_id = str(dev_id)
#        cmd_phy = "cls_cli_tool -d /dev/sg" + dev_id + " -c phyinfo"
#        self.cmd = command.CommandLocalViaSystem(cmd_phy) 


        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        dev_list = detect_ses_dev(self.product_id)
        dev_id = match_ses_dev(dev_list, self.sg_id)
        dev_id = str(dev_id)
        cmd_phy = "cls_cli_tool -d /dev/sg" + dev_id + " -c phyinfo"
        self.cmd = command.CommandLocalViaSystem(cmd_phy) 

        try:
            value = self.cmd.apply()
            time.sleep(3)
        except ValueError:
            return False
        iovalue = self.parse_pyhinfo(value)
        ret = self.compare_value(self.list_xmlphyd, iovalue)
        if ret:
            return True
        else:
            return False
            
    def parse_pyhinfo(self, value):
        """
        @todo by Grace, to Chuanjian, 1. the naming of the variable should be meaningful. 2. The python internal name shouldn't be used as variable name, such as "list" "dict" "tuple". 3. How about if the PHY_ID is "006"? 4.There're more or less than 14 items, if the command "option" is different. So should not fix the item_number is 14 and the item_title.
        """
        item_title = ["PHY_ID", "DEV_TYPE", "NLR", "PHY_CNG_CNT", "SSSSSSS_STMSTMA_PPPPPPT_IIITTTA", "ATTACHED_SAS_ADDR", "ROUTE_TYPE", "ZONE_GRP", "ZONE_CTRL_BUS", "CONN_TYPE", "CONN_ELEM_INDX", "CONN_PHY_LINK", "MAP_PHY_ID", "E_E_DFR_FCR_BSL"]
        phyinfo_list = value.split("\r\n")
        list_phyinfoline = []
        for i in phyinfo_list:
            if -1 != i.find("-"):
                list_phyinfoline.append(i)
        list_allphyarb_result = []
        for i in list_phyinfoline:
            count = 0
            list_everyphyarb_value = []
            phyopt_tuple = i.partition(" ")
            count += 1
            if phyopt_tuple[0][0] == "0":
                list_everyphyarb_value.append(phyopt_tuple[0][1])
            else:
                list_everyphyarb_value.append(phyopt_tuple[0])
            while (count < 14): 
                tuple_n = phyopt_tuple[2].lstrip()
                phyopt_tuple = tuple_n.partition(" ")
                count += 1
                if count == 2:
                    if phyopt_tuple[0] == "END":
                        list_everyphyarb_value.append("END")
                    elif phyopt_tuple[0] == "EXP":
                        list_everyphyarb_value.append("EXP")
                    else:
                        list_everyphyarb_value.append("")
                        count += 1
                        list_everyphyarb_value.append(phyopt_tuple[0])
                elif count == 6:
                    if len(phyopt_tuple[0]) == 1:
                        list_everyphyarb_value.append("")
                        list_everyphyarb_value.append(phyopt_tuple[0])
                        count += 1
                    else:
                        list_everyphyarb_value.append(phyopt_tuple[0])
                else:
                    list_everyphyarb_value.append(phyopt_tuple[0])
    	    list_allphyarb_result.append(list_everyphyarb_value)	
        list_allphyarb_dict = []
        phy_dict = {}
        for i in list_allphyarb_result:
            phy_dict ={}
            for j in range(14):
                item = {item_title[j]: i[j]}
                phy_dict.update(item)
            list_allphyarb_dict.append(phy_dict)	
        return list_allphyarb_dict

    def compare_value(self, xmlvalue, iovalue):
        """
        @todo by Grace, to Chuanjian, 1. Use "break" in for loop can improve efficiency.
        """
        flag_allphy = 0
        for i in xmlvalue:
            list_xmlphykey = i.keys()
            ret = 0
            flag_phy = 0
            for j in iovalue:
                if i["PHY_ID"] == j["PHY_ID"]:
                    for k in list_xmlphykey:
                        if i[k] != j[k]:
                            _LOGGER.info("Check %s fail,xmlvalue:%s,iovalue:%s" % (k, i[k], j[k]))
                   #         _LOGGER.info("Check PHY_ID:%s fail" % (i["PHY_ID"]))
                   #         _LOGGER.info("Expander Id:%s" % self.sg_id)
                            flag_phy = 1
                            flag_allphy = 1
                   #         return 1
                    if flag_phy != 1:
                        _LOGGER.info("Check PHY_ID:%s all pass" % (i["PHY_ID"]))
                    else:
                        _LOGGER.info("Check PHY_ID:%s fail" % (i["PHY_ID"]))
                    ret = 1
                    break
            if ret != 1:
                _LOGGER.info("Unknown PHY_ID")
                return False
        if flag_allphy != 1:
            _LOGGER.info("Check phy status pass,Expander id:%s" % self.sg_id)
            return True
        else:
            _LOGGER.info("Check phy status fail,Expander id:%s" % self.sg_id)
            return False

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
 #       self.cmd.show()
        return True
    
