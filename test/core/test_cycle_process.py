#! /usr/bin/python

import unittest
import sys
import xml.etree.ElementTree as ET
sys.path.append("../..")
sys.path.append("../../pycat")
import log
_LOGGER = log.getLogger("log.test")

from item import *

PROCESS_STR = """
    <cycle-process name="Test" cycle_total="3" ignore_error="False">
        <item type="place-holder" name="item-1">
            <desc value="Execute item-1"/>
            <place-holder/>
        </item> 
        <item type="place-holder" name="item-2">
            <desc value="Execute item-2"/>
            <repeat value="2"/>
            <retry value="2"/>
            <error-handle>
                <error name="ErrorType1" ignore="true"/>
                <error name="ErrorType3" ignore="true"/>
            </error-handle>
            <place-holder rerror="2">
                <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
            </place-holder>
        </item> 
        <item type="place-holder" name="item-3">
            <desc value="Execute item-3"/>
            <predelay value="PT1S"/>
            <error-handle>
                <error name="ErrorType1" ignore="true"/>
                <error name="ErrorType2" ignore="true"/>
                <error name="ErrorType3" ignore="true"/>
            </error-handle>
            <place-holder rerror="5">
                <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
            </place-holder>
            <delay value="PT1S"/>
        </item> 
    </cycle-process>"""

PROCESS_FAIL_STR = """
    <cycle-process name="Test" cycle_total="3">
        <item type="place-holder" name="item-1">
            <desc value="Execute item-1"/>
            <place-holder/>
        </item> 
        <item type="place-holder" name="item-2">
            <desc value="Execute item-2"/>
            <repeat value="2"/>
            <retry value="2"/>
            <error-handle>
                <error name="ErrorType1" ignore="true"/>
                <error name="ErrorType3" ignore="true"/>
            </error-handle>
            <place-holder rerror="3">
                <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
            </place-holder>
        </item> 
        <item type="place-holder" name="item-3">
            <desc value="Execute item-3"/>
            <predelay value="PT1S"/>
            <error-handle>
                <error name="ErrorType1" ignore="true"/>
                <error name="ErrorType2" ignore="true"/>
                <error name="ErrorType3" ignore="true"/>
            </error-handle>
            <place-holder rerror="5">
                <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
            </place-holder>
            <delay value="PT1S"/>
        </item> 
    </cycle-process>"""

class TestCycleProcessTC(unittest.TestCase):
    def XtestShow(self):
        _LOGGER.info("========== CycleProcess - Show ==========")
        process = CycleProcess()
        xmlroot = None
        node = ET.fromstring(PROCESS_STR)
        process.xml_interpret(xmlroot, node)
        process.show()

    def XtestAPI(self):
        _LOGGER.info("========== CycleProcess - API ==========")
        process = CycleProcess()
        xmlroot = None
        node = ET.fromstring(PROCESS_STR)
        process.xml_interpret(xmlroot, node)
        _LOGGER.info("Process Name: %s", process.get_name())
        _LOGGER.info("Modify Name")
        process.set_name("new-process")
        _LOGGER.info("Process Name: %s", process.get_name())
        
        _LOGGER.info("IgnoreError : %s", process.get_ignore_error())
        _LOGGER.info("Modify IgnoreError")
        process.set_ignore_error(True)
        _LOGGER.info("IgnoreError: %s", process.get_ignore_error())
        _LOGGER.info("CompletionPercentage: %d%%", 100*process.get_completion_percentage())

        _LOGGER.info("TotalCycle: %s", process.get_total_cycle())
        _LOGGER.info("Modify TotalCycle")
        process.set_total_cycle(100)
        _LOGGER.info("TotalCycle: %s", process.get_total_cycle())

    def XtestInit(self):
        _LOGGER.info("========== CycleProcess - Init ==========")
        process = CycleProcess()
        xmlroot = None
        node = ET.fromstring(PROCESS_STR)
        process.xml_interpret(xmlroot, node)
        process.action_init()

    def XtestClear(self):
        _LOGGER.info("========== CycleProcess - Clear ==========")
        process = CycleProcess()
        xmlroot = None
        node = ET.fromstring(PROCESS_STR)
        process.xml_interpret(xmlroot, node)
        process.action_clear()

    def XtestRunSucc(self):
        _LOGGER.info("========== CycleProcess - Run -Succ ==========")
        process = CycleProcess()
        xmlroot = None
        node = ET.fromstring(PROCESS_STR)
        process.xml_interpret(xmlroot, node)
        process.action_run()

    def testRunFail(self):
        _LOGGER.info("========== CycleProcess - Run -Fail ==========")
        process = CycleProcess()
        xmlroot = None
        node = ET.fromstring(PROCESS_FAIL_STR)
        process.xml_interpret(xmlroot, node)
        try:
            process.action_run()
        except ProcessError:
            _LOGGER.info("Catch a process error")
        else:
            raise ValueError("Should catch a process error")


if __name__ == "__main__":
    log.config()
    unittest.main()


