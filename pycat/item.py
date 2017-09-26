#! /usr/bin/python

"""
Item Module

This module supplies classes and functions to build items and processes.
"""

#from lxml import etree
import time
import datetime
import re
#import os

#from pycat import config
#from pycat import log
#from pycat import status
import log

_LOGGER_ROOT = log.getLogger("log")
_LOGGER = log.getLogger("log.Item")
_LOGGER_PROC_INFO = log.getLogger("log.ProcInfo")
_LOGGER_PROC_RESULT = log.getLogger("log.ProcResult")
_LOGGER_CYCLE_INFO = log.getLogger("log.CycleInfo")
_LOGGER_CYCLE_RESULT = log.getLogger("log.CycleResult")
_LOGGER_ITEM_INFO = log.getLogger("log.ItemInfo")
_LOGGER_ITEM_RESULT = log.getLogger("log.ItemResult")
_LOGGER_ERROR_ENTRY = log.getLogger("log.ErrorEntry")
_LOGGER_ERROR_TIME = log.getLogger("log.ErrorEntry")
_LOGGER_ERROR_MESG = log.getLogger("log.ErrorMesg")

_PROCESS_LINE = "*" * 40
_CYCLE_LINE = "#" * 40
_ITEM_LINE = "=" * 40
_REPEAT_LINE = "_" * 40
_RETRY_LINE = '-' * 40

#--------------------------------------------------------------------------
# Error Handle Class
#--------------------------------------------------------------------------
class ErrorRecord(Exception):
    """
    An ErrorRecord instance contains message refer to an error, including
    error name, description, message and trigger time.
    """
    def __init__(self,
                 name,
                 message=None,
                 description=None):
        """
        name: error name
        message: error message
        description: the description of this error record.
        """
        Exception.__init__(self)
        self.name = name
        self.description = description
        self.message = message
        self.trigger_time = datetime.datetime.now()

    def __str__(self):
        ret = ("ErrorRecord{name: %s, description: %s, message: %s}"
                % (self.name, self.description, self.message))
        return ret

    def sync_log(self):
        """
        Synchronize error message in memory with log.
        """
        _LOGGER_ERROR_ENTRY.error("%s: %s", self.name, self.description)
        _LOGGER_ERROR_TIME.error("Trigger Time: %s", self.trigger_time)
        lines = self.message.split("\n")
        for line in lines:
            _LOGGER_ERROR_MESG.error(line)

class ErrorRecords(Exception):
    """
    An ErrorRecords instance is a container of ErrorRecord instances.
    """
    def __init__(self):
        Exception.__init__(self)
        self.records = []

    def __str__(self):
        return str(self.records)

    def add_record(self, record):
        """
        Add an ErrorRecord instance.

        record: an ErrorRecord instance
        """
        if not (record in self.records):
            self.records.append(record)

    def remove_record(self, record):
        """
        Remove an ErrorRecord instance.

        record: an ErrorRecord instance.
        """
        if record in self.records:
            self.records.remove(record)

    def size(self):
        """
        Get the size of this ErrorRecords instance.

        Return the size of this ErrorRecords.
        """
        return len(self.records)

    def empty(self):
        """
        Measure whether this ErrorRecords instance is empty.

        Reutrn True if this ErrorRecords instance is empty. Otherwise return
        False.
        """
        if len(self.records) == 0:
            return True
        else:
            return False

class TestItemError(Exception):
    """
    A TestItemError instance should be raised when a TestItem met an error.

    Raise a TestItemError means that a TestItem failed. It doesn't contain
    any error message. All error message should be recorded before raising
    a TestItemError.
    """
    def __init__(self, value=None):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return str(self.value)

class ProcessError(Exception):
    """
    A ProcessError instance should be raised when a Process met an error.

    Raise a ProcessError means that a Process failed. It doesn't contain
    any error message. All error message should be recorded before raising
    a TestItemError.
    """
    def __init__(self, value=None):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return str(self.value)

#--------------------------------------------------------------------------
# Duration Data Type
#--------------------------------------------------------------------------
def convert_duration_data(data):
    """
    Convert XML duration data type to datetime.timedelta.

    XML duration date type:
        The duration data type is used to specify a time interval.
        
        The time interval is specified in the following form "PnYnMnDTnHnMnS"
        where:
        
        P indicates the period (required)
        nY indicates the number of years
        nM indicates the number of months
        nD indicates the number of days
        T indicates the start of a time section (required if you are going to
          specify hours, minutes, or seconds)
        nH indicates the number of hours
        nM indicates the number of minutes
        nS indicates the number of seconds
    """
    assert isinstance(data, str)
    data_dict = {"year": 0,
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

    # Convert XML data to dict.
    mat = re.match("P.*T", data)
    if mat is not None:
        datatmp = mat.group()
    else:
        mat = re.match("P.*[YMD]", data)
        if mat is not None:
            datatmp = data
    spos = datatmp.find("P") + 1
    for key in ("Y", "M", "D"):
        epos = datatmp.find(key)
        if epos != -1:
            val = int(datatmp[spos:epos])
            dkey = date_map[key]
            data_dict[dkey] = val
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
                data_dict[dkey] = val
                spos = epos + 1

    # Convert dict to datetime.timedelta
    duration = datetime.timedelta(days=(data_dict["day"]
                                      + data_dict["month"]*30
                                      + data_dict["year"]*365),
                                  hours=data_dict["hour"],
                                  minutes=data_dict["minute"],
                                  seconds=data_dict["second"])
    #if data_dict["month"] != 0:
    #    raise ValueError("Convert 1 month to 30 days.")
    #if data_dict["year"] != 0:
    #    raise ValueError("Convert 1 year to 365 days.")
    return duration

#---------------------------------------------------------------------------
# Event Handle Class
#---------------------------------------------------------------------------
class EventObserver(object):
    """
    An EventObserver instance will be executed when the relatived event
    happened.
    """
    def __init__(self):
        pass

    def update(self):
        """
        This method will be called when the relatived event happened.
        """
        raise NotImplementedError

class Event(object):
    """
    An Event instance represents an event of a TestItem or a Process, such as
    'CycleStart', 'CycleEnd', 'InitStart', etc.

    Event name rules:
        Event name can contain any char and splited by dot. For example:
            EventA.BB.AAA
            EventA.BB.BBB
            EventB.AA.AAA

        EventA.BB is the parent of EventA.BB.AAB and EventA.BB.BBB.
        EventA is the parent of EventA.BB, EventA.BB.AAB and EventA.BB.BBB.
        If raise EventA.BB.AAA, EventA.BB and EventA will be raised too.
    """
    def __init__(self, name):
        """
        name: Event name
        """
        self.name = name
        self.parent = None
        self.observers = []

    def __str__(self):
        ret = "%s: %d observers" % (self.name, len(self.observers))
        return ret

    def set_parent(self, event):
        """
        Set the parent event.

        event: an Event instance
        """
        self.parent = event

    def register_observer(self, observer):
        """
        Register an observer.

        observer: an EventObserver instance
        """
        if not (observer in self.observers):
            self.observers.append(observer)

    def unregister_observer(self, observer):
        """
        Unregister an observer.

        observer: an EventObserver instance
        """
        if observer in self.observers:
            self.observers.remove(observer)

    def notify_observers(self):
        """
        Notify all observers of this event and its parent.
        """
        for observer in self.observers:
            observer.update()
        if self.parent != None:
            self.parent.notify_observers()

class EventManager(object):
    """
    An EventManager instance contains Event instances and controls them.
    """
    def __init__(self):
        self.event_dict = {}

    def __str__(self):
        return str(self.event_dict)

    def show(self, logger=_LOGGER):
        """
        Print self information to the log.
        """
        logger.info("Events:")
        for key in self.event_dict:
            logger.info("  %s", self.event_dict[key])

    def add_event(self, name):
        """
        Add a new event to the EventManager.

        name: Event name
        """
        if not name in self.event_dict.keys():
            event = Event(name)
            self.event_dict[name] = event
        name_split = name.rsplit(".", 1)
        if len(name_split) == 2:
            parent_name = name_split[0]
            self.add_event(parent_name)
            self.event_dict[name].set_parent(self.event_dict[parent_name])

    def remove_event(self, name):
        """
        Remove an event.

        name: event name
        """
        for key in self.event_dict.keys():
            if re.match(name, key) != None:
                self.event_dict.pop(key)

    def register_observer(self, name, observer):
        """
        Register an observer.

        name: event name
        observer: an EventObserver instance
        """
        if name in self.event_dict.keys():
            self.event_dict[name].register_observer(observer)
        else:
            raise KeyError("Unknown event '%s'" % (name))

    def unregister_observer(self, name, observer):
        """
        Unregister an observer.

        name: event name
        observer: an EventObserver instance
        """
        if name in self.event_dict.keys():
            self.event_dict[name].unregister_observer(observer)
        else:
            raise KeyError("Unknown event '%s'" % (name))

    def notify_observers(self, name):
        """
        Notify all observers of an event.

        name: event name
        """
        if name in self.event_dict.keys():
            self.event_dict[name].notify_observers()
        else:
            raise KeyError("Unknown event '%s'" % (name))

#---------------------------------------------------------------------------
# Item Class
#---------------------------------------------------------------------------
class Item(object):
    """
    This is the interface of all SimpleItem, DecoratorItem and Process
    classes.
    """
    item_type = None
    def __init__(self):
        pass

    def __str__(self):
        return "ItemBase"

    def show(self):
        """
        Print self information to the log.
        """
        _LOGGER_ITEM_INFO.info("ItemBase")

    def xml_interpret(self, xmlroot, node):
        """
        Interpret XML parameter.

        xmlroot: XML root node
        node: Item node
        """
        raise NotImplementedError

    def action_init(self):
        """
        Execte actions to initialize an item.
        """
        raise NotImplementedError

    def action_run(self):
        """
        Execute actions to run an item.
        """
        raise NotImplementedError

    def action_clear(self):
        """
        Execute actions to clear resource of an item.
        """
        raise NotImplementedError

    def add_event(self, event):
        """
        Add an event.

        event: event name
        """
        raise NotImplementedError

    def remove_event(self, event):
        """
        Remove an event.

        event: event name
        """
        raise NotImplementedError

    def event_register_observer(self, event, observer):
        """
        Register an observer on an event.

        event: event name
        observer: an EventObserver instance
        """
        raise NotImplementedError

    def event_unregister_observer(self, event, observer):
        """
        Unregister an observer on an event.

        event: event name
        observer: an EventObserver instance
        """
        raise NotImplementedError

    def event_notify_observers(self, event):
        """
        Notify all observers on an event.

        event: event name
        """
        raise NotImplementedError

    def record_error(self, record):
        """
        Record an error.

        record: an ErrorRecord instance
        """
        raise NotImplementedError

#---------------------------------------------------------------------------
# SimpleItem
#---------------------------------------------------------------------------
class SimpleItem(Item):
    """
    SimpleItem is a interface of concrete test items.
    """
    item_type = "simple-item"
    def __init__(self, name=None, desc=None):
        Item.__init__(self)
        self.name = name
        self.desc = desc
        self.rawdata = ""
        self.event_manager = EventManager()

    def __str__(self):
        ret = "SimpleItem: %s" % (self.name)
        return ret

    def show(self):
        """
        Print self information.
        """
        _LOGGER_ITEM_INFO.info("SimpleItem: %s", self.name)
        _LOGGER_ITEM_INFO.info("Description: %s", self.desc)
        _LOGGER_ITEM_INFO.info("Rawdata: %d bytes", len(self.rawdata))
        self.event_manager.show(_LOGGER_ITEM_INFO)

    def xml_interpret(self, xmlroot, node):
        """
        Interpret XML parameter.

        xmlroot: XML root node
        node: Item node
        """
        raise NotImplementedError

    def action_init(self):
        """
        Execte actions to initialize an item.
        """
        raise NotImplementedError

    def action_run(self):
        """
        Execute actions to run an item.
        """
        raise NotImplementedError

    def action_clear(self):
        """
        Execute actions to clear resource of an item.
        """
        raise NotImplementedError

    def get_name(self):
        """
        Get the item name.

        Return the item name.
        """
        return self.name

    def set_name(self, name):
        """
        Set the item name.

        name: item name
        """
        self.name = name

    def get_desc(self):
        """
        Get the item description.

        Return the item description.
        """
        return self.desc

    def set_desc(self, desc):
        """
        Set the item description.

        desc: the item description
        """
        self.desc = desc

    def get_rawdata(self):
        """
        Get rawdata if the item has any rawdata.

        Return rawdata.
        """
        return self.rawdata

    def set_rawdata(self, rawdata):
        """
        Set rawdata.

        rawdata: the rawdata
        """
        self.rawdata = rawdata

    def record_error(self, record):
        """
        Record an error.

        record: an ErrorRecord instance
        """
        # @todo Write record to log and database
        #raise NotImplementedError
        record.sync_log()
        _LOGGER_ITEM_INFO.debug("@todo Update DB.")

    def add_event(self, event):
        """
        Add an event.

        event: event name
        """
        self.event_manager.add_event(event)

    def remove_event(self, event):
        """
        Remove an event.

        name: event name
        """
        self.event_manager.remove_event(event)

    def event_register_observer(self, event, observer):
        """
        Register an observer on an event.

        event: event name
        observer: an EventObserver instance
        """
        self.event_manager.register_observer(event, observer)

    def event_unregister_observer(self, event, observer):
        """
        Unregister an observer on an event.

        event: event name
        observer: an EventObserver instance
        """
        self.event_manager.unregister_observer(event, observer)

    def event_notify_observers(self, event):
        """
        Notify all observers on an event.

        event: event name
        """
        self.event_manager.notify_observers(event)

class PlaceHolderItem(SimpleItem):
    """
    A PlaceHolderItem instance only shows self information.
    """
    item_type = "place-holder"
    def __init__(self, name=None, desc=None):
        SimpleItem.__init__(self, name, desc)
        self.ierror = 0
        self.rerror = 0
        self.cerror = 0
        self.error_record = None

    def __str__(self):
        return "PlaceHolderItem: %s" % (self.name)

    def show(self):
        """
        Print self information to the log.
        """
        _LOGGER_ITEM_INFO.info("PlaceHolderItem: %s", self.name)
        _LOGGER_ITEM_INFO.info("Description: %s", self.desc)
        _LOGGER_ITEM_INFO.info("Rawdata: %d bytes", len(self.rawdata))
        self.event_manager.show(_LOGGER_ITEM_INFO)

    def xml_interpret(self, xmlroot, node):
        """
        Interpret XML parameter.

        xmlroot: XML root node
        node: Item node

        XML Example:
            <place-holder ierror="5" rerror="5" cerror="5">
                <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
            </place-holder>
        """
        assert node.tag == self.item_type
        if node.get("ierror") != None:
            self.ierror = int(node.get("ierror"))
        if node.get("rerror") != None:
            self.rerror = int(node.get("rerror"))
        if node.get("cerror") != None:
            self.cerror = int(node.get("cerror"))
        error_number = len(node.findall("error"))
        if error_number == 0:
            pass
        elif error_number == 1:
            error_node = node.find("error")
            record = ErrorRecord(name=error_node.get("name"),
                                 description=error_node.get("description"),
                                 message=error_node.get("message"))
            self.error_record = record
        else:
            records = ErrorRecords()
            for error_node in node.findall("error"):
                record = ErrorRecord(name=error_node.get("name"),
                                     description=error_node.get("description"),
                                     message=error_node.get("message"))
                records.add_record(record)
            self.error_record = records

    def action_init(self):
        """
        Execte actions to initialize an item.
        """
        self.show()
        if self.ierror > 0:
            self.ierror -= 1
            if self.error_record == None:
                raise ValueError("Raise an error")
            else:
                raise self.error_record

    def action_run(self):
        """
        Execute actions to run an item.
        """
        self.show()
        if self.rerror > 0:
            self.rerror -= 1
            if self.error_record == None:
                raise ValueError("Raise an error")
            else:
                raise self.error_record

    def action_clear(self):
        """
        Execute actions to clear resource of an item.
        """
        self.show()
        if self.cerror > 0:
            self.cerror -= 1
            if self.error_record == None:
                raise ValueError("Raise an error")
            else:
                raise self.error_record

    def set_error(self, action, error_num, error_record=None):
        """
        Set error.

        action: action name. Must be action_init, action_run or action_clear.
        error_num: the number how many times the error should be raised.
        error_record: an error_record instance.
        """
        assert action in ("action_init", "action_run", "action_clear")
        assert isinstance(error_num, int)
        if action == "action_init":
            self.ierror = error_num
        elif action == "action_run":
            self.rerror = error_num
        elif action == "action_clear":
            self.cerror = error_num
        self.error_record = error_record

#---------------------------------------------------------------------------
# DecoratorItem
#---------------------------------------------------------------------------
class DecoratorItem(Item):
    """
    DecoratorItem is a interface for PredelayItem, RepeatItem, etc.
    """
    item_type = "decorator-item"
    def __init__(self, item):
        Item.__init__(self)
        assert isinstance(item, Item)
        self.item = item

    def __str__(self):
        return "DecoratorItem(%s)" % (self.item)

    def show(self):
        """
        Print self information into the log.
        """
        self.item.show()

    def xml_interpret(self, xmlroot, node):
        """
        Interpret XML parameter.

        xmlroot: XML root node
        node: Item node
        """
        raise NotImplementedError

    def action_init(self):
        """
        Execte actions to initialize an item.
        """
        raise NotImplementedError

    def action_run(self):
        """
        Execute actions to run an item.
        """
        raise NotImplementedError

    def action_clear(self):
        """
        Execute actions to clear resource of an item.
        """
        raise NotImplementedError

    def record_error(self, record):
        """
        Record an error.

        record: an ErrorRecord instance
        """
        self.item.record_error(record)

    def get_name(self):
        """
        Get the item name.

        Return the item name.
        """
        return self.item.get_name()

    def set_name(self, name):
        """
        Set the item name.

        name: item name
        """
        self.item.set_name(name)

    def get_desc(self):
        """
        Get the item description.

        Return the item description.
        """
        return self.item.get_desc()

    def set_desc(self, desc):
        """
        Set the item description.

        desc: the item description
        """
        self.item.set_desc(desc)

    def get_rawdata(self):
        """
        Get rawdata if the item has any rawdata.

        Return rawdata.
        """
        return self.item.get_rawdata()

    def set_rawdata(self, rawdata):
        """
        Set rawdata.

        rawdata: the rawdata
        """
        self.item.set_rawdata(rawdata)

    def add_event(self, event):
        """
        Add an event.

        event: event name
        """
        self.item.add_event(event)

    def remove_event(self, event):
        """
        Remove an event.

        name: event name
        """
        self.item.remove_event(event)

    def event_register_observer(self, event, observer):
        """
        Register an observer on an event.

        event: event name
        observer: an EventObserver instance
        """
        self.item.event_register_observer(event, observer)

    def event_unregister_observer(self, event, observer):
        """
        Unregister an observer on an event.

        event: event name
        observer: an EventObserver instance
        """
        self.item.event_unregister_observer(event, observer)

    def event_notify_observers(self, event):
        """
        Notify all observers on an event.

        event: event name
        """
        self.item.event_notify_observers(event)

class PredelayItem(DecoratorItem):
    item_type = "predelay"
    def __init__(self, item):
        DecoratorItem.__init__(self, item)
        self.delay = None
        self.add_event("PredelayStart")
        self.add_event("PredelayEnd")

    def __str__(self):
        return "PredelayItem(%s)" % (self.item)

    def show(self):
        self.item.show()
        _LOGGER_ITEM_INFO.info("Predelay:")
        _LOGGER_ITEM_INFO.info("  time: %s", self.delay)

    def xml_interpret(self, xmlroot, node):
        """
        XML Example:
            <predelay value="PT5S"/>
        """
        assert node.tag == self.item_type
        self.delay = convert_duration_data(node.get("value"))

    def action_init(self):
        self.item.action_init()
        if self.delay != None:
            _LOGGER_ITEM_INFO.info("Predelay:")
            _LOGGER_ITEM_INFO.info("  time: %s", self.delay)
        else:
            raise ValueError("Predelay value hasn't set.")

    def action_run(self):
        _LOGGER_ITEM_INFO.info("Predelay: wait %s", self.delay)
        self.event_notify_observers("PredelayStart")
        time.sleep(self.delay.total_seconds())
        self.event_notify_observers("PredelayEnd")
        self.item.action_run()

    def action_clear(self):
        self.item.action_clear()

    def set_delay(self, delay):
        assert isinstance(delay, datetime.timedelta)
        self.delay = delay


class DelayItem(DecoratorItem):
    item_type = "delay"
    def __init__(self, item):
        DecoratorItem.__init__(self, item)
        self.delay = None
        self.add_event("DelayStart")
        self.add_event("DelayEnd")

    def __str__(self):
        return "DelayItem(%s)" % (self.item)

    def show(self):
        self.item.show()
        _LOGGER_ITEM_INFO.info("Delay:")
        _LOGGER_ITEM_INFO.info("  time: %s", self.delay)

    def xml_interpret(self, xmlroot, node):
        """
        XML Example:
            <delay value="PT5S"/>
        """
        assert node.tag == self.item_type
        self.delay = convert_duration_data(node.get("value"))

    def action_init(self):
        self.item.action_init()
        if self.delay != None:
            _LOGGER_ITEM_INFO.info("Delay:")
            _LOGGER_ITEM_INFO.info("  time: %s", self.delay)
        else:
            raise ValueError("Delay value hasn't set.")

    def action_run(self):
        self.item.action_run()
        _LOGGER_ITEM_INFO.info("Delay: wait %s", self.delay)
        self.event_notify_observers("DelayStart")
        time.sleep(self.delay.total_seconds())
        self.event_notify_observers("DelayEnd")

    def action_clear(self):
        self.item.action_clear()

    def set_delay(self, delay):
        assert isinstance(delay, datetime.timedelta)
        self.delay = delay

class RetryItem(DecoratorItem):
    item_type = "retry"
    def __init__(self, item):
        DecoratorItem.__init__(self, item)
        self.retry = None
        self.interval = None
        self.add_event("RetryOnce")

    def __str__(self):
        ret = "RetryItem(%s)" % (self.item)
        return ret

    def show(self):
        self.item.show()
        _LOGGER_ITEM_INFO.info("Retry:")
        _LOGGER_ITEM_INFO.info("  retry: %d", self.retry)
        _LOGGER_ITEM_INFO.info("  interval: %s", self.interval)

    def xml_interpret(self, xmlroot, node):
        """
        <retry value="5" interval="PT5S"/>
        """
        assert node.tag == self.item_type
        retry = int(node.get("value"))
        if retry > 0:
            self.retry = retry
        else:
            raise ValueError("Invalid retry value: %d", retry)

        if node.get("interval") != None:
            self.interval = convert_duration_data(node.get("interval"))

    def action_init(self):
        self.item.action_init()
        if self.retry != None:
            _LOGGER_ITEM_INFO.info("Retry:")
            _LOGGER_ITEM_INFO.info("  retry: %d", self.retry)
            _LOGGER_ITEM_INFO.info("  interval: %s", self.interval)
        else:
            raise ValueError("Retry value hasn't set.")

    def action_run(self):
        succeed = False
        for times in range(self.retry):
            try:
                self.item.action_run()
            except ErrorRecord, err:
                self.record_error(err)
            except ErrorRecords, errs:
                for record in errs.records:
                    self.record_error(record)
            except Exception, err:
                record = ErrorRecord(name="unnamed",
                                     description=type(err),
                                     message=str(err))
                self.record_error(record)
            else:
                succeed = True
                break
            _LOGGER_ITEM_INFO.info(_RETRY_LINE)
            _LOGGER_ITEM_INFO.warning("Retry: execution %d", times + 1)
            self.event_notify_observers("RetryOnce")
            if self.interval != None and self.interval.total_seconds() != 0:
                _LOGGER_ITEM_INFO.info("Retry Interval: wait %s", self.interval)
                time.sleep(self.interval.total_seconds())
        if not succeed:
            self.event_notify_observers("RetryOnce")
            self.item.action_run()

    def action_clear(self):
        self.item.action_clear()

    def set_retry(self, retry):
        assert isinstance(retry, int)
        if retry > 0:
            self.retry = retry
        else:
            raise ValueError("Invalid retry value: %d", retry)

class RepeatItem(DecoratorItem):
    item_type = "repeat"
    def __init__(self, item):
        DecoratorItem.__init__(self, item)
        self.repeat = None
        self.interval = None
        self.add_event("RepeatOnce")

    def __str__(self):
        ret = "RepeatItem(%s)" % (self.item)
        return ret

    def show(self):
        self.item.show()
        _LOGGER_ITEM_INFO.info("Repeat:")
        _LOGGER_ITEM_INFO.info("  repeat: %d", self.repeat)
        _LOGGER_ITEM_INFO.info("  interval: %s", self.interval)

    def xml_interpret(self, xmlroot, node):
        """
        XML Example:
            <repeat value="5" interval="PT5S"/>
        """
        assert node.tag == self.item_type
        repeat = int(node.get("value"))
        if repeat > 0:
            self.repeat = repeat
        else:
            raise ValueError("Invalid repeat value: %d", repeat)

        if node.get("interval") != None:
            self.interval = convert_duration_data(node.get("interval"))

    def action_init(self):
        self.item.action_init()
        ret = True
        if self.repeat != None:
            _LOGGER_ITEM_INFO.info("Repeat:")
            _LOGGER_ITEM_INFO.info("  repeat: %d", self.repeat)
            _LOGGER_ITEM_INFO.info("  interval: %s", self.interval)
        else:
            raise ValueError("Repeat value hasn't set.")

    def action_run(self):
        for i in range(self.repeat):
            _LOGGER_ITEM_INFO.info(_REPEAT_LINE)
            _LOGGER_ITEM_INFO.info("Repeat: execution %d", i + 1)
            self.event_notify_observers("RepeatOnce")
            self.item.action_run()
            if self.interval != None:
                _LOGGER_ITEM_INFO.info("Repeat Interval: wait %s ",
                                        self.interval)
                time.sleep(self.interval.total_seconds())

    def action_clear(self):
        self.item.action_clear()

    def set_repeat(self, repeat):
        assert isinstance(repeat, int)
        if repeat > 0:
            self.repeat = repeat
        else:
            raise ValueError("Invalid repeat value: %d", repeat)

class ErrorHandleItem(DecoratorItem):    
    item_type = "error-handle"
    def __init__(self, item):
        DecoratorItem.__init__(self, item)
        self.ignore_all_errors = False
        self.ignore_unnamed_errors = False
        self.error_handle = {}
        self.add_event("IgnoreError")

    def __str__(self):
        ret = "ErrorHandleItem(%s)" % (self.item)
        return ret

    def show(self):
        self.item.show()
        _LOGGER_ITEM_INFO.info("ErrorHandle:")
        _LOGGER_ITEM_INFO.info("  ignore-all-errors: %s",
                               self.ignore_all_errors)
        _LOGGER_ITEM_INFO.info("  ignore-unnamed-errors: %s",
                               self.ignore_unnamed_errors)
        if len(self.error_handle) == 0:
            _LOGGER_ITEM_INFO.info("  error-handle: None")
        else:
            _LOGGER_ITEM_INFO.info("  error-handle:")
            for key in self.error_handle:
                _LOGGER_ITEM_INFO.info("    %s: ignore=%s",
                                       key, self.error_handle[key])

    def set_ignore_all_errors(self, value):
        assert value in (True, False)
        self.ignore_all_errors = value

    def set_ignore_unnamed_errors(self, value):
        assert value in (True, False)
        self.ignore_unnamed_errors = value

    def set_ignore_error(self, name, value):
        assert value in (True, False)
        self.error_handle[name] = value

    def xml_interpret(self, xmlroot, node):
        """
        XML Example:
            <error-handle ignore_all_errors="true" ignore_unnamed_errors="true">
                <error name="error-1" ignore="true"/>
                <error name="error-2" ignore="true"/>
            </error-handle>
        """
        assert node.tag == self.item_type
        if node.get("ignore_all_errors") == "true":
            self.ignore_all_errors = True
        else:
            self.ignore_all_errors = False

        if node.get("ignore_unnamed_errors") == "true":
            self.ignore_unnamed_errors = True
        else:
            self.ignore_unnamed_errors = False

        for subnode in node.findall("error"):
            if subnode.get("ignore") == "true":
                ignore = True
            elif subnode.get("ignore") == "false":
                ignore = False
            self.error_handle[subnode.get("name")] = ignore

    def action_init(self):
        self.item.action_init()
        _LOGGER_ITEM_INFO.info("ErrorHandle:")
        _LOGGER_ITEM_INFO.info("  ignore-all-errors: %s",
                               self.ignore_all_errors)
        _LOGGER_ITEM_INFO.info("  ignore-unnamed-errors: %s",
                               self.ignore_unnamed_errors)
        if len(self.error_handle) == 0:
            _LOGGER_ITEM_INFO.info("  error-handle: None")
        else:
            _LOGGER_ITEM_INFO.info("  error-handle:")
            for key in self.error_handle:
                _LOGGER_ITEM_INFO.info("    %s: ignore=%s",
                                       key, self.error_handle[key])

    def action_run(self):
        try:
            self.item.action_run()

        except ErrorRecord, err:
            if err.name in self.error_handle.keys():
                # Users have defined whether this error should be ignored.
                if self.error_handle[err.name] == False:
                    raise err
                else:
                    _LOGGER_ITEM_INFO.warning("Ignore an error.")
                    self.record_error(err)
                    self.event_notify_observers("IgnoreError")
            else:
                # Use default value to decide whether this error should be
                # ignored.
                if self.ignore_all_errors == False:
                    raise err
                else:
                    _LOGGER_ITEM_INFO.warning("Ignore an error.")
                    self.record_error(err)
                    self.event_notify_observers("IgnoreError")

        except ErrorRecords, errs:
            catched_errors = ErrorRecords()
            for err in errs.records:
                if err.name in self.error_handle.keys():
                    # Users have defined whether this error should be ignored.
                    if self.error_handle[err.name] == False:
                        catched_errors.records.append(err)
                    else:
                        _LOGGER_ITEM_INFO.warning("Ignore an error.")
                        self.record_error(err)
                        self.event_notify_observers("IgnoreError")
                else:
                    # Use default value to decide whether this error should be
                    # ignored.
                    if self.ignore_all_errors == False:
                        catched_errors.records.append(err)
                    else:
                        _LOGGER_ITEM_INFO.warning("Ignore an error.")
                        self.record_error(err)
                        self.event_notify_observers("IgnoreError")
            # If there are catched errors, raise it again.
            if len(catched_errors.records) != 0:
                raise catched_errors

        except Exception, err:
            # Catch other errors
            record = ErrorRecord(name="unnamed",
                                 description=type(err),
                                 message=str(err))
            if self.ignore_all_errors or self.ignore_unnamed_errors:
                _LOGGER_ITEM_INFO.warning("Ignore an error.")
                self.record_error(record)
                self.event_notify_observers("IgnoreError")
            else:
                raise record

    def action_clear(self):
        self.item.action_clear()

#---------------------------------------------------------------------------
# ItemFactory
#---------------------------------------------------------------------------
class ItemFactory(object):
    def __init__(self):
        self.item_dict = {PlaceHolderItem.item_type: PlaceHolderItem}

    def create_item(self, xmlroot, node):
        if node.tag in self.item_dict.keys():
            item = self.item_dict[node.tag]()
            item.xml_interpret(xmlroot, node)
            return item
        else:
            ValueError("Unknown item '%s'", node.tag)

#---------------------------------------------------------------------------
# TestItem
#---------------------------------------------------------------------------
class TisLogEO(EventObserver):
    """
    Test Item Start Log EventObserver
    Update Log when the 'InitStart', 'RunStart' or 'ClearStart' event of a
    TestItem instance happened.
    """
    def __init__(self, item):
        EventObserver.__init__(self)
        self.item = item

    def update(self):
        _LOGGER_ROOT.setItem(self.item.get_name())
        _LOGGER_ITEM_INFO.info(_ITEM_LINE)
        _LOGGER_ITEM_INFO.info(self.item.get_desc())

class TiisLogEO(EventObserver):
    """
    Test Item InitStart Log EventObserver
    Update Log when the 'InitStart' event of a TestItem instance happened.
    """
    def __init__(self, item):
        EventObserver.__init__(self)
        self.item = item

    def update(self):
        _LOGGER_ROOT.setItem(self.item.get_name())
        _LOGGER_ITEM_INFO.info(_ITEM_LINE)

class TiesLogEO(EventObserver):
    """
    Test Item End.Succeed Log EventObserver
    Update Log when the 'InitEnd.Succeed', 'RunEnd.Succeed' or
    'ClearEnd.Succeed' event of a TestItem instance happened.
    """
    def __init__(self, item):
        EventObserver.__init__(self)
        self.item = item

    def update(self):
        _LOGGER_ITEM_INFO.info("")
        _LOGGER_ITEM_RESULT.info("%s: Succeed", self.item.get_name())

class TiefLogEO(EventObserver):
    """
    Test Item End.Fail Log EventObserver
    Update Log when the 'InitEnd.Fail', 'RunEnd.Fail' or
    'ClearEnd.Fail' event of a TestItem instance happened.
    """
    def __init__(self, item):
        EventObserver.__init__(self)
        self.item = item

    def update(self):
        _LOGGER_ITEM_INFO.info("")
        _LOGGER_ITEM_RESULT.error("%s: Fail", self.item.get_name())

# @todo Add DB EventObserver
class TiisDBEO(EventObserver):
    """
    Test Item 'InitStart' Database EventObserver
    """
    def __init__(self, item):
        pass

    def update(self):
        pass

class TestItem(DecoratorItem):
    item_type = "item"
    item_factory = ItemFactory()
    def __init__(self):
        DecoratorItem.__init__(self, PlaceHolderItem())

    def set_default_events(self):
        # Add Events
        self.item.add_event("InitStart")
        self.item.add_event("InitEnd.Succeed")
        self.item.add_event("InitEnd.Fail")
        self.item.add_event("RunStart")
        self.item.add_event("RunEnd.Succeed")
        self.item.add_event("RunEnd.Fail")
        self.item.add_event("ClearStart")
        self.item.add_event("ClearEnd.Succeed")
        self.item.add_event("ClearEnd.Fail")
        # Register default event observers
        self.item.event_register_observer("InitStart", TiisLogEO(self))
        #self.item.event_register_observer("InitEnd.Succeed", TiesLogEO(self))
        self.item.event_register_observer("InitEnd.Fail", TiefLogEO(self))
        self.item.event_register_observer("RunStart", TisLogEO(self))
        self.item.event_register_observer("RunEnd.Succeed", TiesLogEO(self))
        self.item.event_register_observer("RunEnd.Fail", TiefLogEO(self))
        self.item.event_register_observer("ClearStart", TisLogEO(self))
        #self.item.event_register_observer("ClearEnd.Succeed", TiesLogEO(self))
        self.item.event_register_observer("ClearEnd.Fail", TiefLogEO(self))

    @classmethod
    def set_item_factory(cls, factory):
        cls.item_factory = factory

    def __str__(self):
        return str(self.item)

    def show(self):
        self.item.show()
        _LOGGER_ITEM_INFO.info("Hierarchy:")
        _LOGGER_ITEM_INFO.info("  %s", self.item)

    def xml_interpret(self, xmlroot, node):
        """
        predelay -> repeat(retry(error-handle(one-simple-item))) -> delay

        XML Example:
            <item type="one-simple-item" name="item-name">
                <desc value="A log description"/>
                <predelay value="PT5S"/>
                <repeat value="5" interval="PT5S"/>
                <retry value="5"/>
                <error-handle ignore_all_errors="true" ignore_unnamed_errors="true">
                    <error name="error-1" ignore="true"/>
                    <error name="error-2" ignore="true"/>
                </error-handle>
                <one-simple-item/>
                <delay value="PT5S"/>
            </item>
        """
        assert node.tag == self.item_type
        simple_item = self.item_factory.create_item(xmlroot,
                                                    node.find(node.get("type")))
        if simple_item == None:
            raise ValueError("Unknown item type: %s" % (node.get("type")))
        simple_item.set_name(node.get("name"))
        simple_item.set_desc(node.find("desc").get("value"))

        item = simple_item
        item = ErrorHandleItem(item)
        if node.find("error-handle") != None:
            item.xml_interpret(xmlroot, node.find("error-handle"))

        if node.find("retry") != None:
            item = RetryItem(item)
            item.xml_interpret(xmlroot, node.find("retry"))
        if node.find("repeat") != None:
            item = RepeatItem(item)
            item.xml_interpret(xmlroot, node.find("repeat"))
        if node.find("predelay") != None:
            item = PredelayItem(item)
            item.xml_interpret(xmlroot, node.find("predelay"))
        if node.find("delay") != None:
            item = DelayItem(item)
            item.xml_interpret(xmlroot, node.find("delay"))
        self.item = item
        self.set_default_events()

    def action_init(self):
        item_error = True
        self.event_notify_observers("InitStart")
        try:
            self.item.action_init()
        except ErrorRecord, err:
            self.item.record_error(err)
        except ErrorRecords, errs:
            for record in errs.records:
                self.item.record_error(record)
        except Exception, err:
            record = ErrorRecord(name="unnamed",
                                 description=type(err),
                                 message=str(err))
            self.item.record_error(record)
        else:
            item_error = False

        if item_error:
            self.event_notify_observers("InitEnd.Fail")
            raise TestItemError
        else:
            self.event_notify_observers("InitEnd.Succeed")

    def action_run(self):
        item_error = True
        self.event_notify_observers("RunStart")
        try:
            self.item.action_run()
        except ErrorRecord, err:
            self.item.record_error(err)
        except ErrorRecords, errs:
            for record in errs.records:
                self.item.record_error(record)
        except Exception, err:
            record = ErrorRecord(name="unnamed",
                                 description=type(err),
                                 message=str(err))
            self.item.record_error(record)
        else:
            item_error = False

        if item_error:
            self.event_notify_observers("RunEnd.Fail")
            raise TestItemError
        else:
            self.event_notify_observers("RunEnd.Succeed")

    def action_clear(self):
        item_error = True
        self.event_notify_observers("ClearStart")
        try:
            self.item.action_clear()
        except ErrorRecord, err:
            self.item.record_error(err)
        except ErrorRecords, errs:
            for record in errs.records:
                self.item.record_error(record)
        except Exception, err:
            record = ErrorRecord(name="unnamed",
                                 description=type(err),
                                 message=str(err))
            self.item.record_error(record)
        else:
            item_error = False

        if item_error:
            self.event_notify_observers("ClearEnd.Fail")
            raise TestItemError
        else:
            self.event_notify_observers("ClearEnd.Succeed")

class AssemblyItem(DecoratorItem):
    def __init__(self):
        """
        XML Example:
           <assembly-item>
             <predelay value="PT5S">
               <delay value="PT5S">
                 <repeat value="5" interval="PT5S">
                   <retry value="5">
                     <error-handle ignore_all_errors="true" ignore_unnamed_errors="true">
                       <error name="error-1" ignore="true"/>
                       <error name="error-2" ignore="true"/>
                       <one-simple-item/>
                     </error-handle>
                   </retry>
                 </repeat>
               </delay>
             </predelay>
           </assembly-item>
        """
        pass

#---------------------------------------------------------------------------
# Process
#---------------------------------------------------------------------------

PROC_STAGE_INIT = "Initialize"
PROC_STAGE_RUN = "Execute"
PROC_STAGE_CLEAR = "Clear"

class PsLogEO(EventObserver):
    """
    Stage Start Log EventObserver
    Update Log when the 'InitStart', 'RunStart' or 'ClearStart' events of a
    Process instance happened.
    """
    def __init__(self, process):
        EventObserver.__init__(self)
        self.process = process

    def update(self):
        _LOGGER_ROOT.setProcess(self.process.get_name())
        _LOGGER_ROOT.setStage(self.process.get_stage())
        _LOGGER_ROOT.setCycle("None")
        _LOGGER_ROOT.setItem("None")
        _LOGGER_PROC_INFO.info(_PROCESS_LINE)
        _LOGGER_PROC_INFO.info("%s %s: Start",
                               self.process.get_stage(),
                               self.process.get_name())

class PesLogEO(EventObserver):
    """
    Process End.Succeed Log EventObserver
    Update Log when the 'InitEnd.Succeed', 'RunEnd.Succeed' or
    'ClearEnd.Succeed' events of a Process instance happened.
    """
    def __init__(self, process):
        EventObserver.__init__(self)
        self.process = process

    def update(self):
        _LOGGER_ROOT.setItem("None")
        _LOGGER_ROOT.setCycle("None")
        _LOGGER_PROC_INFO.info("")
        _LOGGER_PROC_RESULT.info("%s %s: Succeed",
                               self.process.get_stage(),
                               self.process.get_name())

class PefLogEO(EventObserver):
    """
    Process End.Fail Log EventObserver
    Update Log when the 'InitEnd.Fail', 'RunEnd.Fail' or
    'ClearEnd.Fail' event of a Process instance happened.
    """
    def __init__(self, process):
        EventObserver.__init__(self)
        self.process = process

    def update(self):
        _LOGGER_ROOT.setItem("None")
        _LOGGER_ROOT.setCycle("None")
        _LOGGER_PROC_INFO.info("")
        _LOGGER_PROC_RESULT.info("%s %s: Fail",
                               self.process.get_stage(),
                               self.process.get_name())

class CsLogEO(EventObserver):
    """
    Cycle Start Log EventObserver
    Update Log when the 'CycleStart' event of a Process instance happened.
    """
    def __init__(self, process):
        EventObserver.__init__(self)
        self.process = process

    def update(self):
        _LOGGER_ROOT.setItem("None")
        cycle = "Cycle-%d" % (self.process.get_cycle())
        _LOGGER_ROOT.setCycle(cycle)
        _LOGGER_CYCLE_INFO.info(_CYCLE_LINE)
        _LOGGER_CYCLE_INFO.info("%s Cycle-%s: Start",
                                self.process.get_name(),
                                self.process.get_cycle())

class CesLogEO(EventObserver):
    """
    Cycle End.Succeed Log EventObserver
    Update Log when the 'CycleEnd.Succeed' event of a Process instance
    happened.
    """
    def __init__(self, process):
        EventObserver.__init__(self)
        self.process = process

    def update(self):
        _LOGGER_ROOT.setItem("None")
        _LOGGER_CYCLE_INFO.info("")
        _LOGGER_CYCLE_RESULT.info("%s Cycle-%s: Succeed",
                                  self.process.get_name(),
                                  self.process.get_cycle())

class CefLogEO(EventObserver):
    """
    Cycle End.Fail Log EventObserver
    Update Log when the 'CycleEnd.Fail' event of a Process instance
    happened.
    """
    def __init__(self, process):
        EventObserver.__init__(self)
        self.process = process

    def update(self):
        _LOGGER_ROOT.setItem("None")
        _LOGGER_CYCLE_INFO.info("")
        _LOGGER_CYCLE_RESULT.info("%s Cycle-%s: Fail",
                                  self.process.get_name(),
                                  self.process.get_cycle())

class Process(Item):
    item_type = "process"
    def __init__(self):
        Item.__init__(self)
        self.items = []
        self.event_manager = EventManager()
        self.stage = None

    def __str__(self):
        return "Process: %d items" % (len(self.items))

    def show(self):
        _LOGGER_PROC_INFO.info("Process:")
        for item in self.items:
            item.show()

    def get_completion_percentage(self):
        raise NotImplementedError

    def get_stage(self):
        return self.stage

    def set_stage(self, stage):
        assert stage in (PROC_STAGE_INIT, PROC_STAGE_RUN, PROC_STAGE_CLEAR)
        self.stage = stage

    def xml_interpret_attribute(self, xmlroot, node):
        raise NotImplementedError

    def xml_interpret(self, xmlroot, node):
        """
        XML Example:
            <process args="value">
                <item/>
                <item/>
            </process>
        """
        assert node.tag == self.item_type
        self.xml_interpret_attribute(xmlroot, node)
        for item_node in node:
            item = TestItem()
            item.xml_interpret(xmlroot, item_node)
            self.items.append(item)

    def action_init(self):
        raise NotImplementedError

    def action_run(self):
        raise NotImplementedError

    def action_clear(self):
        raise NotImplementedError

    def add_event(self, event):
        self.event_manager.add_event(event)

    def remove_event(self, event):
        self.event_manager.remove_event(event)

    def event_register_observer(self, event, observer):
        self.event_manager.register_observer(event, observer)

    def event_unregister_observer(self, event, observer):
        self.event_manager.unregister_observer(event, observer)

    def event_notify_observers(self, event):
        self.event_manager.notify_observers(event)


class SimpleProcess(Process):
    item_type = "simple-process"
    def __init__(self):
        Process.__init__(self)
        self.name = None
        self.ignore_error = False
        self.cycle_count = 0
        self.completion_percentage = 0.0
        self.add_event("InitStart")
        self.add_event("InitEnd.Succeed")
        self.add_event("InitEnd.Fail")
        self.add_event("RunStart")
        self.add_event("RunEnd.Succeed")
        self.add_event("RunEnd.Fail")
        self.add_event("ClearStart")
        self.add_event("ClearEnd.Succeed")
        self.add_event("ClearEnd.Fail")
        self.add_event("CycleStart")
        self.add_event("CycleEnd.Succeed")
        self.add_event("CycleEnd.Fail")
        # Register default event observers
        self.event_register_observer("InitStart", PsLogEO(self))
        self.event_register_observer("InitEnd.Succeed", PesLogEO(self))
        self.event_register_observer("InitEnd.Fail", PefLogEO(self))
        self.event_register_observer("RunStart", PsLogEO(self))
        self.event_register_observer("RunEnd.Succeed", PesLogEO(self))
        self.event_register_observer("RunEnd.Fail", PefLogEO(self))
        self.event_register_observer("ClearStart", PsLogEO(self))
        self.event_register_observer("ClearEnd.Succeed", PesLogEO(self))
        self.event_register_observer("ClearEnd.Fail", PefLogEO(self))
        self.event_register_observer("CycleStart", CsLogEO(self))
        self.event_register_observer("CycleEnd.Succeed", CesLogEO(self))
        self.event_register_observer("CycleEnd.Fail", CefLogEO(self))

    def __str__(self):
        return "SimpleProcess: %s" % (self.name)

    def show(self):
        _LOGGER_PROC_INFO.info("SimpleProcess: %s", self.name)
        _LOGGER_PROC_INFO.info("IgnoreError: %s", self.ignore_error)
        self.event_manager.show(logger=_LOGGER_PROC_INFO)
        _LOGGER_PROC_INFO.info("Items: %d", len(self.items))
        for item in self.items:
            _LOGGER_ITEM_INFO.info(_ITEM_LINE)
            item.show()

    def get_name(self):
        return self.name

    def set_name(self, name):
        assert isinstance(name, str)
        self.name = name

    def get_ignore_error(self):
        return self.ignore_error

    def set_ignore_error(self, value):
        assert value in (True, False)
        self.ignore_error = value

    def get_cycle(self):
        return self.cycle_count

    def get_completion_percentage(self):
        return self.completion_percentage

    def xml_interpret_attribute_name(self, xmlroot, node):
        self.name = node.get("name")

    def xml_interpret_attribute_ignore_error(self, xmlroot, node):
        ignore_error = node.get("ignore_error")
        if ignore_error in ("true", "True", "TRUE"):
            self.ignore_error = True
        else:
            self.ignore_error = False

    def xml_interpret_attribute(self, xmlroot, node):
        """
        XML Example:
            <simple-process name="abc" ignore_error="true">
                <item/>
                <item/>
            </simple-process>
        """
        self.xml_interpret_attribute_name(xmlroot, node)
        self.xml_interpret_attribute_ignore_error(xmlroot, node)

    def action_init(self):
        self.set_stage(PROC_STAGE_INIT)
        no_error = True
        self.event_notify_observers("InitStart")
        for item in self.items:
            try:
                item.action_init()
            except TestItemError:
                no_error = False
        if no_error:
            self.event_notify_observers("InitEnd.Succeed")
        else:
            self.event_notify_observers("InitEnd.Fail")
            raise ProcessError

    def action_run_catch_error(self):
        self.set_stage(PROC_STAGE_RUN)
        no_error = True
        self.cycle_count = 1
        count = 0.0
        self.event_notify_observers("RunStart")
        self.event_notify_observers("CycleStart")
        for item in self.items:
            try:
                item.action_run()
            except TestItemError:
                no_error = False
                break
            count += 1
            self.completion_percentage = count/len(self.items)
        if no_error:
            self.event_notify_observers("CycleEnd.Succeed")
            self.event_notify_observers("RunEnd.Succeed")
        else:
            self.event_notify_observers("CycleEnd.Fail")
            self.event_notify_observers("RunEnd.Fail")
            raise ProcessError

    def action_run_ignore_error(self):
        self.set_stage(PROC_STAGE_RUN)
        no_error = True
        self.cycle_count = 1
        count = 0.0
        self.event_notify_observers("RunStart")
        self.event_notify_observers("CycleStart")
        for item in self.items:
            try:
                item.action_run()
            except TestItemError:
                no_error = False
            count += 1
            self.completion_percentage = count/len(self.items)
        if no_error:
            self.event_notify_observers("CycleEnd.Succeed")
            self.event_notify_observers("RunEnd.Succeed")
        else:
            self.event_notify_observers("CycleEnd.Fail")
            self.event_notify_observers("RunEnd.Fail")
            raise ProcessError

    def action_run(self):
        if not self.ignore_error:
            self.action_run_catch_error()
        else:
            self.action_run_ignore_error()

    def action_clear(self):
        self.set_stage(PROC_STAGE_CLEAR)
        no_error = True
        self.event_notify_observers("ClearStart")
        for item in self.items:
            try:
                item.action_clear()
            except TestItemError:
                no_error = False
        if no_error:
            self.event_notify_observers("ClearEnd.Succeed")
        else:
            self.event_notify_observers("ClearEnd.Fail")
            raise ProcessError

class CceLogEO(EventObserver):
    def __init__(self, process):
        EventObserver.__init__(self)
        self.process = process

    def update(self):
        _LOGGER_PROC_INFO.info("CompletedCycle: %d", self.process.get_cycle())
        _LOGGER_PROC_INFO.info("TotalCycle: %s", self.process.get_total_cycle())
        _LOGGER_PROC_INFO.info("Completion: %.1f%%", 
                                  100*self.process.get_completion_percentage())

class CycleProcess(SimpleProcess):
    item_type = "cycle-process"
    def __init__(self):
        SimpleProcess.__init__(self)
        self.total_cycle = 0
        self.event_register_observer("CycleEnd", CceLogEO(self))

    def __str__(self):
        return "CycleProcess: %s" % (self.name)

    def show(self):
        _LOGGER_PROC_INFO.info("CycleProcess: %s", self.name)
        _LOGGER_PROC_INFO.info("IgnoreError: %s", self.ignore_error)
        _LOGGER_PROC_INFO.info("TotalCycle: %s", self.total_cycle)
        self.event_manager.show(logger=_LOGGER_PROC_INFO)
        _LOGGER_PROC_INFO.info("Items: %d", len(self.items))
        for item in self.items:
            _LOGGER_ITEM_INFO.info(_ITEM_LINE)
            item.show()

    def set_total_cycle(self, num):
        assert isinstance(num, int)
        self.total_cycle = num

    def get_total_cycle(self):
        return self.total_cycle

    def xml_interpret_attribute_total_cycle(self, xmlroot, node):
        total_cycle = int(node.get("cycle_total"))
        if total_cycle > 0:
            self.total_cycle = total_cycle
        else:
            raise ValueError("Invalid 'total_cycle' value: %d" % (cycle_total))

    def xml_interpret_attribute(self, xmlroot, node):
        """
        XML Example:
            <cycle-process name="abc" total_cycle="10" ignore_error="true">
              <item/>
              <item/>
            </cycle-process>
        """
        self.xml_interpret_attribute_name(xmlroot, node)
        self.xml_interpret_attribute_ignore_error(xmlroot, node)
        self.xml_interpret_attribute_total_cycle(xmlroot, node)

    def action_run_ignore_error(self):
        self.set_stage(PROC_STAGE_RUN)
        no_error = True
        item_count = 0.0
        item_total = self.total_cycle * len(self.items)
        self.cycle_count = 0
        self.event_notify_observers("RunStart")
        while self.cycle_count < self.total_cycle:
            cycle_no_error = True
            self.cycle_count += 1
            self.event_notify_observers("CycleStart")
            for item in self.items:
                try:
                    item.action_run()
                except TestItemError:
                    cycle_no_error = False
                finally:
                    item_count += 1
                    self.completion_percentage = item_count / item_total
            if cycle_no_error:
                self.event_notify_observers("CycleEnd.Succeed")
            else:
                self.event_notify_observers("CycleEnd.Fail")
                no_error = False
        if no_error:
            self.event_notify_observers("RunEnd.Succeed")
        else:
            self.event_notify_observers("RunEnd.Fail")

    def action_run_catch_error(self):
        self.set_stage(PROC_STAGE_RUN)
        no_error = True
        item_count = 0.0
        item_total = self.total_cycle * len(self.items)
        self.cycle_count = 0
        self.event_notify_observers("RunStart")
        while self.cycle_count < self.total_cycle and no_error:
            self.cycle_count += 1
            self.event_notify_observers("CycleStart")
            for item in self.items:
                try:
                    item.action_run()
                except TestItemError:
                    no_error = False
                finally:
                    item_count += 1
                    self.completion_percentage = item_count / item_total
                if not no_error:
                    break
            if no_error:
                self.event_notify_observers("CycleEnd.Succeed")
            else:
                self.event_notify_observers("CycleEnd.Fail")

        if no_error:
            self.event_notify_observers("RunEnd.Succeed")
        else:
            self.event_notify_observers("RunEnd.Fail")
            raise ProcessError

    def action_run(self):
        if not self.ignore_error:
            self.action_run_catch_error()
        else:
            self.action_run_ignore_error()

class DceLogEO(EventObserver):
    def __init__(self, process):
        EventObserver.__init__(self)
        self.process = process

    def update(self):
        _LOGGER_PROC_INFO.info("StartTime: %s", self.process.get_start_time())
        _LOGGER_PROC_INFO.info("UsedTime: %s", self.process.get_used_time())
        _LOGGER_PROC_INFO.info("Duration: %s", self.process.get_duration())
        _LOGGER_PROC_INFO.info("%s Completion: %.1f%%", 
                                  self.process.get_name(),
                                  100*self.process.get_completion_percentage())

class DurationProcess(SimpleProcess):
    item_type = "duration-process"
    def __init__(self):
        SimpleProcess.__init__(self)
        self.duration = None
        self.start = None
        self.cycle_count = 0
        self.event_register_observer("CycleEnd", DceLogEO(self))

    def show(self):
        _LOGGER_PROC_INFO.info("DurationProcess: %s", self.name)
        _LOGGER_PROC_INFO.info("IgnoreError: %s", self.ignore_error)
        _LOGGER_PROC_INFO.info("Duration: %s", self.duration)
        self.event_manager.show(logger=_LOGGER_PROC_INFO)
        _LOGGER_PROC_INFO.info("Items: %d", len(self.items))
        for item in self.items:
            _LOGGER_ITEM_INFO.info(_ITEM_LINE)
            item.show()

    def get_start_time(self):
        return self.start

    def get_used_time(self):
        if self.start == None:
            return datetime.timedelta()
        else:
            return datetime.datetime.now() - self.start

    def get_duration(self):
        return self.duration

    def set_duration(self, duration):
        assert isinstance(duration, datetime.timedelta)
        self.duration = duration

    def get_completion_percentage(self):
        if self.start == None:
            return 0.0
        else:
            used_time = datetime.datetime.now() - self.start
            used = used_time.total_seconds()
            total = self.duration.total_seconds()
            self.completion_percentage = used/total
        return self.completion_percentage

    def xml_interpret_attribute_duration(self, xmlroot, node):
        self.duration = convert_duration_data(node.get("duration"))

    def xml_interpret_attribute(self, xmlroot, node):
        """
        XML Example:
            <duration-process name="abc" duration="PT10M" ignore_error="false">
              <item/>
              <item/>
            </duration-process>
        """
        self.xml_interpret_attribute_name(xmlroot, node)
        self.xml_interpret_attribute_ignore_error(xmlroot, node)
        self.xml_interpret_attribute_duration(xmlroot, node)

    def action_run_catch_error(self):
        self.set_stage(PROC_STAGE_RUN)
        no_error = True
        self.start = datetime.datetime.now()
        self.event_notify_observers("RunStart")
        used_time = datetime.timedelta()
        while used_time < self.duration and no_error:
            self.cycle_count += 1
            self.event_notify_observers("CycleStart")
            for item in self.items:
                try:
                    item.action_run()
                except TestItemError:
                    no_error = False
                    break
            used_time = datetime.datetime.now() - self.start
            if no_error:
                self.event_notify_observers("CycleEnd.Succeed")
            else:
                self.event_notify_observers("CycleEnd.Fail")

        if no_error:
            self.event_notify_observers("RunEnd.Succeed")
        else:
            self.event_notify_observers("RunEnd.Fail")
            raise ProcessError

    def action_run_ignore_error(self):
        self.set_stage(PROC_STAGE_RUN)
        no_error = True
        self.start = datetime.datetime.now()
        self.event_notify_observers("RunStart")
        used_time = datetime.timedelta()
        while used_time < self.duration:
            cycle_no_error = True
            self.cycle_count += 1
            self.event_notify_observers("CycleStart")
            for item in self.items:
                try:
                    item.action_run()
                except TestItemError:
                    cycle_no_error = False
            used_time = datetime.datetime.now() - self.start
            if cycle_no_error:
                self.event_notify_observers("CycleEnd.Succeed")
            else:
                self.event_notify_observers("CycleEnd.Fail")
                no_error = False
        if no_error:
            self.event_notify_observers("RunEnd.Succeed")
        else:
            self.event_notify_observers("RunEnd.Fail")

    def action_run(self):
        if not self.ignore_error:
            self.action_run_catch_error()
        else:
            self.action_run_ignore_error()



