from pymodbus.server.sync import StartTcpServer
from pymodbus.server.sync import ModbusTcpServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

import time
import datetime
import threading
import logging

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

time_address = 1
ready_flag_address = 1


def print_time(timestamp):
    print(datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'))


class DataBlock(ModbusSparseDataBlock):

    def __init__(self, values):
        super(DataBlock, self).__init__(values)
        self.time = 0
        self.__time_callback__ = None

    def setValues(self, address, values):
        super(DataBlock, self).setValues(address, values)

        if address == time_address:
            self.time = self.__calculate_timestamp__(values)
            self.__time_callback__(self.time)

    def set_time_callback(self, function):
        self.__time_callback__ = function

    @staticmethod
    def __calculate_timestamp__(register_values):
        time1 = register_values[0]
        time2 = register_values[1]
        return (time1 << 16) | time2


class CoilBlock(ModbusSparseDataBlock):

    def setValues(self, address, values):
        super(CoilBlock, self).setValues(address, values)


class Server:
    def __init__(self, address, port, block_size):
        self.holding_register_block = DataBlock([0] * block_size)
        self.coil_block = CoilBlock([0] * block_size)
        self.input_register_block = ModbusSparseDataBlock([0] * block_size)
        self.digital_input_block = ModbusSparseDataBlock([0] * block_size)
        self.store = ModbusSlaveContext(di=self.digital_input_block,
                                        co=self.coil_block,
                                        hr=self.holding_register_block,
                                        ir=self.input_register_block)
        self.context = ModbusServerContext(slaves=self.store, single=True)
        self.server = ModbusTcpServer(self.context, address=(address, port))
        self.thread = threading.Thread(target=self.__run_thread__, args=())
        self.__time_callback__ = None

    def __run_thread__(self):
        self.server.serve_forever()

    def run(self):
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.thread.join()

    def set_time_callback(self, function):
        self.holding_register_block.set_time_callback(function)

    def set_ready_flag(self):
        self.coil_block.setValues(ready_flag_address, True)

# set proper IP address and port number!
server = Server("", 502, 1000)
server.set_time_callback(print_time)
server.run()
print("Server's running...")

close = False
while not close:
    try:
        time.sleep(0.001)
        server.set_ready_flag()
    except KeyboardInterrupt:
        print("Interruption from keyboard occurred")
        close = True

server.stop()
print("Server stopped")

