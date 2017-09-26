#! /usr/bin/python

import sys
import logging
import unittest
import xml.etree.ElementTree as ET

sys.path.append('../../pycat/common/')
sys.path.append('../../../pycat-plugins/Tabasco-DVT/')
import log
import config
from config import *
import FWProgram

class FWProgramTestCase(unittest.TestCase):
    def testTestCaseConfig(self):
        print "========== FW Program =========="
        cache = Cache()
        cache.append("/media/sf_E_DRIVE/SVN/branch_wilson/pycat/test/common/cache")
        config = "/media/sf_E_DRIVE/SVN/branch_wilson/pycat/test/common/cache/session/session-1/fw-program-default.xml"
        tc = FWProgram.FirmwareProgramTestCase(config)
        tc.perform_process()

if __name__ == "__main__":
    log.config()
    unittest.main()

