#! /usr/bin/python

"""
Command Executor Module

This module supplies classes and functions to execute commands on localhost,
though UART or thuogh SSH, etc. It also has a error filter and value filter
mechanism to check the result of commands.
"""

import re
import tempfile
import os
import subprocess, shlex
import paramiko
import time
import log
import serial
# _LOGGER = log.getLogger("log.cmdexec")
# _LOGGER_RAW = log.getLogger("log.rawdata")

_LOGGER = log.getLogger("log.tc")
_LOGGER_RAW = log.getLogger("log.tc")

#--------------------------------------------------------------------------
#    Error Filter
#--------------------------------------------------------------------------
class ErrorFilter(object):
    """
    An ErrorFilter instance checks data to determine whether the data are
    valid.
    """
    def __init__(self, action=None, args=None):
        pass

    def __str__(self):
        return "Unknown ErrorFilter"

    def filter(self, data):
        """
        The method of filter data. The children of ErrorFilter should
        implement this method.
        If the condition is satisfied, an error happened. This method
        should raise an ValueError.

        data: Must be a string.
        """
        raise NotImplementedError

    def show(self):
        """
        Print self information to the log.
        """
        _LOGGER.warning("Unknown ErrorFilter")

class ErrorFilterSet(ErrorFilter):
    """
    An ErrorFilterSet is a list of ErrorFilter.
    """
    def __init__(self):
        ErrorFilter.__init__(self)
        self.filters = []

    def __str__(self):
        ret = "["
        for fil in self.filters:
            ret += str(fil) + ","
        ret = ret[:-1] + "]"
        return ret

    def add_filter(self, efilter):
        """
        Add an ErrorFilter instance.
        """
        if not (efilter in self.filters):
            self.filters.append(efilter)

    def remove_filter(self, efilter):
        """
        remove an ErrorFilter instance.
        """
        if efilter in self.filters:
            self.filters.remove(efilter)

    def filter(self, data):
        """
        Call all ErrorFilter instance in the list one by one.
        """
        match = False
        for efilter in self.filters:
            try:
                efilter.filter(data)
            except ValueError, err:
                match = True
                _LOGGER.error(err)
            else:
                _LOGGER.debug("%s dismatch", efilter)
        if match:
            raise ValueError

    def show(self):
        """
        Print self information into the log.
        """
        _LOGGER.info("ErrorFilterSet:")
        for fil in self.filters:
            fil.show()

class KeywordErrorFilter(ErrorFilter):
    """
    A KeywordErrorFilter instance search a keyword in the data to determine
    whether the data are valid.

    action:
       * find: If the keyword is found in the data, the data are invalid and
               raise an ValueError.
       * not-find: If the keyword isn't found in the data, the data are
                   invalid and raise an ValueError.
    keyword:
       The keyword is used to search in the data. It must be a string.
    """
    def __init__(self, action, keyword):
        ErrorFilter.__init__(self)
        self.filter_func = {"find": self.find_keyword,
                            "not-find": self.not_find_keyword}
        if action in self.filter_func.keys():
            self.action = action
        else:
            raise KeyError("Unknown action '%s'." % (action))
        if isinstance(keyword, str):
            self.keyword = keyword
        else:
            raise ValueError("Keyword must be a string.")

    def __str__(self):
        ret = "KeywordErrorFilter(%s '%s')" % (self.action, self.keyword)
        return ret

    def find_keyword(self, data):
        """
        If the keyword is found in the data, raise a ValueError.
        """
        lines = data.split('\n')
        for line in lines:
            sret = re.search(self.keyword, line)
            if sret != None:
                raise ValueError("Find keyword '%s'" % (self.keyword))

    def not_find_keyword(self, data):
        """
        If the keyword isn't found in the data, raise a ValueError.
        """
        lines = data.split('\n')
        find_keyword = False
        for line in lines:
            sret = re.search(self.keyword, line)
            if sret != None:
                find_keyword = True
        if find_keyword == False:
            raise ValueError("Can't find keyword '%s'" % (self.keyword))

    def filter(self, data):
        """
        Execute the filter function.
        """
        self.filter_func[self.action](data)

    def show(self):
        """
        Print self information to the log.
        """
        _LOGGER.info("KeywordErrorFilter: %s '%s'",
            self.action, self.keyword)

class LineNumErrorFilter(ErrorFilter):
    """
    A LineNumErrorFilter instance count line number of the data and check
    whether the line number is correct.

    action:
        * less-than: If the line number of the data is less-than the
                     'linenum', raise a ValueError.
        * less-equal: If the line number of the data is less-equal the
                      'linenum', raise a ValueError.
        * equal: If the line number of the data is equal to the 'linenum',
                 raise a ValueError.
        * not-equal: If the line number of the data is not-equal to the
                     'linenum', raise a ValueError.
        * greater-equal: If the line number of the data is greater-equal the
                      'linenum', raise a ValueError.
        * greater-than: If the line number of the data is greater-than the
                     'linenum', raise a ValueError.

    linenum:
        The linenum is used to compare with the real line number of the data.
    """
    def __init__(self, action, linenum):
        ErrorFilter.__init__(self)
        self.filter_func = {"less-than": self.less_than,
                            "less-equal": self.less_equal,
                            "equal": self.equal,
                            "not-equal": self.not_equal,
                            "greater-equal": self.greater_equal,
                            "greater-than": self.greater_than
                           }
        if action in self.filter_func.keys():
            self.action = action
        else:
            raise KeyError("Unknown action '%s'" % (action))

        if isinstance(linenum, str):
            self.linenum = int(linenum)
        elif isinstance(linenum, int):
            self.linenum = linenum
        else:
            raise ValueError("Invalid linenum.")

    def __str__(self):
        ret = ("LineNumErrorFilter(Line number %s %s)"
            % (self.action, self.linenum))
        return ret

    def less_than(self, data):
        """
        If the line number is less-than self.linenum, raise a ValueError.
        """
        lines = data.split('\n')
        if len(lines) < self.linenum:
            raise ValueError("Find %d lines, less-than %d."
                % (len(lines), self.linenum))

    def less_equal(self, data):
        """
        If the line number is less-equal self.linenum, raise a ValueError.
        """
        lines = data.split('\n')
        if len(lines) <= self.linenum:
            raise ValueError("Find %d lines, less-equal %d."
                % (len(lines), self.linenum))

    def equal(self, data):
        """
        If the line number is equal to self.linenum, raise a ValueError.
        """
        lines = data.split('\n')
        if len(lines) == self.linenum:
            raise ValueError("Find %d lines, equal %d."
                % (len(lines), self.linenum))

    def not_equal(self, data):
        """
        If the line number is not-equal to self.linenum, raise a ValueError.
        """
        lines = data.split('\n')
        if len(lines) != self.linenum:
            raise ValueError("Find %d lines, not equal %d."
                % (len(lines), self.linenum))

    def greater_equal(self, data):
        """
        If the line number is greater-equal self.linenum, raise a
        valueError.
        """
        lines = data.split('\n')
        if len(lines) >= self.linenum:
            raise ValueError("Find %d lines, greater-equal %d."
                % (len(lines), self.linenum))

    def greater_than(self, data):
        """
        If the line number is greater-than self.linenum, raise a ValueError.
        """
        lines = data.split('\n')
        if len(lines) > self.linenum:
            raise ValueError("Find %d lines, greater-than %d."
                % (len(lines), self.linenum))

    def filter(self, data):
        """
        Execute the filter function.
        """
        self.filter_func[self.action](data)

    def show(self):
        """
        Print self information to the log.
        """
        _LOGGER.info("LineNumErrorFilter: Line number %s %s",
            self.action, self.linenum)

class DataSizeErrorFilter(ErrorFilter):
    """
    A DataSiseErrorFilter instance count the data size and check whether it
    is valid.

    action:
        * less-than: If the data size is less-than the 'size', raise a
                     ValueError.
        * less-equal: If the data size is less-equal the 'size', raise a
                      ValueError.
        * equal: If the data size is equal to the 'size', raise a ValueError.
        * not-equal: If the data size is not-equal to the 'size', raise a
                     ValueError.
        * greater-equal: If the data size is greater-equal the 'size', raise
                         a ValueError.
        * greater-than: If the data size is greater-than the 'size', raise a
                        ValueError.

    size:
        The 'size' is used to compare with the real data size.
    """
    def __init__(self, action, size):
        ErrorFilter.__init__(self)
        self.filter_func = {"less-than": self.less_than,
                            "less-equal": self.less_equal,
                            "equal": self.equal,
                            "not-equal": self.not_equal,
                            "greater-equal": self.greater_equal,
                            "greater-than": self.greater_than
                           }
        if action in self.filter_func.keys():
            self.action = action
        else:
            raise KeyError("Unknown action '%s'" % (action))
        if isinstance(size, str):
            self.size = int(size)
        elif isinstance(size, int):
            self.size = size
        else:
            raise ValueError("Invalid size.")
        
    def __str__(self):
        ret = ("DataSizeErrorFilter(Size %s %s bytes)"
            % (self.action, self.size))
        return ret

    def less_than(self, data):
        """
        If the data size is less-than self.size, raise a ValueError.
        """
        size = len(data)
        if size < self.size:
            raise ValueError("Find %d bytes, less-than %d."
                % (size, self.size))

    def less_equal(self, data):
        """
        If the data size is less-equal self.size, raise a ValueError.
        """
        size = len(data)
        if size <= self.size:
            raise ValueError("Find %d bytes, less-equal %d."
                % (size, self.size))

    def equal(self, data):
        """
        If the data size is equal to self.size, raise a ValueError.
        """
        size = len(data)
        if size == self.size:
            raise ValueError("Find %d bytes, equal %d."
                % (size, self.size))

    def not_equal(self, data):
        """
        If the data size is not-equal to self.size, raise a ValueError.
        """
        size = len(data)
        if size != self.size:
            raise ValueError("Find %d bytes, not-equal %d."
                % (size, self.size))

    def greater_equal(self, data):
        """
        If the data size is greater-equal self.size, raise a ValueError.
        """
        size = len(data)
        if size >= self.size:
            raise ValueError("Find %d bytes, greater-equal %d."
                % (size, self.size))

    def greater_than(self, data):
        """
        If the data size is greater-than self.size, raise a ValueError.
        """
        size = len(data)
        if size > self.size:
            raise ValueError("Find %d bytes, greater-than %d."
                % (size, self.size))

    def filter(self, data):
        """
        Execute the filter function.
        """
        self.filter_func[self.action](data)

    def show(self):
        """
        Print self information to the log.
        """
        _LOGGER.info("DataSizeErrorFilter: Size %s %s bytes",
            self.action, self.size)

class ErrorFilterFactory(object):
    """
    A ErrorFilterFactory is a factory of ErrorFilter and its children.
    """
    def __init__(self):
        self.filters = {"key-word": KeywordErrorFilter,
                        "data-size": DataSizeErrorFilter,
                        "line-number": LineNumErrorFilter}

    def create_filter(self, ftype, action, args):
        """
        Create an ErrorFilter instance.

        ftype: ErrorFilter Type. It could be 'key-word', 'data-size',
               'line-number'.
        action: This argument will be pass to ErrorFilter's initialization
                function.
        args: This argument will be pass to ErrorFilter's initialization
              function.
        """
        if ftype in self.filters.keys():
            efilter = self.filters[ftype](action, args)
            return efilter
        else:
            raise KeyError("Unknown Error Filter '%s'" % (ftype))

#--------------------------------------------------------------------------
# ValueFilter
#--------------------------------------------------------------------------
class ValueFilter(object):
    """
    A ValueFilter instance check data and modify it.
    """
    def __init__(self, action=None, args=None):
        pass

    def __str__(self):
        return "Unknown ValueFilter"

    def filter(self, data):
        """
        The method of filter data. The children of ValueFilter should
        implement this method.
        This method should modify the data as user asked and return the
        result.

        data: Must be a string.
        """
        raise NotImplementedError

    def show(self):
        """
        Print self information to the log.
        """
        _LOGGER.warning("Unknown ValyeFilter")

class ValueFilterSet(ValueFilter):
    """
    A ValueFilterSet is a list of ValueFilter instance.
    """
    def __init__(self):
        ValueFilter.__init__(self)
        self.filters = []

    def __str__(self):
        ret = "["
        for vfilter in self.filters:
            ret += str(vfilter) + ","
        ret = ret[:-1] + "]"
        return ret

    def add_filter(self, vfilter):
        """
        Add a ValueFilter instance.
        """
        if not (vfilter in self.filters):
            self.filters.append(vfilter)

    def remove_filter(self, vfilter):
        """
        Remove a ValueFilter instance.
        """
        if vfilter in self.filters:
            self.filters.remove(vfilter)

    def filter(self, data):
        """
        Execute all ValueFilter instance in the list.
        """
        for vfilter in self.filters:
            data = vfilter.filter(data)
        return data

    def show(self):
        """
        Print self information to the log.
        """
        _LOGGER.info("ValueFilterSet:")
        for vfilter in self.filters:
            vfilter.show()

class LineFilter(ValueFilter):
    """
    A LineFilter instance remove line which includes a keyword.

    action:
        * remove-line-start-with-keyword: Remove lines which starts with a
              keyword.
        * remove-line-include-keyword: Remove lines which includes a
              keyword.
    keyword:
       The keyword is used to search in the data.
    """
    def __init__(self, action, keyword):
        ValueFilter.__init__(self)
        self.filter_func = {
          "remove-line-start-with-keyword": self.remove_line_start_with_keyword,
          "remove-line-include-keyword": self.remove_line_include_keyword
          }
        if action in self.filter_func.keys():
            self.action = action
        else:
            raise KeyError("Unknown action '%s'" % (action))
        if isinstance(keyword, str):
            self.keyword = keyword
        else:
            raise ValueError("Invalid Keyword")

    def __str__(self):
        ret = "LineFilter(%s %s)" % (self.action, self.keyword)
        return ret

    def remove_line_start_with_keyword(self, data):
        """
        Remove lines which starts with a keyword.
        """
        lines = data.split("\n")
        ret = ""
        for line in lines:
            mar = re.match(self.keyword, line)
            if mar == None:
                ret += line + "\n"
        if len(ret) != 0 and ret[-1] == "\n":
            ret = ret[:-1]
        return ret

    def remove_line_include_keyword(self, data):
        """
        Remove lines which includes a keyword.
        """
        lines = data.split("\n")
        ret = ""
        for line in lines:
            ser = re.search(self.keyword, line)
            if ser == None:
                ret += line + "\n"
        if len(ret) != 0 and ret[-1] == "\n":
            ret = ret[:-1]
        return ret

    def filter(self, data):
        """
        Execute the filter function.
        """
        data = self.filter_func[self.action](data)
        return data

    def show(self):
        """
        Print self information to the log.
        """
        _LOGGER.info("LineFilter: %s %s", self.action, self.keyword)

class ValueFilterFactory(object):
    """
    A ValueFilterFactory is a factory of ValueFilter.
    """
    def __init__(self):
        self.filters = {"line-filter":LineFilter}

    def create_filter(self, ftype, action, args):
        """
        Create ValueFilter instances.

        ftype: ValueFilter Type. It could be 'line-filter'.
        action: This argument will be pass to ValueFilter's initialization
                function.
        args: This argument will be pass to ValueFilter's initialization
              function.
        """
        if ftype in self.filters.keys():
            vfilter = self.filters[ftype](action, args)
            return vfilter
        else:
            raise KeyError("Unknown Value Filter")

#--------------------------------------------------------------------------
#    System Command Executor
#--------------------------------------------------------------------------
class CommandExecutor(object):
    """
    A CommandExecutor instance execute a command.

    cmd: The command will be executed. It could be a string, a list or a
         tuple. For example, "ifconfig -a", ("ifconfig", "-a") or
         ["ifconfig", "-a"]
    user_input: User input data. It could be a list or a tuple. For example,
                ["Y", "Y", "N"] or ("Y", "Y", "N")
    value_filter: A ValueFilter instance.
    error_filter: A ErrorFilter instance.
    """
    def __init__(self,
                 cmd,
                 user_input=None,
                 value_filter=None,
                 error_filter=None):
        if isinstance(cmd, str):
            self.cmd = shlex.split(cmd)
        elif isinstance(cmd, (tuple, list)):
            self.cmd = cmd
        else:
            raise ValueError("cmd must be a string or a tuple.")

        if user_input == None:
            self.user_input = None
        elif isinstance(user_input, str):
            self.user_input = [user_input]
        elif isinstance(user_input, (tuple, list)):
            self.user_input = user_input
        else:
            raise ValueError("user_input must be a string or a tuple.")

        self.value_filter = value_filter
        self.error_filter = error_filter

    def __str__(self):
        ret = ("{Command: %s,"
               "UserInput: %s,"
               "ValueFilter: %s,"
               "ErrorFilter: %s}"
            % (self.cmd,
               self.user_input,
               self.value_filter,
               self.error_filter))
        return ret

    def __call__(self):
        _LOGGER.info("Command: %s", self.to_str())
        value = self.apply()
        if self.value_filter != None:
            value = self.value_filter.filter(value)
        if self.error_filter != None:
            self.error_filter.filter(value)

    def apply(self):
        """
        Execute the command and return the rawdata. Children of
        CommandExecutor should implement this method.
        """
        raise NotImplementedError

    def set_value_filter(self, vfilter):
        """
        Set the ValueFilter instance.
        """
        self.value_filter = vfilter

    def set_error_filter(self, efilter):
        """
        Set the ErrorFitler instance
        """
        self.error_filter = efilter

    def to_str(self):
        """
        Get the string of the command.
        """
        cmd = ""
        for arg in self.cmd:
            cmd += arg + " "
        return cmd

    def show(self):
        """
        Print self information to the log.
        """
        _LOGGER.info("Command: %s", self.to_str())
        _LOGGER.info("UserInput: %s", self.user_input)
        if self.value_filter != None:
            self.value_filter.show()
        else:
            _LOGGER.info("ValueFilter: None")

        if self.error_filter != None:
            self.error_filter.show()
        else:
            _LOGGER.info("ErrorFilter: None")

class CommandLocalViaSystem(CommandExecutor):
    """
    Execute command through system(). This is the simplest way to execute a
    command on localhost.

    cmd: The command will be executed. It could be a string, a list or a
         tuple. For example, "ifconfig -a", ("ifconfig", "-a") or
         ["ifconfig", "-a"]
    """
    def __init__(self, cmd):
        CommandExecutor.__init__(self, cmd)

    def apply(self):
        """
        Execute the command.
        """
        stdout_fd, stdout_path = tempfile.mkstemp()
        stderr_fd, stderr_path = tempfile.mkstemp()
        cmd_real = "%s >%s 2>%s" % (self.to_str(), stdout_path, stderr_path)
        ret = os.system(cmd_real)
        stdout = file(stdout_path, 'r')
        value = stdout.read()
        stdout.seek(0)
        for line in stdout:
            if line[-1] == "\n":
                _LOGGER_RAW.info("%s", line[:-1])
            else:
                _LOGGER_RAW.info("%s", line)
        stdout.close()
        os.close(stdout_fd)
        os.remove(stdout_path)

        if ret != 0 or os.path.getsize(stderr_path) != 0:
            stderr = file(stderr_path, 'r')
            for line in stderr:
                if line[-1] == "\n":
                    _LOGGER_RAW.warning("%s", line[:-1])
                else:
                    _LOGGER_RAW.warning("%s", line)
            stderr.close()
            os.close(stderr_fd)
            os.remove(stderr_path)
            _LOGGER.warning("Exit code: %s", ret)
            raise OSError("Command '%s' failed." % (self.to_str()))
        os.close(stderr_fd)
        os.remove(stderr_path)
        return value

class CommandLocalViaPopen(CommandExecutor):
    """
    Execute a command through Popen().

    cmd: The command will be executed. It could be a string, a list or a
         tuple. For example, "ifconfig -a", ("ifconfig", "-a") or
         ["ifconfig", "-a"]
    user_input: User input data. It could be a list or a tuple. For example,
                ["Y", "Y", "N"] or ("Y", "Y", "N")
    value_filter: A ValueFilter instance.
    error_filter: A ErrorFilter instance.
    """
    def __init__(self,
                 cmd,
                 user_input=None,
                 value_filter=None,
                 error_filter=None):
        CommandExecutor.__init__(self,
                                 cmd,
                                 user_input,
                                 value_filter,
                                 error_filter)

    def apply(self):
        """
        Execute the command. If the command's exit code isn't zero, raise an
        OSError.
        """
        cmd = subprocess.Popen(self.cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               stdin=subprocess.PIPE)
        # Send user input.
        if self.user_input != None:
            for arg in self.user_input:
                if arg[-1] != "\n":
                    arg += "\n"
                cmd.stdin.write(arg)
        # Read stdout and stderr
        value = ""
        last_clear = False
        while True:
            while True:
                outline = cmd.stdout.readline()
                if len(outline) != 0:
                    value += outline
                    if outline[-1] == "\n":
                        _LOGGER_RAW.info("%s", outline[:-1])
                    else:
                        _LOGGER_RAW.info("%s", outline)
                else:
                    break

            while True:
                errline = cmd.stderr.readline()
                if len(errline) != 0:
                    value += errline
                    if errline[-1] == "\n":
                        _LOGGER_RAW.warning("%s", errline[:-1])
                    else:
                        _LOGGER_RAW.warning("%s", errline)
                else:
                    break
            if cmd.poll() != None:
                # read stdout and stderr again before quit.
                if last_clear == True:
                    break
                else:
                    last_clear = True
        # Check the return code.
        if cmd.returncode != 0:
            _LOGGER.warning("Exit code: %d", cmd.returncode)
            raise OSError("Command '%s' failed." % (self.cmd))
        return value

class CommandUart(CommandExecutor):
    """
    Execute a command through UART.

    cmd: The command will be executed. It could be a string, a list or a
         tuple. For example, "ifconfig -a", ("ifconfig", "-a") or
         ["ifconfig", "-a"]
    port: UART port, such as "/dev/ttyUSB0".
    baudrate: UART baudrate, such as "115200".
    timeout: The timeout for reading or writing once. It could be a float or
             a string. For example, "0.1" or 0.1. The default value is 0.1
             second.
    end_of_line: The end mark of a line.
                 * "LF" use "\n" as end mark.
                 * "CR" use "\r" as end mark.
                 * "CRLF" use "\r\n" as end mark.
    recv: The byte number that we expected.
    endmarks: The endmarks of a command. It could be string, a list or a
              tuple . For example, "0000:0000>", ["0000:0000", "0000:0001"]
              or ("0000:0000", "0000:0001").
    user_input: Doesn't support user input. This argument will be ignored.
    value_filter: A ValueFilter instance.
    error_filter: A ErrorFilter instance.
    """
    global_endmarks = []
    global_end_of_line = "LF"
    def __init__(self,
                 cmd,
                 port,
                 baudrate,
                 timeout=None,
                 end_of_line=None,
                 cmd_timeout=None,
                 recv=None,
                 endmarks=None,
                 user_input=None,
                 value_filter=None,
                 error_filter=None):
        CommandExecutor.__init__(self,
                                 cmd,
                                 user_input,
                                 value_filter,
                                 error_filter)
        # Set UART port, baudrate
        self.port = port
        self.baudrate = baudrate
        # Set timeout, default is 0.1
        if timeout == None or float(timeout) <= 0:
            self.timeout = 0.1
        else:
            self.timeout = float(timeout)
        # Set cmd_timeout, default is 0.5
        if cmd_timeout == None or float(cmd_timeout) <= 0:
            self.cmd_timeout = 0.5
        else:
            self.cmd_timeout = float(cmd_timeout)
        if recv == None:
            self.recv = None
            self.read_size = 4096
        else:
            self.recv = int(recv)
            self.read_size = self.recv

        # Set endmarks
        if isinstance(endmarks, (list, tuple)):
            self.endmarks = endmarks
        elif isinstance(endmarks, str):
            self.endmarks = [endmarks]
        elif endmarks == None:
            self.endmarks = self.global_endmarks

        # Set end_of_line and eol
        if end_of_line in ("LF", "CR", "CRLF"):
            self.end_of_line = end_of_line
        else:
            self.end_of_line = self.global_end_of_line
        if self.end_of_line == "LF":
            self.eol = "\n"
        elif self.end_of_line == "CR":
            self.eol = "\r"
        elif self.end_of_line == "CRLF":
            self.eol = "\r\n"

    def __str__(self):
        ret = ("{Command: %s,"
               "UserInput: %s,"
               "ValueFilter: %s,"
               "ErrorFilter: %s,"
               "Uart: %s:%s:%ss}"
            % (self.cmd,
               self.user_input,
               self.value_filter,
               self.error_filter,
               self.port, self.baudrate, self.timeout))
        return ret

    def show(self):
        """
        Print self information to the log.
        """
        _LOGGER.info("Command: %s", self.to_str())
        _LOGGER.info("UserInput: %s", self.user_input)
        if self.value_filter != None:
            self.value_filter.show()
        else:
            _LOGGER.info("ValueFilter: None")

        if self.error_filter != None:
            self.error_filter.show()
        else:
            _LOGGER.info("ErrorFilter: None")
        _LOGGER.info("Timeout: %s", self.cmd_timeout)
        _LOGGER.info("Receive Bytes: %s", self.recv)
        _LOGGER.info("Uart: port %s, baudrate %s, timeout %ss",
            self.port, self.baudrate, self.timeout)
        if self.end_of_line == "LF":
            _LOGGER.info(r"End Of Line: LF(\n)")
        elif self.end_of_line == "CR":
            _LOGGER.info(r"End Of Line: CR(\r)")
        elif self.end_of_line == "CRLF":
            _LOGGER.info(r"End Of Line: CRLF(\r\n)")
        for endmark in self.endmarks:
            _LOGGER.info("End Mark: %s", endmark)

    def apply(self):
        """
        Execute the command.
        """
        # Init Uart
        uart = serial.Serial(self.port,
                             self.baudrate,
                             timeout=self.timeout)
        # Execute Command
        time_start = time.time()
        time_escape = time.time() - time_start
        uart.write(self.cmd + self.eol)
        uart.flush()
        rawdata = ""
        while time_escape <= self.cmd_timeout:
            rawdata += uart.read(self.read_size)
            if self.recv != None and len(rawdata) >= self.recv:
                break

            find_endmark = False
            for endmark in self.endmarks:
                sret = re.search(endmark, rawdata)
                if sret != None:
                    find_endmark = True
                    break
            if find_endmark == True:
                break
            time_escape = time.time() - time_start
        uart.close()
        # Print rawdata
        lines = rawdata.split("\n")
        for line in lines:
            _LOGGER_RAW.info("%s", line)
        return rawdata

    @classmethod
    def set_global_endmarks(cls, endmarks):
        """
        Set global endmarks. This method effects all CommandUart instances.
        """
        if isinstance(endmarks, str):
            cls.global_endmarks = [endmarks]
        elif isinstance(endmarks, (list, tuple)):
            cls.global_endmarks = endmarks
        else:
            cls.global_endmarks = []

    @classmethod
    def set_global_end_of_line(cls, end_of_line):
        """
        Set global end_of_line, This method effects all CommandUart
        instances.
        """
        if end_of_line in ("LF", "CR", "CRLF"):
            cls.global_end_of_line = end_of_line
        else:
            cls.global_end_of_line = "LF"
            


class CommandSSH(CommandExecutor):
    """
    Execute a command through SSH.

    cmd: The command will be executed. It could be a string, a list or a
         tuple. For example, "ifconfig -a", ("ifconfig", "-a") or
         ["ifconfig", "-a"]
    host: The IP address of the host, such as "192.168.0.1".
    user: The user name on the host.
    passwd: The password of the user.
    port: SSH service port, the default value is 22.
    user_input: User input data. It could be a list or a tuple. For example,
                ["Y", "Y", "N"] or ("Y", "Y", "N")
    value_filter: A ValueFilter instance.
    error_filter: A ErrorFilter instance.
    """
    def __init__(self,
                 cmd,
                 host,
                 user,
                 passwd,
                 port=22,
                 user_input=None,
                 value_filter=None,
                 error_filter=None,
                 label=None):
        CommandExecutor.__init__(self,
                                 cmd,
                                 user_input,
                                 value_filter,
                                 error_filter)
        self.host = host
        self.user = user
        self.passwd = passwd
        self.port = port
        if label == None:
            self.label = ""
        else:
            self.label = "<%s> " % (label)

    def __str__(self):
        ret = ("{Command: %s,"
               "UserInput: %s,"
               "ValueFilter: %s,"
               "ErrorFilter: %s,"
               "SSH: %s:%s@%s:%s}"
            % (self.cmd,
               self.user_input,
               self.value_filter,
               self.error_filter,
               self.user,
               self.passwd,
               self.host,
               self.port))
        return ret

    def show(self):
        """
        Print self information to the log.
        """
        _LOGGER.info("Command: %s", self.to_str())
        _LOGGER.info("UserInput: %s", self.user_input)
        if self.value_filter != None:
            self.value_filter.show()
        else:
            _LOGGER.info("ValueFilter: None")

        if self.error_filter != None:
            self.error_filter.show()
        else:
            _LOGGER.info("ErrorFilter: None")
        _LOGGER.info("SSH: %s:%s@%s:%s",
            self.user, self.passwd, self.host, self.port )

    def apply(self):
        """
        Execute the command.
        """
        # Create SSH Connection.
        ssh_log_fd, ssh_log_path = tempfile.mkstemp()
        paramiko.util.log_to_file(ssh_log_path)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.load_system_host_keys()
        try:
            client.connect(self.host, self.port, self.user, self.passwd)
        except Exception, err:
            _LOGGER.error(err)
            raise OSError("Failed to create SSH connection.")
        stdin, stdout, stderr = client.exec_command(self.to_str())
        # Send user input.
        if self.user_input != None:
            for arg in self.user_input:
                if arg[-1] != "\n":
                    arg += "\n"
                stdin.write(arg)
        # Read stdout and stderr
        value = ""
        stdout_mesg = ""
        stderr_mesg = ""
        last_check = False
        while True:
            if stdout.channel.recv_ready():
                stdout_mesg += stdout.channel.recv(1024)
                buf = stdout_mesg.split("\n")
                if len(buf) > 1:
                    stdout_mesg = buf[-1]
                    lines = buf[:-1]
                    for line in lines:
                        _LOGGER_RAW.info("%s%s", self.label, line)
                        value += line + "\n"
            if stdout.channel.recv_stderr_ready():
                stderr_mesg += stdout.channel.recv_stderr(1024)
                buf = stderr_mesg.split("\n")
                if len(buf) > 1:
                    stderr_mesg = buf[-1]
                    lines = buf[:-1]
                    for line in lines:
                        _LOGGER_RAW.warning("%s%s", self.label, line)
                        value += line + "\n"
            if stdout.channel.exit_status_ready():
                if last_check:
                    break
                else:
                    last_check = True
            time.sleep(0.01)
        # Check exit status.
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            _LOGGER.warning("%sExit code: %d", self.label, exit_status)
            ssh_log = file(ssh_log_path)
            for line in ssh_log:
                _LOGGER.info("%s%s", self.label, line)
            ssh_log.close()
        client.close()
        os.close(ssh_log_fd)
        os.remove(ssh_log_path)
        if exit_status != 0:
            raise OSError("%sCommand '%s' failed." % (self.label, self.to_str()))
        return value

