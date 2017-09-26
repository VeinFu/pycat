#! /usr/bin/python

"""
Command test items.
"""

from lxml import etree
import os
import re
import tempfile
import copy
import subprocess
import paramiko
import serial
import time

from pycat import log, testcase

_LOGGER = log.getLogger("log.tc")

#--------------------------------------------------------------------------
#    Error Filter
#--------------------------------------------------------------------------
class ErrorFilter(object):
    def __init__(self):
        pass

    def determine(self, data):
        raise NotImplementedError

class KeywordErrorFilter(ErrorFilter):
    def __init__(self, action, keyword):
        ErrorFilter.__init__(self)
        self.action = action
        self.keyword = keyword

    def __str__(self):
        ret = "ErrorFilter: %s keyword '%s'" % (self.action, self.keyword)
        return ret

    def find_keyword(self, data):
        lines = data.split('\n')
        for line in lines:
            sret = re.search(self.keyword, line)
            if sret != None:
                raise ValueError("Find keyword '%s' in line '%s'" % (self.keyword, line))

    def not_find_keyword(self, data):
        lines = data.split('\n')
        find_keyword = False
        for line in lines:
            sret = re.search(self.keyword, line)
            if sret != None:
                 find_keyword = True
        if find_keyword == False:
            raise ValueError("Can't find keyword '%s'" % (self.keyword))

    def determine(self, data):
        if self.action == "find":
            self.find_keyword(data)
        elif self.action == "not-find":
            self.not_find_keyword(data)

class LineNumErrorFilter(ErrorFilter):
    def __init__(self, action, linenum):
        ErrorFilter.__init__(self)
        self.action = action
        if isinstance(linenum, str):
            self.linenum = int(linenum)
        elif isinstance(linenum, int):
            self.linenum = linenum

        self.determine_func = {"less-than": self.less_than,
                               "less-equal": self.less_equal,
                               "equal": self.equal,
                               "not-equal": self.not_equal,
                               "greater-equal": self.greater_equal,
                               "greater-than": self.greater_than
                              }
        if not self.action in self.determine_func.keys():
            raise KeyError("Unknown action '%s'" % (self.action))

    def __str__(self):
        ret = "ErrorFilter: Line number %s %s" % (self.action, self.linenum)
        return ret

    def less_than(self, data):
        lines = data.split('\n')
        if len(lines) < self.linenum:
            raise ValueError("Find %d lines, less-than %d." % (len(lines), self.linenum))

    def less_equal(self, data):
        lines = data.split('\n')
        if len(lines) <= self.linenum:
            raise ValueError("Find %d lines, less-equal %d." % (len(lines), self.linenum))

    def equal(self, data):
        lines = data.split('\n')
        if len(lines) == self.linenum:
            raise ValueError("Find %d lines, equal %d." % (len(lines), self.linenum))

    def not_equal(self, data):
        lines = data.split('\n')
        if len(lines) != self.linenum:
            raise ValueError("Find %d lines, not equal %d." % (len(lines), self.linenum))

    def greater_equal(self, data):
        lines = data.split('\n')
        if len(lines) >= self.linenum:
            raise ValueError("Find %d lines, greater-equal %d." % (len(lines), self.linenum))

    def greater_than(self, data):
        lines = data.split('\n')
        if len(lines) > self.linenum:
            raise ValueError("Find %d lines, greater-than %d." % (len(lines), self.linenum))

    def determine(self, data):
        self.determine_func[self.action](data)

class DataSizeErrorFilter(ErrorFilter):
    def __init__(self, action, size):
        ErrorFilter.__init__(self)
        self.action = action
        self.size = size
        if isinstance(size, str):
            self.size = int(size)
        elif isinstance(size, int):
            self.size = size

        self.determine_func = {"less-than": self.less_than,
                               "less-equal": self.less_equal,
                               "equal": self.equal,
                               "not-equal": self.not_equal,
                               "greater-equal": self.greater_equal,
                               "greater-than": self.greater_than
                              }
        if not self.action in self.determine_func.keys():
            raise KeyError("Unknown action '%s'" % (self.action))
        
    def __str__(self):
        ret = "ErrorFilter: Size %s %s bytes" % (self.action, self.size)
        return ret

    def less_than(self, data):
        size = len(data)
        if size < self.size:
            raise ValueError("Find %d bytes, less-than %d." % (size, self.size))

    def less_equal(self, data):
        size = len(data)
        if size <= self.size:
            raise ValueError("Find %d bytes, less-equal %d." % (size, self.size))

    def equal(self, data):
        size = len(data)
        if size == self.size:
            raise ValueError("Find %d bytes, equal %d." % (size, self.size))

    def not_equal(self, data):
        size = len(data)
        if size != self.size:
            raise ValueError("Find %d bytes, not-equal %d." % (size, self.size))

    def greater_equal(self, data):
        size = len(data)
        if size >= self.size:
            raise ValueError("Find %d bytes, greater-equal %d." % (size, self.size))

    def greater_than(self, data):
        size = len(data)
        if size > self.size:
            raise ValueError("Find %d bytes, greater-than %d." % (size, self.size))

    def determine(self, data):
        self.determine_func[self.action](data)

class SerialBinaryFilter(ErrorFilter):
    def __init__(self, action, nbytes=None):
        ErrorFilter.__init__(self)
        self.action = action
        self.nbytes = nbytes
        if isinstance(nbytes, str):
            self.nbytes = int(nbytes)
        elif isinstance(nbytes, int):
            self.nbytes = nbytes

    def __str__(self):
        ret = "ErrorFilter: Search %s binary." % (self.nbytes)
        return ret

    #@todo Not Implemented
    def determine(self, data):
        raise NotImplementedError

ErrorFilters = {"key-word": KeywordErrorFilter,
                "data-size": DataSizeErrorFilter,
                "line-number": LineNumErrorFilter,
                "serial-number": SerialBinaryFilter}

#--------------------------------------------------------------------------
#    System Command Executor
#--------------------------------------------------------------------------
class CommandExecutor(object):
    """
    A CommandExecutor instance execute a command through different ways.
    """
    def __init__(self, cmd):
        assert isinstance(cmd, str)
        self.cmd = cmd
        self.error_fliters = list()

    def __str__(self):
        return self.cmd

    def apply(self):
        """
        Children of CommandExecutor should replace this method.
        """
        raise NotImplementedError

class CommandLocalViaSystem(CommandExecutor):
    """
    Execute command through system().
    """
    def __init__(self, cmd):
        CommandExecutor.__init__(self, cmd)

    def __str__(self):
        ret = "CMD: '%s'" % (self.cmd)
        return ret

    def show(self):
        _LOGGER.info("CMD: %s", self.cmd)

    def apply(self):
        """
        Execute the command.
        """
        count = 0
        for i in range(3):
            flag = 0
            stdout_fd, stdout_path = tempfile.mkstemp()
            stderr_fd, stderr_path = tempfile.mkstemp()
            cmd_real = "%s >%s 2>%s" % (self.cmd, stdout_path, stderr_path)
            ret = os.system(cmd_real)
            stdout = file(stdout_path, 'r')
            value = stdout.read()
            stdout.seek(0)
            for line in stdout:
                _LOGGER.debug("%s", line)
            stdout.close()
            os.close(stdout_fd)
            os.remove(stdout_path)

            if ret != 0 or os.path.getsize(stderr_path) != 0:
                flag += 1
                count += 1
                stderr = file(stderr_path, 'r')
                for line in stderr:
                    _LOGGER.warning("%s", line)
                stderr.close()
                if count == 3:
                    os.close(stderr_fd)
                    os.remove(stderr_path)
                    raise OSError("Failed to apply '%s'." % (self.cmd))
                time.sleep(30)
            os.close(stderr_fd)
            os.remove(stderr_path)
            if flag == 0:
                break
        return value

class CommandLocalViaPopen(CommandExecutor):
    """
    Execute a command through Popen().
    """
    def __init__(self, cmd):
        CommandExecutor.__init__(self, cmd)

    def __str__(self):
        ret = "CMD: '%s'" % (self.cmd)
        return ret

    def show(self):
        _LOGGER.info("CMD: %s", self.cmd)

    def apply(self):
        """
        Execute the command.
        """
        _LOGGER.info("Execute '%s'" % (self.cmd))
        cmd = tuple(self.cmd.split(' '))
        cmdexec = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        value = ""
        last_clear = False
        while True:
            line = cmdexec.stdout.readline()
            while line != "":
                value += line
                if line[-1] == "\n":
                    _LOGGER.info("%s", line[:-1])
                else:
                    _LOGGER.info("%s", line)
                line = cmdexec.stdout.readline()
            line = cmdexec.stderr.readline()
            while line != "":
                _LOGGER.warning("%s", line[:-1])
                line = cmdexec.stderr.readline()
            ret = cmdexec.poll()
            if ret != None:
                if last_clear == True:
                    break
                last_clear = True
#        if ret != 0:
#            _LOGGER.warning("Exit code: %d", ret)
#            raise OSError("Failed to apply '%s'." % (self.cmd))
        return value

class CommandUart(CommandExecutor):
    """
    Execute a command through uart.
    If timeout is less then zero or equal to zero, timeout will be set as 0.5.
    If recv isn't set, it will be set as 4096.
    If recv is zero, that means there're no data returned from the uart.
    """
    def __init__(self, cmd, port, baudrate, timeout=None, recv=None):
        CommandExecutor.__init__(self, cmd)
        self.port = port
        self.baudrate = baudrate
        if timeout == None or float(timeout) <= 0:
            self.timeout = 0.5
        else:
            self.timeout = float(timeout)
        if recv == None:
            self.recv = 4096
        else:
            self.recv = int(recv)

    def __str__(self):
        ret = "CMD: '%s' \nUart: port %s, baudrate %s, timeout %ss"\
              % (self.cmd, self.port, self.baudrate, self.timeout)
        return ret

    def show(self):
        _LOGGER.info("CMD: %s", self.cmd)
        _LOGGER.info("Uart: port %s, baudrate %s, timeout %ss", self.port, self.baudrate, self.timeout)

    def apply(self):
        """
        Execute the command.
        """
        uart = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        _LOGGER.info("Execute '%s'", self.cmd)
        cmd = self.cmd + '\n'
        uart.write(cmd)
        uart.flush()
        value = None
        if self.recv > 0:
            value = uart.read(self.recv)
            lines = value.split('\n')
            for line in lines:
                _LOGGER.info("%s", line)
        return value

class CommandSSH(CommandExecutor):
    """
    Execute a command through SSH.
    """
    def __init__(self, cmd, host, user, passwd, port=22):
        CommandExecutor.__init__(self, cmd)
        self.host = host
        self.user = user
        self.passwd = passwd
        self.port = port

    def __str__(self):
        ret = "CMD: '%s' \nSSH: %s:%s %s %s" % (self.cmd, self.host, self.port, self.user, self.passwd)
        return ret

    def show(self):
        _LOGGER.info("CMD: %s", self.cmd)
        _LOGGER.info("SSH: %s:%s %s %s", self.host, self.port, self.user, self.passwd)

    def apply(self):
        """
        Execute the command.
        """
        for i in range(1):
            ssh_log_fd, ssh_log_path = tempfile.mkstemp()
            paramiko.util.log_to_file(ssh_log_path)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.load_system_host_keys()
            try:
                client.connect(self.host, self.port, self.user, self.passwd)
            except Exception, err:
                _LOGGER.error(err)
                raise OSError("Failed to apply '%s'." % (self.cmd))
        #transport = client.get_transport()
        #session = transport.open_session()
        #session.request_x11(single_connection=True)
#        _LOGGER.info("Execute '%s'" % (self.cmd))
            time.sleep(4)
            _LOGGER.info("Execute '%s'" % (self.cmd))
            try:
                stdin, stdout, stderr = client.exec_command(self.cmd)
            except Exception, err:
                _LOGGER.error(err)
            value = stdout.read()
            lines = value.split('\n')
            for line in lines:
                _LOGGER.info("%s", line)
            errinfo = stderr.read()
            lines = errinfo.split('\n')
            for line in lines:
                if len(line) == 0 or line.isspace():
                    continue
                _LOGGER.warning("%s", line)
            exit_status = stdout.channel.recv_exit_status()
#            if exit_status != 0:
#                _LOGGER.warning("exit code: %d", exit_status)
#                ssh_log = file(ssh_log_path)
#                for line in ssh_log:
#                    _LOGGER.info("%s", line)
#                ssh_log.close()
            client.close()
            os.close(ssh_log_fd)
            os.remove(ssh_log_path)
            if exit_status == 0:
                break
#        if exit_status != 0:
#            raise OSError("Failed to apply '%s'." % (self.cmd))
        return value

class CommandTelnet(CommandExecutor):
	
	""" Execute a command through telnet
	"""

	def __init__(self, cmd, host, user, passwd, timeout, port=23):
		CommandExecutor.__init__(self, cmd)
		self.host = host
		self.user = user
		self.passwd = passwd
		self.timeout = timeout
		self.port = port

	
# @todo Not Implemented
#class CommandSSHX11(CommandExecutor):
#class CommandTCP(CommandExecutor):

#--------------------------------------------------------------------------
#    Command Test Items
#--------------------------------------------------------------------------

def combine_attribute(new_node, src_node, ref_node, attr, default=None):
    """
    Combine attribute in items.

    If find attribute in src_node, copy it into new_node.
    Otherwise search attribite in ref_node. If find attribute, copy it into new_node.
    If can't find attribute in src_node or ref_node, use the default value.
    """
    attr_value = src_node.get(attr)
    if attr_value == None and ref_node != None:
        attr_value = ref_node.get(attr)
    if attr_value != None :
        new_node.set(attr, attr_value)
    elif default != None:
        new_node.set(attr, default)

def combine_unique_node(new_node, src_node, ref_node, tag):
    """
    Combine unique node in itmes.

    If find tag in src_node, copy it into new_node.
    Otherwise search tag in ref_node. If find tag in ref_node, cope it into
    new_node.
    If tag isn't in src_node or ref_node, return False.
    """
    subnode = src_node.find(tag)
    if subnode != None:
        subnode_tmp = copy.deepcopy(subnode)
        new_node.append(subnode_tmp)
    elif ref_node != None:
        subnode = ref_node.find(tag)
        if subnode != None:
            subnode_tmp = copy.deepcopy(subnode)
            new_node.append(subnode_tmp)
        else:
            return False
    return True

def combine_sequence_node(new_node, src_node, ref_node, tag, attrs):
    """
    Combine sequence nodes in items.

    Copy ref_node to new_node.
    If a subnode in src_node isn't named, copy it into new_node.
    If a subnode in src_node is named and never appeared in new_node, copy
    it into new_node.
    If a subnode in src_node is named and appeared in new_node, only replace
    its attributes.
    """
    assert src_node != None
    assert tag != None
    assert attrs != None
    if ref_node != None:
        # Copy subnodes in ref node.
        for subnode in ref_node.findall(tag):
            subnode_tmp = copy.deepcopy(subnode)
            new_node.append(subnode_tmp)

    # Combine new_node and ref_node.
    for subnode in src_node.findall(tag):
        subname = subnode.get("name")
        if subname == None:
            # Unnamed node, append it.
            subnode_tmp = copy.deepcopy(subnode)
            new_node.append(subnode_tmp)
        else:
            subnode_exist = new_node.find("./%s[@name='%s']" % (tag, subname))
            if subnode_exist == None:
                # Named node, but never appeared.
                subnode_tmp = copy.deepcopy(subnode)
                new_node.append(subnode_tmp)
            else:
                # Named node and existed, replace attributes only.
                for attr in attrs:
                    attr_value = subnode.get(attr)
                    if attr_value != None:
                        subnode_exist.set(attr, attr_value)

def analyse_node_default(case, source_node, tag):
    """
    Analyse item node define in XML.
    If find 'ref' node, use it. Ohterwise use the current one.
    """
    new_node = etree.Element(tag)
    # Get ref node
    ref = source_node.get("ref")
    ref_node = etree.Element(tag)
    if ref != None:
        ref_node_tmp = case.find(".//%s[@name='%s']" % (tag, ref))
        if ref_node_tmp != None:
            ref_node = analyse_node_default(case, ref_node_tmp, tag)
            new_node = copy.deepcopy(ref_node)
    else:
        new_node = copy.deepcopy(source_node)
    return new_node

def analyse_cmd(case, cmd_node, tag):
    """
    Analyse commands defined in XML.
    """
    node = etree.Element(tag)
    # Get ref node
    ref = cmd_node.get("ref")
    ref_node = etree.Element(tag)
    if ref != None:
        ref_node_tmp = case.find(".//%s[@name='%s']" % (tag, ref))
        if ref_node_tmp != None:
            ref_node = analyse_cmd(case, ref_node_tmp, tag)
    # Set attribute
    name = cmd_node.get("name")
    if name != None:
        node.set("name", name)
    cmd = cmd_node.get("cmd")
    if cmd == None:
        cmd = ref_node.get("cmd")
        if cmd == None:
            raise ValueError("%s node must set or inherit a 'cmd' attribute." % tag)
    node.set("cmd", cmd)
    proxy = cmd_node.get("proxy")
    if proxy == None:
        proxy = ref_node.get("proxy")
        if proxy == None:
            proxy = "local"
    node.set("proxy", proxy)

    # Combine SSH node
    sshnode = cmd_node.find("ssh")
    if sshnode != None:
        sshnode_tmp = copy.deepcopy(sshnode)
        node.append(sshnode_tmp)
    else:
        sshnode = ref_node.find("ssh")
        if sshnode != None:
            sshnode_tmp = copy.deepcopy(sshnode)
            node.append(sshnode_tmp)

    # Combine Uart node
    uartnode = cmd_node.find("uart")
    if uartnode != None:
        uartnode_tmp = copy.deepcopy(uartnode)
        node.append(uartnode_tmp)
    else:
        uartnode = ref_node.find("uart")
        if uartnode != None:
            uartnode_tmp = copy.deepcopy(uartnode)
            node.append(uartnode_tmp)

    # Copy option nodes in ref node.
    for optnode in ref_node.findall("option"):
        optnode_tmp = copy.deepcopy(optnode)
        node.append(optnode_tmp)

    # Combine option nodes in ref_node and cmd_node
    for optnode in cmd_node.findall("option"):
        optname = optnode.get("name")
        if optname == None:
            # Unnamed node, append it.
            optnode_tmp = copy.deepcopy(optnode)
            node.append(optnode_tmp)
        else:
            optnode_exist = node.find("./option[@name='%s']" % (optname))
            if optnode_exist == None:
                # Named node, but never appeared.
                optnode_tmp = copy.deepcopy(optnode)
                node.append(optnode_tmp)
            else:
                # Named node and existed, replace 'args' attribute only.
                optnode_exist.set("args", optnode.get("args"))
    return node

class CommandItem(testcase.TestItem):
    """
    A Command instance execute a command through local shell, SSH or uart.
    Supported proxy:
        * local, Execute a command on local shell.
        * ssh, Execute a command through SSH.
        * uart, Execute a command through uart.
    """
    item_type = "command"
    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.cmd = None

    def action_init(self, kwargs):
        """
        Initialize command. Analyse command and chose a proxy.
        """
        testcase = kwargs.get("testcase")
        cmd_node = self.parameter.find(self.item_type)
        cmd_node_combined = analyse_cmd(testcase, cmd_node, self.item_type)
        cmd = cmd_node_combined.get("cmd")
        for optnode in cmd_node_combined.findall("option"):
            cmd += " %s" % (optnode.get("args"))
        proxy = cmd_node_combined.get("proxy")
        if proxy == "local":
            self.cmd = CommandLocalViaPopen(cmd)
        elif proxy == "ssh":
            ssh = cmd_node_combined.find("ssh")
            host = ssh.get("host")
            user = ssh.get("user")
            passwd = ssh.get("passwd")
            self.cmd = CommandSSH(cmd, host, user, passwd)
        elif proxy == "uart":
            uart = cmd_node_combined.find("uart")
            port = uart.get("port")
            baudrate = uart.get("baudrate")
            timeout = uart.get("timeout")
            recv = uart.get("recv")
            self.cmd = CommandUart(cmd, port, baudrate, timeout, recv)
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        try:
            value = self.cmd.apply()
        except OSError:
            return False
        return True

    def action_clear(self, kwargs):
        """
        No thing to do.
        """
        return True

    def action_print_parameter(self, kwargs):
        """
        Print the command to be executed.
        """
        testcase = kwargs.get("testcase")
        self.cmd.show()
        return True

