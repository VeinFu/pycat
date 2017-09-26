#! /usr/bin/python

import sys
import logging
import unittest
import xml.etree.ElementTree as ET

sys.path.append('../../pycat/common/')
import log
import config
from config import *

class ConfigTestCase(unittest.TestCase):
    def XtestSysConfig(self):
        logger = log.getLogger("cat.SysConf")
        logger.info("========== SysConfig ==========")
        sysconfig = SysConfig()
        logger.info("Dir: %s", sysconfig.get_sysconfig_dir())
        logger.info("Full path: %s", sysconfig.get_sysconfig())
        
    def XtestCache(self):
        logger = log.getLogger("cat.Cache")
        logger.info("========== Cache ==========")
        cache = Cache()
        cache.append("/media/sf_E_DRIVE/SVN/branch_wilson/pycat/test/common/etc")
        for item in cache.get_cache():
            logger.info("%s", item)
        cache.remove("/media/sf_E_DRIVE/SVN/branch_wilson/pycat/test/common/etc")
        cache.append("/media/sf_E_DRIVE/SVN/branch_wilson/pycat/test/common/etc/pycat")
        for item in cache.get_cache():
            logger.info("%s", item)

    def XtestTestCaseConfig(self):
        logger = log.getLogger("cat.TCConf")
        logger.info("========== TestCaseConfig ==========")
        cache = Cache()
        cache.append("/media/sf_E_DRIVE/SVN/branch_wilson/pycat/test/common/cache")
        config = TestCaseConfig("/media/sf_E_DRIVE/SVN/branch_wilson/pycat/test/common/cache/session/session-1/fw-program-default.xml")

    def testPlugin(self):
        logger = log.getLogger("cat.Plugin")
        logger.info("========== Plugin ==========")
        plugin = Plugin()
        plugin.install("/media/sf_E_DRIVE/SVN/branch_wilson/pycat-plugins/Tabasco-DVT-0.0.2.tar.gz")

if __name__ == "__main__":
    log.config()
    unittest.main()

