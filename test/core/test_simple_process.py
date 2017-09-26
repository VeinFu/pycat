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
    <simple-process name="SetUpEnv" ignore_error="False">
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
    </simple-process>"""

PROCESS_FAIL_STR = """
    <simple-process name="SetUpEnv">
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
    </simple-process>"""

class TestSimpleProcessTC(unittest.TestCase):
    def testShow(self):
        _LOGGER.info("========== SimpleProcess - Show ==========")
        process = SimpleProcess()
        xmlroot = None
        node = ET.fromstring(PROCESS_STR)
        process.xml_interpret(xmlroot, node)
        process.show()

    def testAPI(self):
        _LOGGER.info("========== SimpleProcess - API ==========")
        process = SimpleProcess()
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

    def testInit(self):
        _LOGGER.info("========== SimpleProcess - Init ==========")
        process = SimpleProcess()
        xmlroot = None
        node = ET.fromstring(PROCESS_STR)
        process.xml_interpret(xmlroot, node)
        process.action_init()

    def testClear(self):
        _LOGGER.info("========== SimpleProcess - Clear ==========")
        process = SimpleProcess()
        xmlroot = None
        node = ET.fromstring(PROCESS_STR)
        process.xml_interpret(xmlroot, node)
        process.action_clear()

    def testRunSucc(self):
        _LOGGER.info("========== SimpleProcess - Run -Succ ==========")
        process = SimpleProcess()
        xmlroot = None
        node = ET.fromstring(PROCESS_STR)
        process.xml_interpret(xmlroot, node)
        process.action_run()

    def testRunFail(self):
        _LOGGER.info("========== SimpleProcess - Run -Fail ==========")
        process = SimpleProcess()
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


