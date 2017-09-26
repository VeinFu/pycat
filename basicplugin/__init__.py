from pycat import testcase
import command
import acsource
import bbu
import osdev
import sescmd
import i2ccmd
import fpgadev
import sglareboot
import parallelcommand
import packageloss

#---------------------------------------------------------------------------
# Basic Test Case
#---------------------------------------------------------------------------
class BasicTestCase(testcase.TestCase):
    case_type = "basic"
    def __init__(self, config):
        testcase.TestCase.__init__(self, config)
        items = {
            command.CommandItem.item_type: command.CommandItem,
            parallelcommand.ParrallelCommandItem.item_type: parallelcommand.ParrallelCommandItem,
            packageloss.PackageLossItem.item_type: packageloss.PackageLossItem,
            acsource.ACSourceItem.item_type: acsource.ACSourceItem,
            bbu.BBUMonitorItem.item_type: bbu.BBUMonitorItem,
            osdev.DeviceHddItem.item_type: osdev.DeviceHddItem,
            osdev.DeviceMemItem.item_type: osdev.DeviceMemItem,
            osdev.DeviceNetifItem.item_type: osdev.DeviceNetifItem,
            osdev.DevicePciItem.item_type: osdev.DevicePciItem,
            osdev.DeviceScsiItem.item_type: osdev.DeviceScsiItem,
            osdev.MemoryDumpItem.item_type: osdev.MemoryDumpItem,
            osdev.FileCheckSumItem.item_type: osdev.FileCheckSumItem,
            i2ccmd.I2CReadCheckItem.item_type: i2ccmd.I2CReadCheckItem,
            fpgadev.CommandsensorItem.item_type: fpgadev.CommandsensorItem,
            fpgadev.CommandpcieItem.item_type: fpgadev.CommandpcieItem,
            fpgadev.CommandmemItem.item_type: fpgadev.CommandmemItem,
            sglareboot.CommandrebootItem.item_type: sglareboot.CommandrebootItem,
            sglareboot.CommandpingItem.item_type: sglareboot.CommandpingItem,
            sglareboot.CommandchkpoweroffItem.item_type: sglareboot.CommandchkpoweroffItem
        }
        self.update_items(items)


CASES = {
    BasicTestCase.case_type: BasicTestCase
}

def find_testcase(name):
    if name in CASES.keys():
        case = CASES[name]
        return case
    else:
       raise ValueError("Unknown test case '%s'" % name)

