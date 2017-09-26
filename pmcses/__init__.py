from pycat import testcase
import pmcsesI2C
import pmcsesFW
import pmcsesVpd
import pmcsesPowercycle
import pmcsesPowercycle2
from basicplugin import command, acsource, osdev, bbu, sescmd, i2ccmd



#---------------------------------------------------------------------------
# Basic Test Case
#---------------------------------------------------------------------------
class PmcsesTestCase(testcase.TestCase):
    case_type = "pmcses"
    def __init__(self, config):
        testcase.TestCase.__init__(self, config)
        items = {
            pmcsesI2C.PmcsesI2CReadItem.item_type: pmcsesI2C.PmcsesI2CReadItem,
            pmcsesI2C.PmcsesI2CWriteItem.item_type: pmcsesI2C.PmcsesI2CWriteItem,
            pmcsesI2C.PmcsesI2CReadCheckItem.item_type: pmcsesI2C.PmcsesI2CReadCheckItem,
            pmcsesFW.SESComfwcheckItem.item_type: pmcsesFW.SESComfwcheckItem,
            pmcsesFW.SESComcpldcheckItem.item_type: pmcsesFW.SESComcpldcheckItem,
            pmcsesVpd.PmcsesVpdReadItem.item_type: pmcsesVpd.PmcsesVpdReadItem,
            pmcsesVpd.PmcsesVpdWriteItem.item_type: pmcsesVpd.PmcsesVpdWriteItem,
            pmcsesVpd.PmcsesVpdCheckItem.item_type: pmcsesVpd.PmcsesVpdCheckItem,
            pmcsesFW.Diagfwprogram.item_type: pmcsesFW.Diagfwprogram,
            pmcsesPowercycle.SESComphycheckItem.item_type: pmcsesPowercycle.SESComphycheckItem, 
            pmcsesPowercycle2.SESComphycheckItem2.item_type: pmcsesPowercycle2.SESComphycheckItem2, 
            command.CommandItem.item_type: command.CommandItem,
            acsource.ACSourceItem.item_type: acsource.ACSourceItem,
            bbu.BBUMonitorItem.item_type: bbu.BBUMonitorItem,
            osdev.DeviceHddItem.item_type: osdev.DeviceHddItem,
            osdev.DeviceNetifItem.item_type: osdev.DeviceNetifItem,
            osdev.DevicePciItem.item_type: osdev.DevicePciItem,
            osdev.DeviceScsiItem.item_type: osdev.DeviceScsiItem,
            osdev.MemoryDumpItem.item_type: osdev.MemoryDumpItem,
            osdev.FileCheckSumItem.item_type: osdev.FileCheckSumItem,
            sescmd.SESCommandItem.item_type: sescmd.SESCommandItem,
            sescmd.SESCommandchkfixItem.item_type: sescmd.SESCommandchkfixItem,
            sescmd.SESCommandchkfirstItem.item_type: sescmd.SESCommandchkfirstItem,
            i2ccmd.I2CReadCheckItem.item_type: i2ccmd.I2CReadCheckItem,
            pmcsesPowercycle.SESCommandchkhddtempItem.item_type: pmcsesPowercycle.SESCommandchkhddtempItem,
            pmcsesPowercycle.SESCommandchkhddrateItem.item_type: pmcsesPowercycle.SESCommandchkhddrateItem,
            pmcsesPowercycle.SESCommandchkfrugetItem.item_type: pmcsesPowercycle.SESCommandchkfrugetItem,
            pmcsesPowercycle.SESCommandchkfanspdItem.item_type: pmcsesPowercycle.SESCommandchkfanspdItem
        }
        self.update_items(items)


CASES = {
    PmcsesTestCase.case_type: PmcsesTestCase
}

def find_testcase(name):
    if name in CASES.keys():
        case = CASES[name]
        return case
    else:
       raise ValueError("Unknown test case '%s'" % name)

