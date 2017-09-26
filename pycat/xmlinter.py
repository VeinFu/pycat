#! /usr/bin/python

from lxml import etree

#--------------------------------------------------------------------------
#    Command Test Items
#--------------------------------------------------------------------------

def combine_attribute(new_node, src_node, ref_node, attr, default=None):
    """
    Combine attribute in items.

    If find attribute in src_node, copy it into new_node.
    Otherwise search attribite in ref_node. If find attribute, copy it into new_node.
    If can't find attribute in src_node or ref_node, use the default value.
    """
    attr_value = src_node.get(attr)
    if attr_value == None and ref_node != None:
        attr_value = ref_node.get(attr)
    if attr_value != None :
        new_node.set(attr, attr_value)
    elif default != None:
        new_node.set(attr, default)

def combine_unique_node(new_node, src_node, ref_node, tag):
    """
    Combine unique node in itmes.

    If find tag in src_node, copy it into new_node.
    Otherwise search tag in ref_node. If find tag in ref_node, cope it into
    new_node.
    If tag isn't in src_node or ref_node, return False.
    """
    subnode = src_node.find(tag)
    if subnode != None:
        subnode_tmp = copy.deepcopy(subnode)
        new_node.append(subnode_tmp)
    elif ref_node != None:
        subnode = ref_node.find(tag)
        if subnode != None:
            subnode_tmp = copy.deepcopy(subnode)
            new_node.append(subnode_tmp)
        else:
            return False
    return True

def combine_sequence_node(new_node, src_node, ref_node, tag, attrs):
    """
    Combine sequence nodes in items.

    Copy ref_node to new_node.
    If a subnode in src_node isn't named, copy it into new_node.
    If a subnode in src_node is named and never appeared in new_node, copy
    it into new_node.
    If a subnode in src_node is named and appeared in new_node, only replace
    its attributes.
    """
    assert src_node != None
    assert tag != None
    assert attrs != None
    if ref_node != None:
        # Copy subnodes in ref node.
        for subnode in ref_node.findall(tag):
            subnode_tmp = copy.deepcopy(subnode)
            new_node.append(subnode_tmp)

    # Combine new_node and ref_node.
    for subnode in src_node.findall(tag):
        subname = subnode.get("name")
        if subname == None:
            # Unnamed node, append it.
            subnode_tmp = copy.deepcopy(subnode)
            new_node.append(subnode_tmp)
        else:
            subnode_exist = new_node.find("./%s[@name='%s']" % (tag, subname))
            if subnode_exist == None:
                # Named node, but never appeared.
                subnode_tmp = copy.deepcopy(subnode)
                new_node.append(subnode_tmp)
            else:
                # Named node and existed, replace attributes only.
                for attr in attrs:
                    attr_value = subnode.get(attr)
                    if attr_value != None:
                        subnode_exist.set(attr, attr_value)

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




