#! /usr/bin/python

import unittest
import sys
sys.path.append("../../pycat")
import log
_LOGGER = log.getLogger("cat.testcmdexec")

from cmdexec import *

class ErrorFilterTestCase(unittest.TestCase):
    def testKeywordErrorFilter(self):
        _LOGGER.info("========== KeywordErrorFilter ==========")
        data = "abcdefghijklmn"
        ef1 = KeywordErrorFilter("find", "abc")
        ef2 = KeywordErrorFilter("find", "xyz")
        ef3 = KeywordErrorFilter("not-find", "abc")
        ef4 = KeywordErrorFilter("not-find", "xyz")
        _LOGGER.info("Data: %s", data)
        ef1.show()
        try:
            ef1.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef2.show()
        try:
            ef2.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef3.show()
        try:
            ef3.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef4.show()
        try:
            ef4.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

    def testErrorFilterSet(self):
        _LOGGER.info("========== ErrorFilterSet ==========")
        data = "abcdefghijklmn"
        efset = ErrorFilterSet()
        ef1 = KeywordErrorFilter("find", "abc")
        ef2 = KeywordErrorFilter("find", "xyz")
        ef3 = KeywordErrorFilter("not-find", "abc")
        ef4 = KeywordErrorFilter("not-find", "xyz")
        efset.add_filter(ef1)
        efset.add_filter(ef2)
        efset.add_filter(ef3)
        efset.add_filter(ef4)
        _LOGGER.info(efset)
        efset.show()
        efset.remove_filter(ef1)
        _LOGGER.info(efset)
        efset.show()
        try:
            efset.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

    def testLineNumErrorFilter(self):
        _LOGGER.info("========== LineNumErrorFilter ==========")
        data = """line 1
                   line 2
                   line 3
                   line 4
                   line 5"""
        ef11 = LineNumErrorFilter("less-than", 6)
        ef12 = LineNumErrorFilter("less-than", 4)
        ef21 = LineNumErrorFilter("less-equal", 6)
        ef22 = LineNumErrorFilter("less-equal", 5)
        ef31 = LineNumErrorFilter("equal", 5)
        ef32 = LineNumErrorFilter("equal", 2)
        ef41 = LineNumErrorFilter("not-equal", 5)
        ef42 = LineNumErrorFilter("not-equal", 2)
        ef51 = LineNumErrorFilter("greater-equal", 5)
        ef52 = LineNumErrorFilter("greater-equal", 6)
        ef61 = LineNumErrorFilter("greater-than", 4)
        ef62 = LineNumErrorFilter("greater-than", 6)
        _LOGGER.info("Data: 5 lines")
        ef11.show()
        try:
            ef11.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef12.show()
        try:
            ef12.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef21.show()
        try:
            ef21.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef22.show()
        try:
            ef22.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef31.show()
        try:
            ef31.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef32.show()
        try:
            ef32.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef41.show()
        try:
            ef41.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef42.show()
        try:
            ef42.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef51.show()
        try:
            ef51.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef52.show()
        try:
            ef52.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef61.show()
        try:
            ef61.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef62.show()
        try:
            ef62.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

    def testDataSizeErrorFilter(self):
        _LOGGER.info("========== DataSizeErrorFilter ==========")
        data = "12345"
        ef11 = DataSizeErrorFilter("less-than", 6)
        ef12 = DataSizeErrorFilter("less-than", 4)
        ef21 = DataSizeErrorFilter("less-equal", 6)
        ef22 = DataSizeErrorFilter("less-equal", 5)
        ef31 = DataSizeErrorFilter("equal", 5)
        ef32 = DataSizeErrorFilter("equal", 2)
        ef41 = DataSizeErrorFilter("not-equal", 5)
        ef42 = DataSizeErrorFilter("not-equal", 2)
        ef51 = DataSizeErrorFilter("greater-equal", 5)
        ef52 = DataSizeErrorFilter("greater-equal", 6)
        ef61 = DataSizeErrorFilter("greater-than", 4)
        ef62 = DataSizeErrorFilter("greater-than", 6)
        _LOGGER.info("Data:")
        _LOGGER.info(data)
        ef11.show()
        try:
            ef11.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef12.show()
        try:
            ef12.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef21.show()
        try:
            ef21.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef22.show()
        try:
            ef22.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef31.show()
        try:
            ef31.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef32.show()
        try:
            ef32.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef41.show()
        try:
            ef41.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef42.show()
        try:
            ef42.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef51.show()
        try:
            ef51.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef52.show()
        try:
            ef52.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef61.show()
        try:
            ef61.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

        ef62.show()
        try:
            ef62.filter(data)
        except ValueError, err:
            _LOGGER.warning(err)
        else:
            _LOGGER.info("ErrorFilter dismatch")

    def testErrorFilterFactory(self):
        _LOGGER.info("========== ErrorFilterFactory ==========")
        factory =  ErrorFilterFactory()
        ef1 = factory.create_filter("key-word", "find", "abc")
        ef2 = factory.create_filter("data-size", "less-than", "5")
        ef3 = factory.create_filter("line-number", "greater-than", "10")
        efset = ErrorFilterSet()
        efset.add_filter(ef1)
        efset.add_filter(ef2)
        efset.add_filter(ef3)
        efset.show()

class ValueFilterTestCase(unittest.TestCase):
    def testLineFilter(self):
        _LOGGER.info("========== LineFilter ==========")
        data = "line 1 abc def\nghi line 2 jkl\nmno line 3 pqr\nghi line 4 jkl\nstu line 5 vwx\nmno line 6 pqr\nabc line 7 yz\nline 8 qwe wer\nline 9 dfg ghj"
        vf1 = LineFilter("remove-line-start-with-keyword", "abc")
        vf2 = LineFilter("remove-line-start-with-keyword", "ghi")
        vf3 = LineFilter("remove-line-start-with-keyword", "line 8")
        vf4 = LineFilter("remove-line-include-keyword", "pqr")
        vf5 = LineFilter("remove-line-include-keyword", "dfg ghj")
        _LOGGER.info("Data: %s", data)
        vf1.show()
        data = vf1.filter(data)
        _LOGGER.info("Data: %s", data)
        vf2.show()
        data = vf2.filter(data)
        _LOGGER.info("Data: %s", data)
        vf3.show()
        data = vf3.filter(data)
        _LOGGER.info("Data: %s", data)
        vf4.show()
        data = vf4.filter(data)
        _LOGGER.info("Data: %s", data)
        vf5.show()
        data = vf5.filter(data)
        _LOGGER.info("Data: %s", data)

    def testValueFilterSet(self):
        _LOGGER.info("========== ValueFilterSet ==========")
        data = "line 1 abc def\nghi line 2 jkl\nmno line 3 pqr\nghi line 4 jkl\nstu line 5 vwx\nmno line 6 pqr\nabc line 7 yz"
        vfset = ValueFilterSet()
        vf11 = LineFilter("remove-line-start-with-keyword", "abc")
        vf12 = LineFilter("remove-line-start-with-keyword", "ghi")
        vf21 = LineFilter("remove-line-include-keyword", "pqr")
        vfset.add_filter(vf11)
        vfset.add_filter(vf12)
        vfset.add_filter(vf21)
        _LOGGER.info("Data: %s", data)
        vfset.show()
        data = vfset.filter(data)
        _LOGGER.info("Data: %s", data)

    def testValueFilterFactory(self):
        _LOGGER.info("========== ValueFilterFactory ==========")
        factory = ValueFilterFactory()
        vf1 = factory.create_filter("line-filter", "remove-line-start-with-keyword", "abc")
        vf1.show()

class CommandExecutor(unittest.TestCase):
    def testCommandLocalViaSystem(self):
        _LOGGER.info("========== CommandLocalViaSystem ==========")
        cmd = CommandLocalViaSystem("ifconfig -a")
        _LOGGER.info(cmd)
        cmd.show()
        ret = cmd()

    def testCommandLocalViaPopen(self):
        _LOGGER.info("========== CommandLocalViaPopen ==========")
        cmd = CommandLocalViaPopen(["ifconfig", "-a"])
        _LOGGER.info(cmd)
        cmd.show()
        ret = cmd()
        cmd = CommandLocalViaPopen("./cmd.sh", ["a", "b", "c"])
        _LOGGER.info(cmd)
        cmd.show()
        ret = cmd()

    def testCommandSSH(self):
        _LOGGER.info("========== CommandSSH ==========")
        cmd = CommandSSH(["ifconfig", "-a"], host="127.0.0.1", user="root", passwd="qwe123")
        _LOGGER.info(cmd)
        cmd.show()
        ret = cmd()
        cmd = CommandSSH(["/media/sf_E_DRIVE/SVN/diag/branches/pycat/test/core/cmd.sh", "-a"], host="127.0.0.1", user="root", passwd="qwe123", user_input=["x", "y", "z"])
        _LOGGER.info(cmd)
        cmd.show()
        ret = cmd()

    def testCommandUart(self):
        _LOGGER.info("========== CommandUart ==========")
        cmd = CommandUart(["help"], port="/dev/ttyUSB0", baudrate="115200")
        _LOGGER.info(cmd)
        cmd.show()
        #ret = cmd()
        CommandUart.set_global_endmarks("0000:0000")
        CommandUart.set_global_end_of_line("CR")
        cmd2 = CommandUart("seeprom", port="/dev/ttyUSB0", baudrate=115200)
        cmd.show()
        cmd2.show()

if __name__ == "__main__":
    log.config()
    unittest.main()
