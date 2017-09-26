#! /usr/bin/python

"""
Testcase modue for pycat.
"""

from lxml import etree
import time
import re
import os
import datetime

from pycat import config
from pycat import log
from pycat import status

_LOGGER = log.getLogger("log.tc")

#--------------------------------------------------------------------------
#    Duration Data Type
#--------------------------------------------------------------------------
class DurationData(object):
    """
    The duration data type is used to specify a time interval.
    
    The time interval is specified in the following form "PnYnMnDTnHnMnS" where:
    
    P indicates the period (required)
    nY indicates the number of years
    nM indicates the number of months
    nD indicates the number of days
    T indicates the start of a time section (required if you are going to specify hours, minutes, or seconds)
    nH indicates the number of hours
    nM indicates the number of minutes
    nS indicates the number of seconds
    """
    def __init__(self, data):
        assert isinstance(data, str)
        self.data = {"year": 0,
                     "month": 0,
                     "day": 0,
                     "hour": 0,
                     "minute": 0,
                     "second": 0}
        date_map = {"Y": "year",
                    "M": "month",
                    "D": "day"}
        time_map = {"H": "hour",
                    "M": "minute",
                    "S": "second"}

        mat = re.match("P.*T", data)
        if mat is not None:
            datatmp = mat.group()
            spos = datatmp.find("P") + 1
            for key in ("Y", "M", "D"):
                epos = datatmp.find(key)
                if epos != -1:
                    val = int(datatmp[spos:epos])
                    dkey = date_map[key]
                    self.data[dkey] = val
                    spos = epos + 1

        mat = re.search("T.*", data)
        if mat is not None:
            datatmp = mat.group()
            spos = datatmp.find("T") + 1
            for key in ("H", "M","S"):
                epos = datatmp.find(key)
                if epos != -1:
                    val = int(datatmp[spos:epos])
                    dkey = time_map[key]
                    self.data[dkey] = val
                    spos = epos + 1

    def toseconds(self):
        """
        Translate duradata to seconds.
        """
        if self.data["year"] != 0 or self.data["month"] != 0:
            raise ValueError("Can not translate mouth and year to seconds.")
        seconds = self.data["second"] + self.data["minute"] * 60\
                  + self.data["hour"] * 3600 + self.data["day"] * 24 * 3600
        return seconds

    def get(self, domain):
        """
        Get value of a domain. Valid domains are 'year', 'mouth', 'day',
        'hour', 'minute', 'second'.
        """
        return self.data[domain]

#--------------------------------------------------------------------------
#    TestItem
#--------------------------------------------------------------------------
class TestItem(object):
    """
    A TestItem instance defines the actions of completing a task in test
    cases.

    A TestItem instance includes several sequence and each includes several
    actions. An action is an executable object. Actions included in a
    sequence will be executed one by one when a sequence is called.
    Each action should return a boolean value, 'True' on success or 'False'
    on failure.

    To create a child of TestItem, you can replace the methods 'action_init',
    'action_run', 'action_clear', 'action_print_parameter', etc. You can 
    also set the sequences from scratch.
    """
    item_type = "item-base"
    def __init__(self, parameter=None):
        self.desc = None
        self.actions = {"block": self.action_block,
                        "print-parameter": self.action_print_parameter,
                        "init": self.action_init,
                        "run": self.action_run,
                        "clear": self.action_clear
                       }
        self.sequence = dict()
        self.sequence["precheck"] = ["init", "print-parameter"]
        self.sequence["init"] = ["init", "print-parameter"]
        self.sequence["run"] = ["run", "block"]
        self.sequence["clear"] = ["clear"]
        self.sequence["None"] = list()
        self.parameter = None
        if parameter != None:
            self.set_parameter(parameter)

    def __str__(self):
        ret = "%s(%s) " % (self.item_type, self.desc)
        ret += "%s  " % (self.actions)
        for name in self.sequence:
            sequence = self.sequence[name]
            ret += "%s%s; " % (name, sequence)
        return ret

    def _delete_action_in_sequence(self, seq_name, action):
        """
        Delete an action from a sequence.
        """
        sequence = self.sequence[seq_name]
        has_value = True
        while has_value:
            try:
                sequence.remove(action)
            except ValueError:
                has_value = False

    def delete_action(self, name):
        """
        Delete an action from the action list. If this action is used by any
        sequences, remove it from the sequences.
        """
        if name in self.actions:
            for seq_name in self.sequence:
                self._delete_action_in_sequence(seq_name, name)
            del self.actions[name]

    def update_action(self, name, action):
        """
        Update an action.
        """
        self.actions[name] = action

    def get_action(self, name):
        """
        Get an action.
        """
        ret = None
        if name in self.actions:
            ret = self.actions[name]
        return ret

    def update_actions(self, actions):
        """
        Update the action list.
        """
        if isinstance(actions, dict):
            self.actions.update(actions)
            return True
        else:
            return False

    def get_sequence(self, name):
        """
        Get a sequence.
        """
        sequence = None
        if name in self.sequence:
            sequence = self.sequence[name]
        return sequence

    def set_sequence(self, name, sequence):
        """
        Set a sequence.
        """
        if isinstance(name, str) and isinstance(sequence, list):
            for action in sequence:
                if action not in self.actions:
                    raise ValueError("%s isn't supported." % action)
            self.sequence[name] = sequence
            return True
        else:
            raise TypeError
            #return False

    def set_parameter(self, parameter):
        """
        Set the parameter.
        The parameter is an XML element node. The 'type' attribute must match
        the item_type.
        Example:
        <item type="item-type">
            <desc>Description</desc>
            <item-type>subnodes</item-type>
        </item>

        """
        # @todo wilson, etree._Element is a protected member. Replace it.
        if isinstance(parameter, etree._Element)\
           and parameter.get("type") == self.item_type:
            self.parameter = parameter
            self.desc = parameter.find("desc").text
        else:
            raise ValueError("'%s' testitem get a '%s' parameter." %
                             (self.item_type, self.parameter.get("type")))

    def perform_sequence(self, seq_name, kwargs):
        """
        Perform a sequence.
        """
        assert self.parameter != None
        result = False
        sequence = self.sequence["None"]
        if seq_name in self.sequence:
            sequence = self.sequence[seq_name]
            result = True
        for name in sequence:
            ret = self.actions[name](kwargs)
            if ret != True:
                result = False
        return result

    def action_block(self, kwargs):
        """
        Block several seconds.
        """
        #testcase = kwargs.get("testcase")
        block_time = self.parameter.find("block")
        if block_time != None:
            duration = DurationData(block_time.text)
            seconds = duration.toseconds()
            _LOGGER.info("block %d seconds.", seconds)
            time.sleep(seconds)
        return True

    def action_print_parameter(self, kwargs):
        """
        Default callback function for printing parameter. Children of TestItem
        should replace this function.
        """
        raise NotImplementedError

    def action_init(self, kwargs):
        """
        Default callback function for initialization. Children of TestItem
        should replace this function.
        """
        raise NotImplementedError

    def action_run(self, kwargs):
        """
        Default callback function for executing a test item. Children of
        TestItem should replace this function.
        """
        raise NotImplementedError

    def action_clear(self, kwargs):
        """
        Default callback function for clearing parameter. Children of TestItem
        should replace this function.
        """
        raise NotImplementedError

class ItemCreator(object):
    """
    ItemCreator is a factory of TestItem.
    """
    def __init__(self, items=None):
        self.items = dict()
        if items != None:
            self.update_items(items)

    def update_items(self, items):
        """
        Update test item dict.
        """
        if isinstance(items, dict):
            self.items.update(items)
        else:
            raise TypeError

    def create_item(self, param):
        """
        Create a new test item.
        """
        item = None
        item_type = param.get("type")
        if item_type in self.items:
            item = self.items[item_type](param)
        else:
            raise ValueError("Unknown item type %s." % item_type)
        return item

#--------------------------------------------------------------------------
#    Process
#--------------------------------------------------------------------------
# @todo [optimize] Do not let process do too many things. Move log and DB 
# operations into other functions.
class Process(object):
    """
    A Process instance defines how to execute a test case. For example,
    execute it by looping or by duration time. Updating the 'log.txt' and
    'status.db' is its responsibility too.
    """
    process_type = "basic-process"
    def __init__(self):
        self.name = "BasicProcess"

    def perform_process(self, item_creator, process, **kwargs):
        """
        Execute 'init', 'run' and 'clear' sequences of the items. Children
        of Process should replace this method.
        """
        raise NotImplementedError

    def precheck(self, item_creator, process, **kwargs):
        """
        Execute 'precheck' sequence of the items.
        """
        raise NotImplementedError

class LoopProcess(Process):
    """
    A LoopProcess instance execute a test case by looping.
    """
    process_type = "loop-process"
    def __init__(self):
        Process.__init__(self)
        self.logger = _LOGGER

    def precheck(self, item_creator, process, **kwargs):
        """
        Execute 'precheck' sequences of items once.
        """
        result = True
        items = list()
        for param in process.iter(tag="item"):
            item = item_creator.create_item(param)
            items.append(item)
        dbsession = status.get_session()
        record_tc = status.Testcase(name="TestCase",
                                    process_type=self.process_type,
                                    cycle_total=process.get("loop"))
        dbsession.add(record_tc)
        dbsession.commit()
        self.logger.info("Quit type: %s", process.get("quit"))
        self.logger.info("Loop: %s", process.get("loop"))
        self.logger.setCycle("Precheck")
        self.logger.setItem("None")
        record_cycle = status.Cycle(name="precheck",
                                    item_total=len(items),
                                    case_id=record_tc.id)
        dbsession.add(record_cycle)
        for item in items:
            record_item = status.Item(cycle_name="precheck",
                                      status="running",
                                      description=item.desc)
            dbsession.add(record_item)
            self.logger.setItem(item.desc)
            self.logger.info("---------- %s ----------", item.desc)
            ret = item.perform_sequence("precheck", kwargs)
            if ret == True:
                self.logger.info("Precheck %s, succeed.", item.desc)
                record_item.status = "succeed"
                dbsession.add(record_item)
                dbsession.commit()
            else:
                self.logger.error("Precheck %s, fail.", item.desc)
                record_item.status = "fail"
                dbsession.add(record_item)
                dbsession.commit()
                result = False
        record_tc.end_time = datetime.datetime.utcnow()
        dbsession.add(record_tc)
        dbsession.commit()
        return result

    def perform_process(self, item_creator, process, **kwargs):
        """
        Execute 'init', 'run' and 'clear' sequences by looping.
        """
        items = list()
        for param in process.iter(tag="item"):
            item = item_creator.create_item(param)
            items.append(item)
        quit_type = process.get("quit")
        loopnum = int(process.get("loop"))
        dbsession = status.get_session()
        record_tc = status.Testcase(name="TestCase",
                                    process_type=self.process_type,
                                    cycle_total=(loopnum + 2))
        dbsession.add(record_tc)
        dbsession.commit()

        self.logger.setCycle("Init")
        self.logger.setItem("None")
        self.logger.info("========== Init ==========")
        record_cycle = status.Cycle(name="Init",
                                    item_total=len(items),
                                    case_id=record_tc.id)
        dbsession.add(record_cycle)
        for item in items:
            record_item = status.Item(cycle_name="Init",
                                      status="running",
                                      description=item.desc)
            dbsession.add(record_item)
            self.logger.setItem(item.desc)
            self.logger.info("---------- %s ----------", item.desc)
            ret = item.perform_sequence("init", kwargs)
            if ret == True:
                self.logger.info("Init %s, succeed.", item.desc)
                record_item.status = "succeed"
                dbsession.add(record_item)
                dbsession.commit()
            else:
                self.logger.error("Init %s, fail.", item.desc)
                record_item.status = "fail"
                dbsession.add(record_item)
                dbsession.commit()
                if quit_type == "fail":
                    record_tc.end_time = str(datetime.datetime.utcnow())
                    dbsession.add(record_tc)
                    dbsession.commit()
                    return False

        loopcount = 1
        while loopcount <= loopnum:
            record_cycle = status.Cycle(name=str(loopcount),
                                        item_total=len(items),
                                        case_id=record_tc.id)
            dbsession.add(record_cycle)
            self.logger.setItem("Cycle")
            self.logger.setCycle("Cycle-%d" % loopcount)
            self.logger.info("========== Cycle-%d ==========", loopcount)
            for item in items:
                record_item = status.Item(cycle_name=str(loopcount),
                                          status="running",
                                          description=item.desc)
                dbsession.add(record_item)
                self.logger.setItem(item.desc)
                self.logger.info("---------- %s ----------", item.desc)
                ret = item.perform_sequence("run", kwargs)
                if ret == True:
                    record_item.status = "succeed"
                    dbsession.add(record_item)
                    dbsession.commit()
                    self.logger.info("Run %s, succeed.", item.desc)
                else:
                    record_item.status = "fail"
                    dbsession.add(record_item)
                    dbsession.commit()
                    self.logger.error("Run %s, fail.", item.desc)
                    if quit_type == "fail":
                        record_tc.end_time = datetime.datetime.utcnow()
                        dbsession.add(record_tc)
                        dbsession.commit()
                        return False
            loopcount += 1
        self.logger.setItem("None")

        record_cycle = status.Cycle(name="Clear",
                                    item_total=len(items),
                                    case_id=record_tc.id)
        dbsession.add(record_cycle)
        self.logger.setCycle("Clear")
        self.logger.info("========== Clear ==========")
        for item in items:
            record_item = status.Item(cycle_name="Clear",
                                      status="running",
                                      description=item.desc)
            dbsession.add(record_item)
            self.logger.setItem(item.desc)
            self.logger.info("---------- %s ----------", item.desc)
            ret = item.perform_sequence("clear", kwargs)
            if ret == True:
                record_item.status = "succeed"
                dbsession.add(record_item)
                dbsession.commit()
                self.logger.info("Clear %s, succeed.", item.desc)
            else:
                record_item.status = "fail"
                dbsession.add(record_item)
                dbsession.commit()
                self.logger.error("Clear %s, fail.", item.desc)
                if quit_type == "fail":
                    record_tc.end_time = datetime.datetime.utcnow()
                    dbsession.add(record_tc)
                    dbsession.commit()
                    return False
        record_tc.end_time = datetime.datetime.utcnow()
        dbsession.add(record_tc)
        dbsession.commit()
        return True

class DurationProcess(Process):
    """
    A DurationProcess instance executes a test case by duration time.
    """
    process_type = "duration-process"
    def __init__(self):
        Process.__init__(self)
        self.logger = _LOGGER

    def precheck(self, item_creator, process, **kwargs):
        """
        Execute 'precheck' sequences of items once.
        """
        result = True
        items = list()
        for param in process.iter(tag="item"):
            item = item_creator.create_item(param)
            items.append(item)
        dbsession = status.get_session()
        record_tc = status.Testcase(name="TestCase",
                                    process_type=self.process_type,
                                    cycle_total="00")
        dbsession.add(record_tc)
        dbsession.commit()
        self.logger.info("Quit type: %s", process.get("quit"))
        self.logger.info("Duration Time: %s", process.get("duration"))
        self.logger.setCycle("Precheck")
        self.logger.setItem("None")
        record_cycle = status.Cycle(name="precheck",
                                    item_total=len(items),
                                    case_id=record_tc.id)
        dbsession.add(record_cycle)
        for item in items:
            record_item = status.Item(cycle_name="precheck",
                                      status="running",
                                      description=item.desc)
            dbsession.add(record_item)
            self.logger.setItem(item.desc)
            self.logger.info("---------- %s ----------", item.desc)
            ret = item.perform_sequence("precheck", kwargs)
            if ret == True:
                self.logger.info("Precheck %s, succeed.", item.desc)
                record_item.status = "succeed"
                dbsession.add(record_item)
                dbsession.commit()
            else:
                self.logger.error("Precheck %s, fail.", item.desc)
                record_item.status = "fail"
                dbsession.add(record_item)
                dbsession.commit()
                result = False
        record_tc.end_time = datetime.datetime.utcnow()
        dbsession.add(record_tc)
        dbsession.commit()
        return result

    def perform_process(self, item_creator, process, **kwargs):
        """
        Execute 'init', 'run' and 'clear' sequences by duration time.
        """
        items = list()
        for param in process.iter(tag="item"):
            item = item_creator.create_item(param)
            items.append(item)
        quit_type = process.get("quit")
        duration = DurationData(process.get("duration")).toseconds()
        dbsession = status.get_session()
        record_tc = status.Testcase(name="TestCase",
                                    process_type=self.process_type,
                                    cycle_total=0)
        dbsession.add(record_tc)
        dbsession.commit()

        self.logger.setCycle("Init")
        self.logger.setItem("None")
        self.logger.info("========== Init ==========")
        record_cycle = status.Cycle(name="Init",
                                    item_total=len(items),
                                    case_id=record_tc.id)
        dbsession.add(record_cycle)
        for item in items:
            record_item = status.Item(cycle_name="Init",
                                      status="running",
                                      description=item.desc)
            dbsession.add(record_item)
            self.logger.setItem(item.desc)
            self.logger.info("---------- %s ----------", item.desc)
            ret = item.perform_sequence("init", kwargs)
            if ret == True:
                self.logger.info("Init %s, succeed.", item.desc)
                record_item.status = "succeed"
                dbsession.add(record_item)
                dbsession.commit()
            else:
                self.logger.error("Init %s, fail.", item.desc)
                record_item.status = "fail"
                dbsession.add(record_item)
                dbsession.commit()
                if quit_type == "fail":
                    record_tc.end_time = str(datetime.datetime.utcnow())
                    dbsession.add(record_tc)
                    dbsession.commit()
                    return False

        loopcount = 1
        start_time = datetime.datetime.now()
        end_time = datetime.datetime.now()
        while (end_time - start_time).seconds < duration:
            record_cycle = status.Cycle(name=str(loopcount),
                                        item_total=len(items),
                                        case_id=record_tc.id)
            dbsession.add(record_cycle)
            dbsession.commit()
            self.logger.setItem("Cycle")
            self.logger.setCycle("Cycle-%d" % loopcount)
            self.logger.info("========== Cycle-%d ==========", loopcount)
            for item in items:
                record_item = status.Item(cycle_name=str(loopcount),
                                          status="running",
                                          description=item.desc)
                dbsession.add(record_item)
                dbsession.commit()
                self.logger.setItem(item.desc)
                self.logger.info("---------- %s ----------", item.desc)
                ret = item.perform_sequence("run", kwargs)
                if ret == True:
                    record_item.status = "succeed"
                    dbsession.add(record_item)
                    dbsession.commit()
                    self.logger.info("Run %s, succeed.", item.desc)
                else:
                    record_item.status = "fail"
                    dbsession.add(record_item)
                    dbsession.commit()
                    self.logger.error("Run %s, fail.", item.desc)
                    if quit_type == "fail":
                        record_tc.end_time = datetime.datetime.utcnow()
                        dbsession.add(record_tc)
                        dbsession.commit()
                        return False
            end_time = datetime.datetime.now()
            loopcount += 1
        self.logger.setItem("None")

        record_cycle = status.Cycle(name="Clear",
                                    item_total=len(items),
                                    case_id=record_tc.id)
        dbsession.add(record_cycle)
        self.logger.setCycle("Clear")
        self.logger.info("========== Clear ==========")
        for item in items:
            record_item = status.Item(cycle_name="Clear",
                                      status="running",
                                      description=item.desc)
            dbsession.add(record_item)
            self.logger.setItem(item.desc)
            self.logger.info("---------- %s ----------", item.desc)
            ret = item.perform_sequence("clear", kwargs)
            if ret == True:
                record_item.status = "succeed"
                dbsession.add(record_item)
                dbsession.commit()
                self.logger.info("Clear %s, succeed.", item.desc)
            else:
                record_item.status = "fail"
                dbsession.add(record_item)
                dbsession.commit()
                self.logger.error("Clear %s, fail.", item.desc)
                if quit_type == "fail":
                    record_tc.end_time = datetime.datetime.utcnow()
                    dbsession.add(record_tc)
                    dbsession.commit()
                    return False
        record_tc.end_time = datetime.datetime.utcnow()
        dbsession.add(record_tc)
        dbsession.commit()
        return True

class ProcessCreator(object):
    """
    A ProcessCreator instance is a factory of Process instances.
    """
    def __init__(self):
        self.process_dict = {LoopProcess.process_type: LoopProcess,
                             DurationProcess.process_type: DurationProcess}

    def update(self, process_dict):
        """
        Update the process instances dict.
        """
        if isinstance(process_dict, dict):
            self.process_dict.update(process_dict)
        else:
            raise TypeError

    def create(self, ptype):
        """
        Create a new process instance.
        """
        process = None
        if ptype in self.process_dict:
            process = self.process_dict[ptype]()
        else:
            raise TypeError("Unknown process type '%s'" % (ptype))
        return process

    def process_types(self):
        """
        Get all process types available.
        """
        return self.process_dict.keys()

#--------------------------------------------------------------------------
#    TestCase
#--------------------------------------------------------------------------
class TestCase(object):
    """
    A TestCase class is related to a test case defined in XML files. A
    TestCase instance supplys methods to execute a test case as the XML file
    ordered.

    TestCase has two import members, process_creator and item_creator.
    TestCase create a Process instance with process_creator as XML files
    ordered. Then the Process instance create items and executes them.

    To create a child of TestCase, you need update the item_creator and
    process_creator.
    """
    def __init__(self, configfile):
        if isinstance(configfile, str):
            self.config = TestCaseConfig(configfile)
        elif isinstance(configfile, TestCaseConfig):
            self.config = configfile
        else:
            raise TypeError("The config must be a path or a TestCaseConfig instance.")
        self.item_creator = ItemCreator()
        self.process_creator = ProcessCreator()
        #self.reporter = None
        #self.environment = None

    def _create_process(self):
        """
        Create a Process instance.
        """
        root = self.config.get_root()
        process_param = None
        process = None
        for process_type in self.process_creator.process_types():
            process_param = root.find("./%s" % process_type)
            if process_param != None:
                _LOGGER.debug("Find process '%s'", process_type)
                process = self.process_creator.create(process_type)
                break
        if process_param == None or process == None:
            raise ValueError("Can't find process node.")
        return process, process_param

    def update_items(self, items):
        """
        Update items in item_creator.
        """
        self.item_creator.update_items(items)

    def precheck(self):
        """
        Execute precheck task.
        """
        root = self.config.get_root()
        process, process_param = self._create_process()
        ret = process.precheck(self.item_creator,
                               process_param,
                               testcase=root)
        if ret == True:
            _LOGGER.info("Success")
        else:
            _LOGGER.error("Fail")

    def perform_process(self):
        """
        Execute a test case.
        """
        root = self.config.get_root()
        process, process_param = self._create_process()
        ret = process.perform_process(self.item_creator,
                                      process_param,
                                      testcase=root)
        if ret == True:
            _LOGGER.info("Success")
        else:
            _LOGGER.error("Fail")

class TestCaseConfig(object):
    """
    A TestCaseConfig supplys methods to top nodes of a test case XML file and
    a method to validate a test case.
    testcase.xml example:
    <testcase plugin="basic" type="basic" schema="command.xsd">
      <resource>subnodes</resource>
      <loop-process loop="2" quit="fail">
        items
      </loop-process>
    </testcase>
    """
    def __init__(self, configfile):
        assert isinstance(configfile, str)
        self.xmlfile = configfile
        xmlsource = file(self.xmlfile)
        self.xmltree = etree.parse(xmlsource)
        self.xsdfile = None
        self.xsdtree = None
        #self._load_xsd()
        #self._validate()

    def _load_xsd(self):
        """
        Load an XSD file.
        """
        xmlroot = self.xmltree.getroot()
        schema = xmlroot.get("schema")
        sysconf = config.SysConfig()
        plugin = xmlroot.get("plugin")
        conf_dir = sysconf.get_plugin_config_dir(plugin)
        filepath = os.path.join(conf_dir, schema)
        if os.path.exists(filepath):
            self.xsdfile = filepath
        else:
            raise ValueError("Can't find schema '%s'" % schema)
        xsdsource = file(self.xsdfile)
        self.xsdtree = etree.parse(xsdsource)

    def _validate(self):
        """
        Validate an XML file with XSD.
        """
        # XSD validation
        xmlroot = self.xmltree.getroot()
        schema = etree.XMLSchema(self.xsdtree)
        schema.assertValid(xmlroot)
        # name and ref validation
        for node in xmlroot.findall(".//*[@ref]"):
            ref = node.get("ref")
            refnodes = xmlroot.findall(".//*[@name='%s']" % ref)
            length = len(refnodes)
            if length == 0:
                raise SyntaxError("Can't find reference node <%s name='%s'>"
                                   % (node.tag, ref))
            elif length == 1:
                if node.tag != refnodes[0].tag:
                    raise SyntaxError("Can't find reference node <%s name='%s'>"
                                       % (node.tag, ref))
            else:
                raise SyntaxError("Find %d reference nodes which have attribute name='%s'"
                                   % (length, ref))

    def get_root(self):
        """
        Get root node.
        """
        return self.xmltree.getroot()

    def get_plugin(self):
        """
        Get plugin name.
        """
        root = self.xmltree.getroot()
        plugin = root.get("plugin")
        return plugin

    def get_type(self):
        """
        Get test case type.
        """
        root = self.xmltree.getroot()
        casetype = root.get("type")
        return casetype

