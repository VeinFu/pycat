#! /usr/bin/python


from  basicplugin import sescmd
#--------------------------------------------------------------------------
#  SES Command Executor
#--------------------------------------------------------------------------
class LSICommand(sescmd.SESCommandUart):
    def __init__(self, cmd, port, baudrate, timeout=None, end_of_line=None, cmd_timeout=None, recv=None, endmarks=None, error_filters=None):
        sescmd.SESCommandUart.__init__(self, cmd, port, baudrate, timeout, end_of_line, cmd_timeout, recv, endmarks, error_filters)

    def show(self):
        pass

