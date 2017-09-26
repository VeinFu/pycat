#! /usr/bin/python

"""
Test Item for LSI SES VPD read/write/check
"""
from lxml import etree
import copy
import lsises
import binascii

from pycat import log, testcase
from basicplugin import command

_LOGGER = log.getLogger("log.tc")

#--------------------------------------------------------------------------
#  UNIT TEST
#--------------------------------------------------------------------------
_UNIT_TEST=None
def apply():
    ret_str= """
    Data [0] = 0\rData [1] = 0\rData [2] = 0\rData [3] = 0\rData [4] = 0\rData [5] = 0\rData [6] = 0\rData [7] = 0\rData [8] = 0\rData [9] = 0\rData [10] = 0\rData [11] = 0\rData [12] = 0\rData [13] = 0\rData [14] = 0\rData [15] = 0\rData [16] = 0\rData [17] = 0\rData [18] = 0\rData [19] = 0\rData [20] = 0\rData [21] = 0\rData [22] = 0\rData [23] = 0\rData [24] = 0\rData [25] = 0\rData [26] = 0\rData [27] = 0\rData [28] = 0\rData [29] = 0\rData [30] = 0\rData [31] = 0
    """
    return ret_str

#--------------------------------------------------------------------------
#  VPD command
#--------------------------------------------------------------------------
def analyse_vpd_node(case, source_node, tag):
    """
    Analyse item node define in XML.
    If find 'ref' node, use it. Otherwise use the current one.
    """
    new_node = etree.Element(tag)
    # Get ref node
    ref = source_node.get("ref")
    ref_node = etree.Element(tag)
    if ref != None:
        ref_node_tmp = case.find(".//%s[@name='%s']" % (tag, ref))
        if ref_node_tmp != None:
            ref_node = analyse_vpd_node(case, ref_node_tmp, tag)
            new_node = copy.deepcopy(ref_node)
    else:
        new_node = copy.deepcopy(source_node)
    return new_node

#return hex array
#example: input(292,2), return "0x1 0x24 "
def get_offset_bytes(offset, offset_width):
    raw_offset = offset
    offset_bytes=""
    for i in range(0,offset_width):
        offset_bytes = hex(raw_offset&0xff) + " " + offset_bytes
        raw_offset = raw_offset >> 8
    if raw_offset != 0:
        raise ValueError("offset(%d) & offset_with(%d) not matching,", offset, offset_width)
    return offset_bytes

def extract_rawdata(source_str):
    """
    Extract raw data from UART returned string(source string).
    The typical source string is:
     Data [0] = 54 \r
     Data [1] = 61 \r
   \r
   \r
    cmd >
    Then the return string is:
    5461
    """
    rawdata=""
    if (source_str=="" or source_str==None):
        return ""
    value_lines = source_str.split("\r")
    for line in value_lines:
        if line.find("Data")>=0:
            str_data = line.split("=")[1].strip()
            try:
                int_data = int("0x" + str_data, 0)
            except ValueError:
                return ""
            str_data = "%02x" % (int_data)
            rawdata = rawdata + str_data
    return rawdata


class LsisesVpdCmd(object):
    def __init__(self, node_combined):
        self.node_combined  = node_combined
        self.proxy          = None
        self.cmd_timeout    = None
        self.uart_port      = None
        self.uart_baudrate  = None
        self.uart_newline_transmit = None
        self.port_id        = None
        self.device_addr    = None
        self.offset         = None
        self.offset_width   = None
        self.block_size     = None
        self.number_bytes_to_do = None
        self.binary_file    = None
        self.binary_data    = None
        self.binary_fd      = None
        self.endmarks       = []
        self.error_filters  = []
        self.number_bytes_done = 0

    def clear(self):
        if self.binary_fd is not None:
            self.binary_fd.close()
        return True

    def get_parameters(self):
        #i2c cmd related
        self.port_id	    = int(self.node_combined.find("port-id").get("value"),0)
        if self.port_id < 0:
            raise ValueError("XML set error: port_id should >= 0")
        self.device_addr    = int(self.node_combined.find("device-addr").get("value"),0)
        if self.device_addr < 0:
            raise ValueError("XML set error: device_addr should >= 0")
        self.device_addr    = hex(self.device_addr)
        self.offset	    = int(self.node_combined.find("offset").get("value"),0)
        if self.offset < 0:
            raise ValueError("XML set error: offset should >= 0")            
        self.offset_width   = int(self.node_combined.find("offset-width").get("value"),0)
        if self.offset_width < 1 or self.offset_width > 2:
            raise ValueError("XML set error: offset-width should be [1,2]")            
        self.block_size	    = int(self.node_combined.find("block-size").get("value"),0)
        if self.block_size <= 0:
            raise ValueError("XML set error: block_size should > 0")            
        self.number_bytes_to_do = int(self.node_combined.find("number-bytes").get("value"),0)
        if self.number_bytes_to_do <= 0:
            raise ValueError("XML set error: number_bytes should > 0")            
        self.cmd_timeout    = int(self.node_combined.get("timeout"),0)
        if self.cmd_timeout < 0:
            raise ValueError("XML set error: timeout should >= 0")

        #in/out binary-file and binary-data
        temp_file_node=self.node_combined.find("binary-file")
        temp_data_node=self.node_combined.find("binary-data")
        if (temp_file_node is not None) and (temp_data_node is not None):
            raise ValueError("XML set error: binary_file and binary_data can't exist at the same time")
        elif temp_file_node is not None:
            self.binary_file = temp_file_node.get("value")
            if self.node_combined.tag == LsisesVpdReadItem.item_type:
                self.binary_fd = open(self.binary_file, 'w')
            elif self.node_combined.tag == LsisesVpdWriteItem.item_type or self.node_combined.tag == LsisesVpdCheckItem.item_type:
                self.binary_fd = open(self.binary_file, 'r')
            else:
                raise ValueError("XML set error: binary_file tag: in unknow parent item type.")
            if (self.binary_file is None) or (self.binary_fd is None):
                raise ValueError("XML set error: binary_file: '%s' open fail", self.binary_file)
        elif temp_data_node is not None:
            self.binary_data = int(temp_data_node.get("value"),0)
            if self.binary_data < 0 or self.binary_data > 0xff:
                raise ValueError("XML set error: binary_data should >= 0 and <=0xff")
            self.binary_data = "%02x" % (self.binary_data)
        else:
            raise ValueError("XML set error: No binary_file or binary_data set")
        if (self.binary_fd is None) and (self.binary_data is None):
            raise ValueError("XML set error: No binary_file or binary_data set")

        #proxy,uart,port,baudrate,new_line_transmit,end-mark,error-filter
        self.proxy = self.node_combined.get("proxy")
        if self.proxy == "uart":
            uart_node	    = self.node_combined.find("uart")
            self.uart_port  = uart_node.get("port")
            self.uart_baudrate = uart_node.get("baudrate")
            self.uart_newline_transmit = uart_node.get("new_line_transmit")
            for endmark_node in self.node_combined.findall("end-mark"):
                endmark = endmark_node.get("keyword")
                self.endmarks.append(endmark)
            for error_filter_node in self.node_combined.findall("error-filter"):
                error_filter = command.ErrorFilters[error_filter_node.get("type")](
                                                error_filter_node.get("operation"),
                                                error_filter_node.get("value"))
                self.error_filters.append(error_filter)
        elif proxy == "uart-daemon":
            _LOGGER.info("uart-daemon not suppoet")
            return False
        else:
            raise ValueError("Unknown proxy type '%s'", proxy)
        return True

    def read_block(self):
        """    
        return readed length
         > 0, SUCCESS,readed length
         = 0, SUCCESS,EOF
         < 0, ERROR
        """
        remain_bytes = self.number_bytes_to_do - self.number_bytes_done
        if remain_bytes <= 0:
            return 0
        #build and apply cmd
        offset_str = get_offset_bytes(self.offset + self.number_bytes_done, self.offset_width)
        read_bytes = min(self.block_size, remain_bytes)
        cmd = "iicwr" + " " + self.device_addr + " " + (str(self.port_id)) + " " + (str(read_bytes)) + " " + offset_str
        _LOGGER.info("%s ", cmd)
        self.cmd = lsises.LSICommand( cmd, self.uart_port,
                                      self.uart_baudrate, None,
                                      self.uart_newline_transmit,
                                      self.cmd_timeout, None,
                                      self.endmarks, self.error_filters)
        if _UNIT_TEST is not None:
            raw_value = apply()
        else:
            raw_value = self.cmd.apply()
        #convert and check value length
        value = extract_rawdata(raw_value)
        if value == "":
            _LOGGER.info("Error: No value read from UART!") 
            return -1
        ret_bytes = len(value)/2
        if ret_bytes != read_bytes:
            _LOGGER.info("Error: read %d bytes but return %d bytes!", read_bytes, ret_bytes) 
            return -2
        #store value to file
        if self.binary_fd is not None:
            self.binary_fd.write(value)
        self.number_bytes_done += read_bytes
        return read_bytes
            
            
    def write_block(self):
        """    
        return writed length
         > 0, SUCCESS,writen length
        = 0, SUCCESS,EOF
         < 0, ERROR
        """    
        remain_bytes = self.number_bytes_to_do - self.number_bytes_done
        if remain_bytes <= 0:
            return 0
        offset_str = get_offset_bytes(self.offset + self.number_bytes_done, self.offset_width)
        write_bytes = min(self.block_size, remain_bytes)
        
        #build write values
        write_values=""
        if self.binary_fd is not None:
            file_values = self.binary_fd.read(write_bytes * 2)
            write_bytes = len(file_values)
            if write_bytes==0 or write_bytes%2!=0:
                _LOGGER.info("Error: read file return EOF or odd number data:%s", file_values)
                return -1;
            write_bytes /= 2
            for i in range(0, write_bytes):
                write_values += file_values[i*2] + file_values[i*2+1] + " "
        elif self.binary_data != None:
            for i in range(0, write_bytes):
                write_values += self.binary_data + " "
        else:
            _LOGGER.info("Error: No binary_file or binary_data set!")
            return -1
        
        #build and apply cmd        
        cmd = "iicw" + " " + self.device_addr + " " + (str(self.port_id)) + " " + offset_str + " " + write_values
        _LOGGER.info("%s ", cmd)
        self.cmd = lsises.LSICommand( cmd, self.uart_port,
                                      self.uart_baudrate, None,
                                      self.uart_newline_transmit,
                                      self.cmd_timeout, None,
                                      self.endmarks, self.error_filters)
        if _UNIT_TEST is not None:
            raw_value = apply()
        else:
            raw_value = self.cmd.apply()
        
        self.number_bytes_done += write_bytes
        return write_bytes
    
    def check_block(self):
        """    
        return checked length
         > 0, SUCCESS,checked length
         = 0, SUCCESS,EOF
         < 0, ERROR
        """
        remain_bytes = self.number_bytes_to_do - self.number_bytes_done
        if remain_bytes <= 0:
            return 0
        #build and apply cmd
        offset_str = get_offset_bytes(self.offset + self.number_bytes_done, self.offset_width)
        read_bytes = min(self.block_size, remain_bytes)
        cmd = "iicwr" + " " + self.device_addr + " " + (str(self.port_id)) + " " + (str(read_bytes)) + " " + offset_str
        _LOGGER.info("%s ", cmd)
        self.cmd = lsises.LSICommand( cmd, self.uart_port,
                                      self.uart_baudrate, None,
                                      self.uart_newline_transmit,
                                      self.cmd_timeout, None,
                                      self.endmarks, self.error_filters)
        if _UNIT_TEST is not None:
            raw_value = apply()
        else:
            raw_value = self.cmd.apply()
        #convert and check value length
        value = extract_rawdata(raw_value)
        if value == "":
            _LOGGER.info("Error: No value read from UART!") 
            return -1
        ret_bytes = len(value)/2
        if ret_bytes != read_bytes:
            _LOGGER.info("Error: read %d bytes but return %d bytes!", read_bytes, ret_bytes) 
            return -2
        #compare return values
        if self.binary_fd is not None:
            compare_value = self.binary_fd.read(read_bytes * 2)
            if compare_value != value:
                _LOGGER.info("Error: read data differ with file data!")
                _LOGGER.info("Read data: %s", value)
                _LOGGER.info("File data: %s", compare_value)
                return -3
        if self.binary_data != None:
            compare_value=""
            for i in range(0, read_bytes):
                compare_value += self.binary_data
            if compare_value != value:
                _LOGGER.info("Error: read data differ with set binary_data!")
                _LOGGER.info("Read data: %s", value)
                _LOGGER.info("Binary_data: %s", compare_value)
                return -4
        self.number_bytes_done += read_bytes
        return read_bytes
	
#--------------------------------------------------------------------------
#  VPD READ
#--------------------------------------------------------------------------
class LsisesVpdReadItem(testcase.TestItem):
    """
    A LsisesVpdRead instance execute VPD read commands specially for Lsi SES.
    """
    item_type="lsi-vpd-read"

    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.node_combined = None

    def action_init(self, kwargs):
        testcasexml   = kwargs.get("testcase")
        node          = self.parameter.find(self.item_type)
        self.node_combined = analyse_vpd_node(testcasexml, node, self.item_type)
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        cmd = LsisesVpdCmd(self.node_combined)
        try:
            ret = cmd.get_parameters()
            cmd_ret = 1
            while cmd_ret > 0:
                cmd_ret = cmd.read_block()
        except ValueError:
            cmd_ret = -1
        cmd.clear()
        if cmd_ret == 0:
            _LOGGER.info("Read data from eeprom and save succesfully!")
            return True
        else:
            _LOGGER.info("Read data from eeprom and save Faile!")
            return False

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        return True

#--------------------------------------------------------------------------
#  VPD WRITE
#--------------------------------------------------------------------------
class LsisesVpdWriteItem(testcase.TestItem):
    """
    A LsisesVpdWriteItem instance execute Vpd write commands specially for LSI SES.
    """
    item_type          = "lsi-vpd-write"

    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.node_combined = None

    def action_init(self, kwargs):
        testcasexml   = kwargs.get("testcase")
        node          = self.parameter.find(self.item_type)
        self.node_combined = analyse_vpd_node(testcasexml, node, self.item_type)
        return True

    def action_run(self, kwargs):
        """
        Execute the command.
        """
        cmd = LsisesVpdCmd(self.node_combined)
        try:
            ret = cmd.get_parameters()
            cmd_ret = 1
            while cmd_ret > 0:
                cmd_ret = cmd.write_block()
        except ValueError:
            cmd_ret = -1
        cmd.clear()
        if cmd_ret == 0:
            _LOGGER.info("Write data to eeprom succesfully!")
            return True
        else:
            _LOGGER.info("Write data to eeprom Faile!")
            return False

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        return True


#--------------------------------------------------------------------------
#  VPD READ CHECK
#--------------------------------------------------------------------------
class LsisesVpdCheckItem(testcase.TestItem):
    """
    A LsisesVpdCheck instance execute vpd read commands specially for LSI SES, then parse the returned message.
    """
    item_type = "lsi-vpd-check"

    def __init__(self, parameter):
        testcase.TestItem.__init__(self, parameter)
        self.node_combined = None

    def action_init(self, kwargs):
        testcasexml   = kwargs.get("testcase")
        node          = self.parameter.find(self.item_type)
        self.node_combined = analyse_vpd_node(testcasexml, node, self.item_type)
        return True


    def action_run(self, kwargs):
        """
        Execute the command.
        """
        cmd      = LsisesVpdCmd(self.node_combined)
        try:
            ret = cmd.get_parameters()
            cmd_ret = 1
            while cmd_ret > 0:
                cmd_ret = cmd.check_block()
        except ValueError:
            cmd_ret = -1
        cmd.clear()
        if cmd_ret == 0:
            _LOGGER.info("Read data from eeprom and check data succesfully!")
            return True
        else:
            _LOGGER.info("Read data from eeprom and check data Faile!")
            return False

    def action_clear(self, kwargs):
        return True

    def action_print_parameter(self, kwargs):
        testcase = kwargs.get("testcase")
        return True
