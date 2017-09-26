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

"""
Author Eva lin
date July 3
The xml formate is
<?xml version="1.0" encoding="UTF-8"?>
<testcase plugin="pmcses" type="pmcses" schema="command.xsd">
   <resource>
    <check-phy name="phy-status" proxy="uart" timeout="2">
      <uart port="/dev/ttyUSB0" baudrate="115200" timeout="0.1"/>
       <cmd value="status sas_phy" timeout="1" recv="4096"/>
       <phy-table number="35">
        <phy id="0-3,8,32-35">
          <attribute name="Phy Ready" status="*"/>
          <attribute name="Rate=3G" status="*"/>
          <attribute name="Rate=6G" status="*"/>
          <attribute name="Rate=12G" status="-"/>
          <attribute name="I-Phy Reset" status="!"/>
        </phy>
        <phy id="4-5,9-10,15,17-20">
          <attribute name="Phy Ready" status="-"/>
          <attribute name="Rate=3G" status="-"/>
          <attribute name="Rate=6G" status="-"/>
          <attribute name="Rate=12G" status="-"/>
          <attribute name="I-Phy Reset" status="!"/>
        </phy>
      </phy-table>
    </check-phy>
  </resource>
  <loop-process loop="1" quit="never">
    <item type="check-phy">
      <desc>Check PHY Status</desc>
      <check-phy ref="phy-status"/>
   </item>
  </loop-process>
</testcase>

"""
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
            ref_node = analyse_powercycle_node(case, ref_node_tmp, tag)
            new_node = copy.deepcopy(ref_node)
    else:
        new_node = copy.deepcopy(source_node)
    return new_node

class SESComphycheckItem2(testcase.TestItem):

    item_type = "check-phy"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.dicterror = {}
        self.rawerror = {}
        self.dicton = {}
        self.rawon = {}
        self.dictoff = {}
        self.rawoff = {}
        self.phynum = 0
        self.cmd = None
        

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combine = analyse_powercycle_node(testcasexml, node, self.item_type)
        #node_combined = analyse_ses_command_node(testcasexml, node, self.item_type)
        # Set command
        phytree = node_combine.find("phy-table")
        self.phynum =int(phytree.get("number"))
       # dicton = {}
       # dictoff = {}
       # dicterror = {}
        for optphy in phytree.findall("phy"):
            print self.dicton
            print self.dictoff
            print self.dicterror
            phystr = ""   
            phylist = []   
            phy_id = optphy.get("id")
            phy_id = phy_id.split(",")
            for phy in phy_id:
                if -1 != phy.find("-"):
                    phy = phy.split("-")
                    for i in range(int(phy[0]),int(phy[1])+1):
                       #phystr += str(i) + " "
                       phylist.append(str(i))
                else:
                  # phystr += phy
                   phylist.append(phy)
            phystr =" ".join(phylist)
            attrnode = optphy.findall("attribute")
            for node in attrnode: 
                attri = node.get("name")
                print attri
                status = node.get("status")
                print status
               
                if status == "*":
                    if attri in self.dicton.keys():
                        print "********key exist,extend list*******" 
                        #self.dicton[attri].extend(phylist)
                        print "phystr%s" % phystr
                        self.dicton[attri]= str(self.dicton[attri]) +" "+ str(phystr)
                        list(self.dicton[attri]).sort()  
                        print self.dicton
                        print self.dictoff
                        print self.dicterror
                    else:
                        dictitem = {attri : str(phystr)}
                        print dictitem
                        self.dicton.update(dictitem)
       
                elif status == "-":
                    if attri in self.dictoff.keys():
                        
                        print "-----------key exist,extend list-------"
                        self.dictoff[attri]= self.dictoff[attri] + " " +str(phystr)
                        list(self.dictoff[attri]).sort()
                   
                       # self.dictoff[attri].sort()
                        print self.dictoff
                        print self.dicton
                        print self.dicterror
                    else:
                        dictitem = {attri : str(phystr)}
                        print dictitem
                        self.dictoff.update(dictitem) 
                else:
                    if attri in self.dicterror.keys():
                        print "!!!!!!!!!key exist,extend list!!!!!!!!!"
                       # self.dicterror[attri].extend(phylist)
                        self.dicterror[attri]= self.dicterror[attri] + " "+str(phystr)
                        list(self.dicterror[attri]).sort()
                       
                        #print self.dicterror
                   
                    else:
                        dictitem = {attri : str(phystr)}
                        print dictitem
                        self.dicterror.update(dictitem)
              

        print "xml* dict !!!"
        print self.dicton
        print "xml- dict !!!"
        print self.dictoff
        print "xml! dict !!!"
        print self.dicterror
      
    # set command 
        cmd = node_combine.find("cmd").get("value")
        cmd_timeout = node_combine.find("cmd").get("timeout")
        cmd_recv = node_combine.find("cmd").get("recv")

        proxy = node_combine.get("proxy")
        if proxy == "uart":
            uart_node = node_combine.find("uart")
            uart_port = uart_node.get("port")
            uart_baudrate = uart_node.get("baudrate")
            uart_timeout = uart_node.get("timeout")
            uart_end_of_line = uart_node.get("end-of-line")
            endmarks = []
            for endmark_node in node_combine.findall("end-mark"):
                endmark = endmark_node.get("keyword")
                endmarks.append(endmark)
            error_filters = []
            for error_filter_node in node_combine.findall("error-filter"):
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

    def phyinfo_parse(self,rawvalue):
   
        valueline = rawvalue.split("\n")
        phydict = {}
        for line in valueline:
        #print line
            if -1 != line.find("-") or -1 != line.find("*") or -1 != line.find("!"):
                phystatus = []
                phyitem = []
                for word in line.split(" "):
                    if word != "*" and word != "-" and word != "!":
                   # print "itemword %s" %(word)
                        phyitem.append(word)
                    else:
                   # print "statusword %s" %(word)
                        phystatus.append(word)
           # print phyitem
                phyitemstr = " ".join(phyitem)
           # print "joinitem %s" %(phyitemstr)
             
                phyitemstr = phyitemstr.strip()
                liston = []
                listoff = []
                listerror = []
                for i in range(0,len(phystatus)):
                    if phystatus[i] == "*":
                        liston.append(i)
                    elif phystatus[i] == "-":
                        listoff.append(i)
                    elif phystatus[i] == "!":
                        listerror.append(i) 
                liston.sort()
                listoff.sort()
                listerror.sort()
               # if len(liston) > 0:
                rawonitem = { phyitemstr:liston }
                self.rawon.update(rawonitem)
               #if len(listoff) > 0:
                rawoffitem = { phyitemstr:listoff }
                self.rawoff.update(rawoffitem)
               # if len(listerror)> 0:
                rawerroritem = { phyitemstr:listerror }
                self.rawerror.update(rawerroritem)

        print "raw* dict!!!"
        print self.rawon
        print "raw- dict!!!"
        print self.rawoff
        print "raw! dict!!!"
        print self.rawerror          
            
          
   
    def compare_phyinfo(self):
        flag = 0
        for key in self.dicton.keys():
            onlist = []
            offlist = []
            errorlist = []
            print key
            if key in self.rawon:
                print "key %s  in raw value" % key
                tmplist=self.dicton[key].split(" ")
                print tmplist
                print self.rawon[key]
                for phyid in tmplist:
                    phyid = int(phyid)
                    if phyid not in self.rawon[key]:
                        onlist.append(phyid)
                        
                    else:
                          pass
               
               
            else:
                print "key %s not in raw value" % key
                for i in range(0,self.phynum+1):
                    onlist.append(i)
                _LOGGER.info("The attribute name %s spell wrong, the name should be the same with the raw value !!" % key)
            if len(onlist) > 0:
                flag = 1
                print "report error"
                onstr = str(onlist)
                _LOGGER.info("Check %s failed,error=%s" %(key,onstr))
                onlist = []
            else:
                print "Check %s success" % key
        for key in self.dictoff.keys():
            if key in self.rawoff:
                print "key %s  in raw value" % key
                print "xml dict"
                
                tmplist = self.dictoff[key].split(" ")
                print tmplist
                print "raw dict"
                print self.rawoff[key]
                for phyid in tmplist:
                    phyid = int(phyid)
                  
                    if phyid not in self.rawoff[key]:
                        print "phy %s not in raw value" % phyid          
                        offlist.append(int(phyid))
                       
                    else:
                        pass
               
               
            else:
                print "key %s not in raw value"
                _LOGGER.info("The attribute name %s spell wrong,the name should the same with the raw value!!" % key)
                for i in range(0,self.phynum+1):
                    offlist.append(i) 
            if len(offlist) > 0:
                flag = 1
                print "report error"
                print offlist
                offstr= str(offlist)
                _LOGGER.info("Check %s failed,error = %s" %(key,offstr))
                offlist = []
            else:
                print "Check %s success!" % key    

        for key in self.dicterror.keys():
             if key in self.rawerror:
                 print "key %s  in the raw value" % key
                 print "xml dict"
                 tmplist = self.dicterror[key].split(" ")
                 print tmplist
                 print "raw dict"
                 print self.rawerror[key]
                 for phyid in tmplist:
                     phyid = int (phyid)
                     if phyid not in self.rawerror[key]:
                         print "phy %s not in the raw value" % phyid
                         errorlist.append(int(phyid))
                        
                     else:
                         pass                
                             
             else:
                 print "key %s not  in the raw value" % key
                 for i in range(0,self.phynum+1):
                     errorlist.append(i)
                 _LOGGER.info("The attribute name %s spell wrong,the name should be the same with the raw value!!" % key)
             if len(errorlist) > 0 :
                flag = 1
                print "report error"
                print errorlist
                errorstr = str(errorlist)
                _LOGGER.info("Check %s failed.error = %s" %(key,errorstr))
                errorlist = []
             else:
                print "Check %s success!" % key
        if flag == 0:
            _LOGGER.info("Check phy status success!")
            return 0
        else:
            _LOGGER.info("Check phy status failed!")
            return 1
   

                  

    def action_run(self, kwargs):
        """
        Execute the command.
        """
       # try:
           # value = self.cmd.apply()
       # except ValueError:
        #    return False
        value = "=== SAS PHY Layer ===\n\
                    0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35\n\
SAS Attached        -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
SATA Attached       -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
Device Present      -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
PhyRst At Max       -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
Rate=1.5G           -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
Rate=3G             *  *  *  *  *  *  -  -  *  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  *  *  *  *\n\
Rate=6G             *  *  *  *  -  -  -  -  *  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  *  *  *  *\n\
Rate=12G            -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
SAS2 Enabled        -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
Phy Ready           *  *  *  *  *  *  -  -  *  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  *  *  *  *\n\
I-Phy Ready         -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-Spinup Hold Conf  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-Disparity Error   -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-Code Viol Err     -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-Phy Reset         !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !\n\
I-Dword Synch Ls    -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-Cominit           -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-Comwake           -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-Comsas            -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
CtrlCharPosErr*     -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
Primitive error*    -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-PhyReset Failed*  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-Hotplug Timeout*  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !  !\n\
SAS2 SSC            -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
SAS2 CenterSSC      -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-Unsolicit Cominit -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-PS_Pres_Det       -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-PS_Switch_Det     -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n\
I-PHY Reset Failed  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -"


        self.phyinfo_parse(value)
        print "start compare!"
        ret = self.compare_phyinfo()
        if ret == 0:
	    return True 
        else:
            return False

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True





