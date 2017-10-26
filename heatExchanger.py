from pymodbus.server.sync import StartTcpServer
from pymodbus.server.sync import ModbusTcpServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

import time
import datetime
import threading
import _thread
import logging

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

time_address = 1
ready_flag_address = 1


def print_time(timestamp):
    print(datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'))


class HoldingRegisterDataBlock(ModbusSparseDataBlock):

    def __init__(self, values):
        super(HoldingRegisterDataBlock, self).__init__(values)
        self.timestamp = 0
        self.__time_callback__ = None

    def setValues(self, address, values):
        super(HoldingRegisterDataBlock, self).setValues(address, values)
        if address == time_address:
            self.timestamp = self.__calculate_timestamp__(values)
            _thread.start_new_thread(self.time_callback, (self.timestamp, ))

    def set_time_callback(self, function):
        self.time_callback = function

    def get_time(self):
        return self.timestamp

    @staticmethod
    def __calculate_timestamp__(register_values):
        time1 = register_values[0]
        time2 = register_values[1]
        return (time1 << 16) | time2


class Server:
    def __init__(self, address, port):
        self.holding_register_block = HoldingRegisterDataBlock.create()
        self.coil_block = ModbusSparseDataBlock.create()
        self.input_register_block = ModbusSparseDataBlock.create()
        self.store = ModbusSlaveContext(co=self.coil_block, hr=self.holding_register_block)
        self.context = ModbusServerContext(slaves=self.store, single=True)
        self.server = ModbusTcpServer(self.context, address=(address, port))
        self.thread = threading.Thread(target=self.__run_thread__, args=())

    def __run_thread__(self):
        self.server.serve_forever()

    def run(self):
        self.thread.start()

    def stop(self):
        self.server.server_close()
        self.server.shutdown()
        self.thread.join()

    def set_time_callback(self, function):
        self.holding_register_block.set_time_callback(function)

    def set_ready_flag(self):
        self.coil_block.setValues(ready_flag_address, True)

    def get_time(self):
        return self.holding_register_block.get_time()

# starting server
# set proper IP address and port number:
server = Server("", 502, 1000)
# set callback function
server.set_time_callback(print_time)
server.run()
print('Server is running...')

#
# if some setup will be necessary it should be placed here I think...
#

close = False
while not close:
    try:
        # getting actual time
        print('Reading time value...')
        current_time_value = server.get_time()
        print('Current time value: ' + str(current_time_value))
        #
        # model simulation should be performed here
        # receiving data from other systems should also be placed here (data for simulation)
        #
        time.sleep(0.5)
        # setting this flag is crucial for time provider!
        server.set_ready_flag()
    except KeyboardInterrupt:
        print('Interruption from keyboard occurred')
        close = True
try:
    server.stop()
    print('Server stopped')
except:
    print('Issues while closing server')


