#! /usr/bin/python

from pycat import log, testcase, status
from pycat import xmlinter

#--------------------------------------------------------------------------
# PHY Test Item
#--------------------------------------------------------------------------

#pt = PhyTable()
#
#pt["1"]["3G"]
#table = PhyTable()
#table.set_attribute("1", "3G", "-")
#table.set_attribute("1", "6G", "-")
#table.set_attribute("1", "12G", "*")
#table.set_attribute("2", "3G", "-")
#table.set_attribute("2", "6G", "-")
#table.set_attribute("2", "12G", "-")
#print table
#print table["1"]["12G"]

class PhyTable(dict):
    def __init__(self):
        dict.__init__(self)

    def show(self):
        pass

    def set_attribute(self, phy, attribute, value):
        if not (phy in self.keys()):
            self[phy] = {}
        self[phy][attribute] = value

    def accord_with(self, table):
        pass

    def equal_to(self, table):
        pass

def xml_to_phy_table():
    pass

def rawdata_to_phy_table():
    pass


def analyse_phy_status_node(case, source_node, tag):
    """
    Analyse phy-status node define in XML.
    """
    new_node = etree.Element(tag)
    # Get ref node
    ref = source_node.get("ref")
    ref_node = etree.Element(tag)
    if ref != None:
        ref_node_tmp = case.find(".//%s[@name='%s']" % (tag, ref))
        if ref_node_tmp != None:
            ref_node = analyse_phy_status_node(case, ref_node_tmp, tag)

    # Set attribute
    xmlinter.combine_attribute(new_node, source_node, ref_node, "name")
    xmlinter.combine_attribute(new_node, source_node, ref_node, "proxy", "uart")
    xmlinter.combine_attribute(new_node, source_node, ref_node, "timeout", "2")

    # Combine sub-node
    xmlinter.combine_unique_node(new_node, source_node, ref_node, "uart")
    xmlinter.combine_unique_node(new_node, source_node, ref_node, "phy-table")

class PhyStatusItem(testcase.TestItem):
    item_type = "phy-status"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None

    def action_init(self, kwargs):
        testcasexml = kwargs.get("testcase")
        node = self.parameter.find(self.item_type)
        node_combined = analyse_phy_status_node(testcasexml, node, self.item_type)
        


    def action_run(self, kwargs):
        pass

    def action_clear(self, kwargs):
        pass
