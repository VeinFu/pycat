#! /usr/bin/python

import unittest
import sys
import xml.etree.ElementTree as ET
sys.path.append("../..")
sys.path.append("../../pycat")
import log
_LOGGER = log.getLogger("log.test")

from item import *

class TestItemTC(unittest.TestCase):
    def testEvents(self):
        _LOGGER.info("========== TestItem - Events ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="all">
                <desc value="A log description ....."/>
                <predelay value="PT5S"/>
                <repeat value="5" interval="PT5S"/>
                <retry value="5" interval="PT5S"/>
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
                <delay value="PT5S"/>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        item.show()

    def testInit(self):
        _LOGGER.info("========== TestItem - Init ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="all">
                <desc value="A log description ....."/>
                <predelay value="PT5S"/>
                <repeat value="5" interval="PT5S"/>
                <retry value="5" interval="PT5S"/>
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
                <delay value="PT5S"/>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        item.action_init()



    def testPredelay(self):
        _LOGGER.info("========== TestItem - Predelay ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="predelay">
                <desc value="A log description ....."/>
                <predelay value="PT5S"/>
                <place-holder/>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        item.action_init()
        item.action_run()
        item.action_clear()

    def testDelay(self):
        _LOGGER.info("========== TestItem - Delay ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="delay">
                <desc value="A log description ....."/>
                <delay value="PT5S"/>
                <place-holder/>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        item.action_init()
        item.action_run()
        item.action_clear()

    def testRepeatWithInterval(self):
        _LOGGER.info("========== TestItem - Repeat with interval ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="repeat">
                <desc value="A log description ....."/>
                <repeat value="5" interval="PT5S"/>
                <place-holder/>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        item.action_init()
        item.action_run()
        item.action_clear()

    def testRepeatWithoutInterval(self):
        _LOGGER.info("========== TestItem - Repeat without interval ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="repeat">
                <desc value="A log description ....."/>
                <repeat value="5"/>
                <place-holder/>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        item.action_init()
        item.action_run()
        item.action_clear()

    def testRetryInit(self):
        _LOGGER.info("========== TestItem - Retry Init ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="retry">
                <desc value="A log description ....."/>
                <retry value="5" interval="PT5S"/>
                <place-holder ierror="1">
                    <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                    <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                    <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
                </place-holder>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        try:
            item.action_init()
        except TestItemError, err:
            _LOGGER.info("Catch an error.")
        else:
            _LOGGER.error("Should catch an error.")

    def testRetryClear(self):
        _LOGGER.info("========== TestItem - Retry Clear ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="retry">
                <desc value="A log description ....."/>
                <retry value="5" interval="PT5S"/>
                <place-holder cerror="1">
                    <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                    <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                    <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
                </place-holder>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        try:
            item.action_clear()
        except TestItemError, err:
            _LOGGER.info("Catch an error.")
        else:
            _LOGGER.error("Should catch an error.")

    def testRetryWithInterval(self):
        _LOGGER.info("========== TestItem - Retry With Interval ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="retry">
                <desc value="A log description ....."/>
                <retry value="5" interval="PT5S"/>
                <place-holder rerror="5">
                    <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                    <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                    <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
                </place-holder>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        item.action_run()

    def testRetryWithoutInterval(self):
        _LOGGER.info("========== TestItem - Retry Without Interval ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="retry">
                <desc value="A log description ....."/>
                <retry value="5"/>
                <place-holder rerror="5">
                    <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                    <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                    <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
                </place-holder>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        item.action_run()

    def testRetryFail(self):
        _LOGGER.info("========== TestItem - Retry Fail ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="retry">
                <desc value="A log description ....."/>
                <retry value="3"/>
                <place-holder rerror="5">
                    <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                    <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                    <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
                </place-holder>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        try:
            item.action_run()
        except TestItemError, err:
            _LOGGER.info("Catch an error.")
        else:
            _LOGGER.error("Should catch an error.")

    def testErrorHandleInit(self):
        _LOGGER.info("========== TestItem - ErrorHandle Init ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="error-handle">
                <desc value="A log description ....."/>
                <error-handle ignore_all_errors="true" ignore_unnamed_errors="true">
                    <error name="ErrorType1" ignore="true"/>
                    <error name="ErrorType2" ignore="true"/>
                    <error name="ErrorType3" ignore="true"/>
                </error-handle>
                <place-holder ierror="1">
                    <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                    <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                    <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
                </place-holder>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        try:
            item.action_init()
        except TestItemError, err:
            _LOGGER.info("Catch an error.")
        else:
            _LOGGER.error("Should catch an error.")

    def testErrorHandleClear(self):
        _LOGGER.info("========== TestItem - ErrorHandle Clear ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="error-handle">
                <desc value="A log description ....."/>
                <error-handle ignore_all_errors="true" ignore_unnamed_errors="true">
                    <error name="ErrorType1" ignore="true"/>
                    <error name="ErrorType2" ignore="true"/>
                    <error name="ErrorType3" ignore="true"/>
                </error-handle>
                <place-holder cerror="1">
                    <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                    <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                    <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
                </place-holder>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        try:
            item.action_clear()
        except TestItemError, err:
            _LOGGER.info("Catch an error.")
        else:
            _LOGGER.error("Should catch an error.")

    def testErrorHandleSucc(self):
        _LOGGER.info("========== TestItem - ErrorHandle Succ ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="error-handle">
                <desc value="A log description ....."/>
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
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        item.action_run()

    def testErrorHandleFail(self):
        _LOGGER.info("========== TestItem - ErrorHandle Fail ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="error-handle">
                <desc value="A log description ....."/>
                <error-handle>
                    <error name="ErrorType1" ignore="true"/>
                    <error name="ErrorType3" ignore="true"/>
                </error-handle>
                <place-holder rerror="5">
                    <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                    <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                    <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
                </place-holder>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        try:
            item.action_run()
        except TestItemError, err:
            _LOGGER.info("Catch an error.")
        else:
            _LOGGER.error("Should catch an error.")

    def testAllSuccNoretry(self):
        _LOGGER.info("========== TestItem - All Succ -No Retry ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="all">
                <desc value="A log description ....."/>
                <predelay value="PT5S"/>
                <repeat value="5" interval="PT5S"/>
                <retry value="5" interval="PT5S"/>
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
                <delay value="PT5S"/>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        item.action_init()
        item.action_run()
        item.action_clear()

    def testAllSuccRetry(self):
        _LOGGER.info("========== TestItem - All Succ - Retry ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="all">
                <desc value="A log description ....."/>
                <predelay value="PT5S"/>
                <repeat value="5" interval="PT5S"/>
                <retry value="5"/>
                <error-handle>
                    <error name="ErrorType1" ignore="true"/>
                    <error name="ErrorType3" ignore="true"/>
                </error-handle>
                <place-holder rerror="5">
                    <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                    <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                    <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
                </place-holder>
                <delay value="PT5S"/>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        item.action_init()
        item.action_run()
        item.action_clear()

    def testAllInit(self):
        _LOGGER.info("========== TestItem - All - Init ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="all">
                <desc value="A log description ....."/>
                <predelay value="PT5S"/>
                <repeat value="5" interval="PT5S"/>
                <retry value="5" interval="PT5S"/>
                <error-handle>
                    <error name="ErrorType1" ignore="true"/>
                    <error name="ErrorType3" ignore="true"/>
                </error-handle>
                <place-holder ierror="5">
                    <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                    <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                    <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
                </place-holder>
                <delay value="PT5S"/>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        try:
            item.action_init()
        except TestItemError, err:
            _LOGGER.info("Catch an error.")
        else:
            _LOGGER.error("Should catch an error.")

    def testAllClear(self):
        _LOGGER.info("========== TestItem - All - Clear ==========")
        item = TestItem()
        xmlroot = None
        node_str = """
            <item type="place-holder" name="all">
                <desc value="A log description ....."/>
                <predelay value="PT5S"/>
                <repeat value="5" interval="PT5S"/>
                <retry value="5" interval="PT5S"/>
                <error-handle>
                    <error name="ErrorType1" ignore="true"/>
                    <error name="ErrorType3" ignore="true"/>
                </error-handle>
                <place-holder cerror="5">
                    <error name="ErrorType1" message="Error message ..." description="An ErrorType1 Instance"/>
                    <error name="ErrorType2" message="Error message ..." description="An ErrorType2 Instance"/>
                    <error name="ErrorType3" message="Error message ..." description="An ErrorType3 Instance"/>
                </place-holder>
                <delay value="PT5S"/>
            </item> """
        node = ET.fromstring(node_str)
        item.xml_interpret(xmlroot, node)
        try:
            item.action_clear()
        except TestItemError, err:
            _LOGGER.info("Catch an error.")
        else:
            _LOGGER.error("Should catch an error.")




if __name__ == "__main__":
    log.config()
    unittest.main()


