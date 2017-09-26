from pycat import testcase
import lsisesI2C
import lsisesFW
import lsisesPower_cycle
import lsisesVPD
from basicplugin import command, acsource, osdev, bbu, sescmd, i2ccmd


#---------------------------------------------------------------------------
# Basic Test Case
#---------------------------------------------------------------------------
class LsisesTestCase(testcase.TestCase):
    case_type = "lsises"
    def __init__(self, config):
        testcase.TestCase.__init__(self, config)
        items = {
            lsisesI2C.LsisesI2CReadCheckItem.item_type: lsisesI2C.LsisesI2CReadCheckItem,
            lsisesI2C.LsisesI2CWriteReadCheckItem.item_type: lsisesI2C.LsisesI2CWriteReadCheckItem,
            lsisesFW.SESComfwcheckItem.item_type: lsisesFW.SESComfwcheckItem,
            lsisesFW.Diagfwprogram.item_type: lsisesFW.Diagfwprogram,
            lsisesPower_cycle.SESComphycheckItem.item_type: lsisesPower_cycle.SESComphycheckItem,
            lsisesVPD.LsisesVpdReadItem.item_type: lsisesVPD.LsisesVpdReadItem,
            lsisesVPD.LsisesVpdWriteItem.item_type: lsisesVPD.LsisesVpdWriteItem,
            lsisesVPD.LsisesVpdCheckItem.item_type: lsisesVPD.LsisesVpdCheckItem,

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
            i2ccmd.I2CReadCheckItem.item_type: i2ccmd.I2CReadCheckItem
        }
        self.update_items(items)


CASES = {
    LsisesTestCase.case_type: LsisesTestCase
}

def find_testcase(name):
    if name in CASES.keys():
        case = CASES[name]
        return case
    else:
       raise ValueError("Unknown test case '%s'" % name)

