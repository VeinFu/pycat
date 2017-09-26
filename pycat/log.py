#! /usr/bin/python

"""
Root logger's name of all CATLogger instance.
"""

import logging
from logging import LogRecord
from logging import Logger
from logging import getLogger

ROOT_NAME = "log"

class CATLogRecord(LogRecord):
    """
    A CATLogRecord instance represents an event being logged.

    The CATLogRecord class inherits from LogRecord. It adds 'cycle' and 'item'
    attributes.
    """
    def __init__(self, name, level, pathname, lineno,
                 msg, args, exc_info, func=None, item=None, cycle=None, stage=None, process=None):
        LogRecord.__init__(self,  name, level, pathname, lineno,
                 msg, args, exc_info, func=None)
        self.cycle = cycle
        self.item = item
        self.stage = stage
        self.process = process

class CATLogger(Logger):
    """
    The CATLogger class inherits from Logger. It replaces the 'makeRecord'
    method to create a CATLogRecord instance. 
    The 'cycle' and 'item' attribute of a CATLogger instance inherits from its
    parents when they are creating. The methods 'setCycle' and 'setItem' modify
    a instance's attributes and its children attributes.
    For example, if a logger named 'loggerA' set its 'cycle' to '1', all its
    children's 'cycle's are set to '1', including 'loggerA.childA',
    'loggerA.childB', 'loggerA.childB.gchildA', etc.
    """
    def __init__(self, name, level=logging.NOTSET):
        Logger.__init__(self, name, level)
        self.item = self._findParentAttri("item")
        self.cycle = self._findParentAttri("cycle")
        self.stage = self._findParentAttri("stage")
        self.process = self._findParentAttri("process")

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info,
                   func=None, extra=None):
        """
        Replace Logger's makeRecord to create a CATLogRecord instance.
        """
        rv = CATLogRecord(name, level, fn, lno, msg, args, exc_info, func,
                          self.item, self.cycle, self.stage, self.process)
        if extra is not None:
            for key in extra:
                if (key in ["message", "asctime"]) or (key in rv.__dict__):
                    raise KeyError("Attempt to overwrite %r in LogRecord" % key)
                rv.__dict__[key] = extra[key]
        return rv

    def setItem(self, item):
        """
        Set a CATLogger and all its children's 'item' attribute.
        """
        if isinstance(item, basestring):
            self.item = item
        self._setChildrenAttri("item", self.item)

    def setCycle(self, cycle):
        """
        Set a CATLogger and all its children's 'cycle' attribute.
        """
        if isinstance(cycle, basestring):
            self.cycle = cycle
        self._setChildrenAttri("cycle", self.cycle)

    def setStage(self, stage):
        """
        Set a CATLogger and all its children's 'stage' attribute.
        """
        if isinstance(stage, basestring):
            self.stage = stage
        self._setChildrenAttri("stage", self.stage)


    def setProcess(self, process):
        """
        Set a CATLogger and all its children's 'process' attribute.
        """
        if isinstance(process, basestring):
            self.process = process
        self._setChildrenAttri("process", self.process)

    def _findParentAttri(self, attri):
        """
        Find the attribute of a CATLogger's parent.
        """
        name = self.name
        value = None
        while (ROOT_NAME != name) and (self.root.name != name):
            if name.find('.') == -1:
                break
            parent_name = name.rsplit('.', 1)[0]
            parent = self.manager.getLogger(parent_name)
            try:
                rv = parent.__dict__[attri]
            except (KeyError, TypeError):
                rv = None
            if rv != None:
                value = rv
                break
            else:
                name = parent_name
        return value

    def _setChildrenAttri(self, attri, value):
        """
        Set the attribute of a CATLogger's children.
        """
        for key in self.manager.loggerDict:
            ops = key.find(self.name)
            if ops == 0 and key != self.name:
                child = self.manager.getLogger(key)
                try:
                    child.__dict__[attri] = value
                except KeyError:
                    pass

# Set Logger class before any loggers are created.
logging.setLoggerClass(CATLogger)

def config(**kwargs):
    """
    Do configuration for catlog.
    Optional keywords:
    filename  Specifies that a FileHandler be created.
    filemode  Specifies the mode to open the file, if filename is specified
              (if filemode is unspecified, it defaults to 'a').
    level     Set the root logger level to the specified level.
    """
    # fmt = logging.Formatter("[%(asctime)s][%(levelname)-7s][%(name)-15s][%(process)-10s][%(stage)-10s][%(cycle)-10s][%(item)-15s] %(message)s")
    fmt = logging.Formatter("[%(asctime)s][%(levelname)-7s][%(cycle)-10s][%(item)-15s] %(message)s")
    filename = kwargs.get("filename")
    if filename:
        mode = kwargs.get("filemode", "a")
        hdlr = logging.FileHandler(filename, mode)
    else:
        hdlr = logging.StreamHandler()
    hdlr.setFormatter(fmt)
    root_logger = logging.getLogger(ROOT_NAME)
    root_logger.addHandler(hdlr)
    level = kwargs.get("level", logging.DEBUG)
    root_logger.setLevel(level)

