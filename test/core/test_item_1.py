#! /usr/bin/python

import unittest
import sys
import xml.etree.ElementTree as ET
sys.path.append("../..")
sys.path.append("../../pycat")
import log
_LOGGER = log.getLogger("log.test")

from item import *

class LogObserver(EventObserver):
    def __init__(self, mesg):
        EventObserver.__init__(self)
        self.mesg = mesg

    def update(self):
        _LOGGER.info(self.mesg)

class ErrorRecordTestCase(unittest.TestCase):
    def testErrorRecord(self):
        _LOGGER.info("========== ErrorRecord ==========")
        record = ErrorRecord("ErrorType1", "Message ...", "An Error")
        _LOGGER.info(record)

    def testErrorRecords(self):
        _LOGGER.info("========== ErrorRecords ==========")
        records = ErrorRecords()
        record1 = ErrorRecord("ErrorType1", "Message ...", "An Error")
        records.add_record(record1)
        record2 = ErrorRecord("ErrorType2", "Message ...", "An Error")
        records.add_record(record2)
        record3 = ErrorRecord("ErrorType3", "Message ...", "An Error")
        records.add_record(record3)
        record4 = ErrorRecord("ErrorType4", "Message ...", "An Error")
        records.add_record(record4)
        record5 = ErrorRecord("ErrorType5", "Message ...", "An Error")
        _LOGGER.info("Add 5 records.")
        records.add_record(record5)
        _LOGGER.info(records)
        for item in records.records:
            _LOGGER.info(item)
        assert records.size() == 5
        _LOGGER.info("Remove 3 records.")
        records.remove_record(record4)
        records.remove_record(record1)
        records.remove_record(record3)
        assert records.size() == 2
        for item in records.records:
            _LOGGER.info(item)
        _LOGGER.info("Remove 2 records.")
        records.remove_record(record5)
        records.remove_record(record2)
        assert records.size() == 0
        assert records.empty()
        for item in records.records:
            _LOGGER.info(item)

class TestItemErrorTC(unittest.TestCase):
    def testTestItemError(self):
        _LOGGER.info("========== TestItemError ==========")
        err = TestItemError("A TestItem Error")
        _LOGGER.info(err)

class ProcessErrorTC(unittest.TestCase):
    def testProcessError(self):
        _LOGGER.info("========== ProcessError ==========")
        err = ProcessError("A Process Error")
        _LOGGER.info(err)

class DurationDataTC(unittest.TestCase):
    def testDurationData(self):
        _LOGGER.info("========== DurationData ==========")
        dura = convert_duration_data("PT5S")
        _LOGGER.info(dura)
        dura = convert_duration_data("PT4M5S")
        _LOGGER.info(dura)
        dura = convert_duration_data("PT3H4M5S")
        _LOGGER.info(dura)
        dura = convert_duration_data("P1YT5S")
        _LOGGER.info(dura)
        dura = convert_duration_data("P1Y2MT5S")
        _LOGGER.info(dura)
        dura = convert_duration_data("P1Y2M3DT5S")
        _LOGGER.info(dura)
        dura = convert_duration_data("P1Y2M3D")
        _LOGGER.info(dura)
        dura = convert_duration_data("P1Y2M3DT4H6M5S")
        _LOGGER.info(dura)

class EventTC(unittest.TestCase):
    def testEvent(self):
        _LOGGER.info("========== Event ==========")
        event = Event("An Event")
        observer1 = LogObserver("Message 1 ...")
        event.register_observer(observer1)
        observer2 = LogObserver("Message 2 ...")
        event.register_observer(observer2)
        observer3 = LogObserver("Message 3 ...")
        event.register_observer(observer3)
        observer4 = LogObserver("Message 4 ...")
        event.register_observer(observer4)
        event.register_observer(observer4)
        event.unregister_observer(observer2)
        _LOGGER.info(event.name)
        event.notify_observers()

class EventManagerTC(unittest.TestCase):
    def testEventManager(self):
        _LOGGER.info("========== EventManager ==========")
        event_manager = EventManager()
        event_manager.add_event("A.AA.AAA.AAA")
        event_manager.add_event("B.AA.AAA.AAA")
        event_manager.add_event("B.BB.AAA.AAA")
        event_manager.add_event("B.BB.BBB.AAA")
        event_manager.add_event("B.BB.BBB.BBB")
        event_manager.add_event("B.BB.BBB.CCC")
        event_manager.add_event("C")
        _LOGGER.info(event_manager.event_dict.keys())
        event_num = len(event_manager.event_dict.keys())
        _LOGGER.info("Event number: %d", event_num)
        assert event_num == 16

        _LOGGER.info("Register Observers")
        event_manager.register_observer("A", LogObserver("A Observer"))
        event_manager.register_observer("A.AA", LogObserver("A.AA Observer"))
        event_manager.register_observer("A.AA.AAA", LogObserver("A.AA.AAA Observer"))
        event_manager.register_observer("A.AA.AAA.AAA", LogObserver("A.AA.AAA.AAA Observer"))
        observer = LogObserver("A.AA Observer 2")
        event_manager.register_observer("A.AA", observer)
        event_manager.notify_observers("A.AA.AAA.AAA")
        _LOGGER.info("Unrgister A.AA Observer 2")
        event_manager.unregister_observer("A.AA", observer)
        event_manager.notify_observers("A.AA.AAA.AAA")

        _LOGGER.info("Remove A.AA")
        event_manager.remove_event("A.AA")
        _LOGGER.info(event_manager.event_dict.keys())
        event_num = len(event_manager.event_dict.keys())
        _LOGGER.info("Event number: %d", event_num)
        assert event_num == 13

        event_manager.register_observer("B", LogObserver("B Observer"))
        event_manager.register_observer("B.AA", LogObserver("B.AA Observer"))
        event_manager.register_observer("B.AA.AAA", LogObserver("B.AA.AAA Observer"))
        event_manager.register_observer("B.BB", LogObserver("B.BB Observer"))
        event_manager.register_observer("B.BB.AAA", LogObserver("B.BB.AAA Observer"))
        event_manager.register_observer("B.BB.AAA.AAA", LogObserver("B.BB.AAA.AAA Observer"))
        event_manager.register_observer("B.BB.BBB", LogObserver("B.BB.BBB Observer"))
        event_manager.register_observer("B.BB.BBB.AAA", LogObserver("B.BB.BBB.AAA Observer"))
        event_manager.register_observer("B.BB.BBB.BBB", LogObserver("B.BB.BBB.BBB Observer"))
        event_manager.register_observer("B.BB.BBB.CCC", LogObserver("B.BB.BBB.CCC Observer"))
        event_manager.register_observer("C", LogObserver("C Observer"))
        _LOGGER.info("Notify B.BB.BBB")
        event_manager.notify_observers("B.BB.BBB")

class ItemTC(unittest.TestCase):
    def testItem(self):
        _LOGGER.info("========== Item ==========")
        item = Item()
        item.show()
        _LOGGER.info(item)

class SimpleItemTC(unittest.TestCase):
    def testBasic(self):
        _LOGGER.info("========== SimpleItem -Basic ==========")
        item = SimpleItem("An Item", "description......")
        _LOGGER.info(item)
        item.show()
        item.set_name("New Item")
        _LOGGER.info("Set name: %s", item.get_name())
        item.set_desc("Abcde......")
        _LOGGER.info("Set desc: %s", item.get_desc())
        item.set_rawdata("rawdata ......")
        _LOGGER.info("Set rawdata: %s", item.get_rawdata())
        item.show()

    def testEvent(self):
        _LOGGER.info("========== SimpleItem -Event ==========")
        item = SimpleItem("An Item", "description......")
        _LOGGER.info("Add events")
        item.add_event("A.AA.BBB")
        item.add_event("C.AA.BBB")
        event_num = len(item.event_manager.event_dict.keys())
        _LOGGER.info("Event number: %d", event_num)
        assert event_num == 6
        item.event_register_observer("A", LogObserver("A Observer"))
        item.event_register_observer("A.AA", LogObserver("A.AA Observer"))
        observer = LogObserver("A.AA Observer 2")
        item.event_register_observer("A.AA", observer)
        item.event_register_observer("A.AA.BBB", LogObserver("A.AA.BBB Observer"))
        item.event_register_observer("C", LogObserver("C Observer"))
        item.event_register_observer("C.AA", LogObserver("C.AA Observer"))
        item.event_register_observer("C.AA.BBB", LogObserver("C.AA.BBB Observer"))
        item.event_notify_observers("A.AA.BBB")
        item.event_notify_observers("C.AA.BBB")
        _LOGGER.info("Unregister A.AA Observer 2")
        item.event_unregister_observer("A.AA", observer)
        item.event_notify_observers("A.AA.BBB")

    def testPlaceHoldItem(self):
        _LOGGER.info("========== PlaceHoldItem ==========")
        xmlroot = None
        node_str = "<place-holder/>"
        node = ET.fromstring(node_str)
        item = PlaceHolderItem()
        item.xml_interpret(xmlroot, node)
        _LOGGER.info("action init")
        item.action_init()
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("action clear")
        item.action_clear()

class DecoratorItemTC(unittest.TestCase):
    def testDecoratorItem(self):
        _LOGGER.info("========== DecoratorItem ==========")
        xmlroot = None
        node_str = "<place-holder/>"
        node = ET.fromstring(node_str)
        item = PlaceHolderItem()
        item.xml_interpret(xmlroot, node)
        item.set_name("An item")
        item.set_desc("Description ......")
        item = DecoratorItem(item)
        item.show()
        item.set_name("New Item")
        _LOGGER.info("Set name: %s", item.get_name())
        item.set_desc("Abcde......")
        _LOGGER.info("Set desc: %s", item.get_desc())
        item.set_rawdata("rawdata ......")
        _LOGGER.info("Set rawdata: %s", item.get_rawdata())
        item.show()

class PredelayItemTC(unittest.TestCase):
    def testAPI(self):
        _LOGGER.info("========== PredelayItem - API ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        item = PredelayItem(item)
        _LOGGER.info("Set predelay=2s")
        item.set_delay(datetime.timedelta(seconds=2))
        _LOGGER.info("action init")
        item.action_init()
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("action clear")
        item.action_clear()

    def testXML(self):
        _LOGGER.info("========== PredelayItem - XML ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        item = PredelayItem(item)
        xmlroot = None
        _LOGGER.info("Set predelay=2s")
        node_str = '<predelay value="PT2S"/>'
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        _LOGGER.info("action init")
        item.action_init()
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("action clear")
        item.action_clear()

class DelayItemTC(unittest.TestCase):
    def testAPI(self):
        _LOGGER.info("========== DelayItem - API ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        item = DelayItem(item)
        _LOGGER.info("Set delay=2s")
        item.set_delay(datetime.timedelta(seconds=2))
        _LOGGER.info("action init")
        item.action_init()
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("action clear")
        item.action_clear()

    def testXML(self):
        _LOGGER.info("========== DelayItem - XML ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        item = DelayItem(item)
        xmlroot = None
        _LOGGER.info("Set delay=2s")
        node_str = '<delay value="PT2S"/>'
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        _LOGGER.info("action init")
        item.action_init()
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("action clear")
        item.action_clear()

class RetryItemTC(unittest.TestCase):
    def testInit(self):
        _LOGGER.info("========== RetryItem - API - Init ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        item.set_error("action_init", 1)
        item = RetryItem(item)
        _LOGGER.info("Set retry=3")
        item.set_retry(3)
        try:
            item.action_init()
        except ValueError:
            _LOGGER.info("Catch an error.")
        else:
            raise ValueError("Should catch an error.")

    def testRunSucc(self):
        _LOGGER.info("========== RetryItem - API - RunSucc ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        item.set_error("action_run", 5)
        item = RetryItem(item)
        _LOGGER.info("Set retry=7")
        item.set_retry(7)
        item.action_run()

    def testRunFail(self):
        _LOGGER.info("========== RetryItem - API - RunFail ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        item.set_error("action_run", 5)
        item = RetryItem(item)
        _LOGGER.info("Set retry=3")
        item.set_retry(3)
        try:
            item.action_run()
        except ValueError:
            _LOGGER.info("Catch an error.")
        else:
            raise ValueError("Should catch an error.")

    def testClear(self):
        _LOGGER.info("========== RetryItem - API - Clear ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        item.set_error("action_clear", 1)
        item = RetryItem(item)
        _LOGGER.info("Set retry=3")
        item.set_retry(3)
        try:
            item.action_clear()
        except ValueError:
            _LOGGER.info("Catch an error.")
        else:
            raise ValueError("Should catch an error.")

class RepeatItemTC(unittest.TestCase):
    def testAPI(self):
        _LOGGER.info("========== RepeatItem - API ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        item = RepeatItem(item)
        item.set_repeat(5)
        _LOGGER.info("action init")
        item.action_init()
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("action clear")
        item.action_clear()

    def testXML(self):
        item = PlaceHolderItem("An Item", "Description ...")
        item = RepeatItem(item)
        xmlroot = None
        _LOGGER.info("Set repeat=10")
        node_str = '<repeat value="10"/>'
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        _LOGGER.info("action init")
        item.action_init()
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("action clear")
        item.action_clear()

class ErrorHandleItemTC(unittest.TestCase):
    def testActionInit(self):
        _LOGGER.info("========== ErrorHandleItem-ActionInit ==========")
        # Can't ignore action_init errors
        item = PlaceHolderItem("An Item", "Description ...")
        item.set_error("action_init", 1)
        item = ErrorHandleItem(item)
        _LOGGER.info("Ignore All Errors")
        item.set_ignore_all_errors(True)
        _LOGGER.info("action init")
        try:
            item.action_init()
        except ValueError:
            _LOGGER.info("Catch an error")
        else:
            raise ValueError("Should catch an error here.")

    def testActionRun(self):
        _LOGGER.info("========== ErrorHandleItem-ActionRun ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        item.set_error("action_run", 1)
        item = ErrorHandleItem(item)
        _LOGGER.info("Ignore All Errors")
        item.set_ignore_all_errors(True)
        _LOGGER.info("action run")
        item.action_run()

    def testActionClear(self):
        _LOGGER.info("========== ErrorHandleItem-ActionClear ==========")
        # Can't ignore action_clear errors
        item = PlaceHolderItem("An Item", "Description ...")
        item.set_error("action_clear", 1)
        item = ErrorHandleItem(item)
        _LOGGER.info("Ignore All Error")
        item.set_ignore_all_errors(True)
        _LOGGER.info("action clear")
        try:
            item.action_clear()
        except ValueError:
            _LOGGER.info("Catch an error")
        else:
            raise ValueError("Should catch an error here.")

    def testUnnamedError(self):
        _LOGGER.info("========== ErrorHandleItem-UnnamedError ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        item.set_error("action_run", 4)
        item = ErrorHandleItem(item)
        _LOGGER.info("Ignore All Errors")
        item.set_ignore_all_errors(True)
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("Ignore Unnamed Errors")
        item.set_ignore_all_errors(False)
        item.set_ignore_unnamed_errors(True)
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("Ignore All and Unnamed Errors")
        item.set_ignore_all_errors(True)
        item.set_ignore_unnamed_errors(True)
        item.action_run()
        _LOGGER.info("Catch errors.")
        item.set_ignore_all_errors(False)
        item.set_ignore_unnamed_errors(False)
        _LOGGER.info("action run")
        try:
            item.action_run()
        except ErrorRecord:
            _LOGGER.info("Catch an error")
        else:
            raise ValueError("Should catch an error here.")

    def testNamedError(self):
        _LOGGER.info("========== ErrorHandleItem-NamedError ==========")
        record = ErrorRecord("ErrorType1", "Message ...", "An Error")
        item = PlaceHolderItem("An Item", "Description ...")
        item.set_error("action_run", 4, record)
        item = ErrorHandleItem(item)
        _LOGGER.info("Ignore All Errors")
        item.set_ignore_all_errors(True)
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("Ignore named Errors")
        item.set_ignore_all_errors(False)
        item.set_ignore_error("ErrorType1", True)
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("Ignore All and named Errors")
        item.set_ignore_all_errors(True)
        item.set_ignore_error("ErrorType1", True)
        item.action_run()
        _LOGGER.info("Catch errors.")
        item.set_ignore_all_errors(False)
        item.set_ignore_error("ErrorType1", False)
        _LOGGER.info("action run")
        try:
            item.action_run()
        except ErrorRecord:
            _LOGGER.info("Catch an error")
        else:
            raise ValueError("Should catch an error here.")

    def testErrorRecords(self):
        _LOGGER.info("========== ErrorHandleItem-ErrorRecords ==========")
        records = ErrorRecords()
        record = ErrorRecord("ErrorType1", "Message ...", "An Error")
        records.add_record(record)
        record = ErrorRecord("ErrorType2", "Message ...", "An Error")
        records.add_record(record)
        record = ErrorRecord("ErrorType3", "Message ...", "An Error")
        records.add_record(record)
        record = ErrorRecord("ErrorType4", "Message ...", "An Error")
        records.add_record(record)
        record = ErrorRecord("ErrorType5", "Message ...", "An Error")
        records.add_record(record)
        item = PlaceHolderItem("An Item", "Description ...")
        item.set_error("action_run", 5, records)
        item = ErrorHandleItem(item)
        _LOGGER.info("Ignore All Errors")
        item.set_ignore_all_errors(True)
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("Ignore named Errors")
        item.set_ignore_all_errors(False)
        item.set_ignore_error("ErrorType1", True)
        item.set_ignore_error("ErrorType2", True)
        item.set_ignore_error("ErrorType3", True)
        item.set_ignore_error("ErrorType4", True)
        item.set_ignore_error("ErrorType5", True)
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("Ignore All and named Errors")
        item.set_ignore_all_errors(True)
        item.set_ignore_error("ErrorType1", True)
        item.set_ignore_error("ErrorType2", True)
        item.set_ignore_error("ErrorType3", True)
        item.set_ignore_error("ErrorType4", True)
        item.set_ignore_error("ErrorType5", True)
        item.action_run()
        _LOGGER.info("Catch 5 errors.")
        item.set_ignore_all_errors(False)
        item.set_ignore_error("ErrorType1", False)
        item.set_ignore_error("ErrorType2", False)
        item.set_ignore_error("ErrorType3", False)
        item.set_ignore_error("ErrorType4", False)
        item.set_ignore_error("ErrorType5", False)
        _LOGGER.info("action run")
        try:
            item.action_run()
        except ErrorRecords, errs:
            _LOGGER.info("Catch %d errors", errs.size())
            assert errs.size() == 5
        else:
            raise ValueError("Should catch an error here.")

        _LOGGER.info("Catch 3 errors.")
        item.set_ignore_all_errors(True)
        item.set_ignore_error("ErrorType1", True)
        item.set_ignore_error("ErrorType2", False)
        item.set_ignore_error("ErrorType3", True)
        item.set_ignore_error("ErrorType4", False)
        item.set_ignore_error("ErrorType5", False)
        _LOGGER.info("action run")
        try:
            item.action_run()
        except ErrorRecords, errs:
            _LOGGER.info("Catch %d errors", errs.size())
            assert errs.size() == 3
        else:
            raise ValueError("Should catch an error here.")

    def testXML(self):
        _LOGGER.info("========== ErrorHandleItem-XML ==========")
        records = ErrorRecords()
        record = ErrorRecord("ErrorType1", "Message ...", "An Error")
        records.add_record(record)
        record = ErrorRecord("ErrorType2", "Message ...", "An Error")
        records.add_record(record)
        record = ErrorRecord("ErrorType3", "Message ...", "An Error")
        records.add_record(record)
        record = ErrorRecord("ErrorType4", "Message ...", "An Error")
        records.add_record(record)
        record = ErrorRecord("ErrorType5", "Message ...", "An Error")
        records.add_record(record)
        item = PlaceHolderItem("An Item", "Description ...")
        item.set_error("action_run", 5, records)
        item = ErrorHandleItem(item)
        xmlroot = None
        _LOGGER.info("Ignore All Errors")
        node_str = """
            <error-handle ignore_all_errors="true" ignore_unnamed_errors="true"/>
        """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("Ignore named Errors")
        node_str = """
            <error-handle ignore_all_errors="false">
                <error name="ErrorType1" ignore="true"/>
                <error name="ErrorType2" ignore="true"/>
                <error name="ErrorType3" ignore="true"/>
                <error name="ErrorType4" ignore="true"/>
                <error name="ErrorType5" ignore="true"/>
            </error-handle>
        """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        _LOGGER.info("action run")
        item.action_run()
        _LOGGER.info("Ignore All and named Errors")
        node_str = """
            <error-handle ignore_all_errors="true">
                <error name="ErrorType1" ignore="true"/>
                <error name="ErrorType2" ignore="true"/>
                <error name="ErrorType3" ignore="true"/>
                <error name="ErrorType4" ignore="true"/>
                <error name="ErrorType5" ignore="true"/>
            </error-handle>
        """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        item.action_run()
        _LOGGER.info("Catch 5 errors.")
        node_str = """
            <error-handle ignore_all_errors="false">
                <error name="ErrorType1" ignore="false"/>
                <error name="ErrorType2" ignore="false"/>
                <error name="ErrorType3" ignore="false"/>
                <error name="ErrorType4" ignore="false"/>
                <error name="ErrorType5" ignore="false"/>
            </error-handle>
        """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        _LOGGER.info("action run")
        try:
            item.action_run()
        except ErrorRecords, errs:
            _LOGGER.info("Catch %d errors", errs.size())
            assert errs.size() == 5
        else:
            raise ValueError("Should catch an error here.")

        _LOGGER.info("Catch 3 errors.")
        node_str = """
            <error-handle ignore_all_errors="true">
                <error name="ErrorType1" ignore="true"/>
                <error name="ErrorType2" ignore="false"/>
                <error name="ErrorType3" ignore="true"/>
                <error name="ErrorType4" ignore="false"/>
                <error name="ErrorType5" ignore="false"/>
            </error-handle>
        """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        _LOGGER.info("action run")
        try:
            item.action_run()
        except ErrorRecords, errs:
            _LOGGER.info("Catch %d errors", errs.size())
            assert errs.size() == 3
        else:
            raise ValueError("Should catch an error here.")

class LogEOTC(unittest.TestCase):
    def testTisLogEO(self):
        _LOGGER.info("========== TisLogEO ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        eo = TisLogEO(item)
        eo.update()

    def testTiesLogEO(self):
        _LOGGER.info("========== TiesLogEO ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        eo = TiesLogEO(item)
        eo.update()

    def testTiefLogEO(self):
        _LOGGER.info("========== TiefLogEO ==========")
        item = PlaceHolderItem("An Item", "Description ...")
        eo = TiefLogEO(item)
        eo.update()
        

if __name__ == "__main__":
    log.config()
    unittest.main()
    #logger = log.getLogger()
    #print logger.root.name


