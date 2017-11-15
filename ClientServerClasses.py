# for server==receiver
from __future__ import print_function
from pymodbus.server.sync import ModbusTcpServer
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

from threading import Thread
import _thread
import datetime
#
# for client==sender
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ConnectionException
import threading
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

##########################
# server-receiver part
##########################


def print_time(timestamp):
    print('yoo!')
    print(datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'))

value_address = 201
time_address = 1
ready_flag_address = 1


class HoldingRegisterDataBlock(ModbusSparseDataBlock):

    def __init__(self, values):
        super(HoldingRegisterDataBlock, self).__init__(values)
        self.timestamp = 0
        self.time_callback = None
        self.value_callback = None

    def setValues(self, address, values):
        super(HoldingRegisterDataBlock, self).setValues(address, values)
        if address == time_address:
            t = threading.Thread(target=self.time_callback)
            t.start()
        elif address == value_address:
            print('Value changed!')
            t = threading.Thread(target=self.value_callback, args=(address,))
            t.start()

    def set_time_callback(self, function):
        self.time_callback = function

    def set_value_callback(self, function):
        self.value_callback = function

    def get_time(self):
        return self.timestamp

    def show_received_value(self, address):
        print('New value received ' + str(self.getValues(address)))

    @staticmethod
    def __calculate_timestamp__(register_values):
        time1 = register_values[0]
        time2 = register_values[1]
        return (time1 << 16) | time2


class Server:

    def __init__(self, address, port):
        self.holding_register_block = HoldingRegisterDataBlock.create()
        self.coil_block = ModbusSparseDataBlock.create()
        self.store = ModbusSlaveContext(hr=self.holding_register_block, co=self.coil_block)
        self.context = ModbusServerContext(slaves=self.store, single=True)
        self.server = ModbusTcpServer(self.context, address=(address, port))
        self.thread = Thread(target=self.__run_thread__, args=())

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

    def set_value_callback(self, function):
        self.holding_register_block.set_value_callback(function)

    def set_ready_flag(self):
        self.coil_block.setValues(ready_flag_address, True)

    def get_time(self):
        return self.holding_register_block.get_time()

    def read_values(self):
        values = []
        # reading incremented addresses because registers' addressing is fu..d up :/
        values.append(self.holding_register_block.getValues(303)[0])  # T_pco
        values.append(self.holding_register_block.getValues(301)[0])  # F_zm
        values.append(self.holding_register_block.getValues(103)[0])  # T_zm
        values.append(self.holding_register_block.getValues(101)[0])  # T_o
        # values.append(self.holding_register_block.getValues(302))   # T_pco
        # values.append(self.holding_register_block.getValues(300))   # F_zm
        # values.append(self.holding_register_block.getValues(102))  # T_zm
        # values.append(self.holding_register_block.getValues(100))  # T_o
        return values

#################################
# client-sender part
#################################


def log_error(message):
    logger.error(message + '\n>>')


def log_warning(message):
    logger.warning(message + '\n>>')


def log_info(message):
    logger.info(message + '\n>>')


class Receiver(ModbusTcpClient):

    time_address = 0
    ready_flag_address = 0

    def __init__(self, host, port, name):
        super(Receiver, self).__init__(host, port)
        self.name = name
        self.initialization = True
        self.id = 0

    def connected(self):
        return self.socket

    def get_name(self):
        return self.name

    def is_ready(self):
        return self.read_coils(self.ready_flag_address).bits[0] or self.initialization

    def reset_ready_flag(self):
        if self.connected():
            self.write_coil(self.ready_flag_address, False)

    def write_time(self, time_value):
        time_ms16b = (time_value >> 16) & 0xffff
        time_ls16b = time_value & 0xffff
        self.write_registers(self.time_address, [time_ms16b, time_ls16b])
        self.initialization = False

    def write_id(self, id_value):
        self.write_registers(1, id_value)

    def write_value(self, address, value):
        self.write_registers(address, value)


class Watchmaker:

    def __init__(self):
        self.receivers = []
        self.timestamp = 1260489600  # 2009-12-11 00:00
        self.id = 0
        self.value_to_send = 0
        self.stop = False
        self.boost_factor = 1.0
        self.connect_timer = None
        self.sending_timer = None
        # flag if values should be pushed do receivers
        self.ready_to_send = False
        # received values
        self.T_pco = 0
        self.F_zm = 0
        self.T_zm = 0
        self.T_o = 0
        # values to send
        self.T_zco = 15 * 100
        self.T_pm = 15 * 100
        # constants
        self.M_m = 3000
        self.M_co = 3000
        self.c_wym = 2700
        self.c_w = 4200
        self.rho = 1000
        self.k_w = 250000
        # F_zm = ???

    def set_boost_factor(self, factor):
        self.boost_factor = factor

    def add_receiver(self, receiver):
        self.receivers.append(receiver)

    def set_values(self, values):
        self.T_pco = values[0]  # scaling here?
        self.F_zm = values[1] / 1000000
        self.T_zm = values[2] / 100
        self.T_o = values[3] / 100

    def calculate_values_to_send(self):
        delta_t = 1.0;
        T_zco_temp = self.T_zco + delta_t * (((-self.F_zm * self.rho * self.c_w) / (self.M_m * self.c_wym)) * (self.T_zco - self.T_pco) + (self.k_w / (self.M_m * self.c_wym)) * (self.T_pm - self.T_zco))
        T_pm_temp = self.T_pm + delta_t * (((self.F_zm * self.rho * self.c_w) / (self.M_m * self.c_wym)) * (self.T_zm - self.T_pm) + (-self.k_w / (self.M_m * self.c_wym)) * (self.T_pm - self.T_zco))
        self.T_zco = T_zco_temp * 100
        self.T_pm = T_pm_temp * 100

    def keep_connecting(self):
        for receiver in self.receivers:
            if not receiver.connect():
                log_error('Error: cannot connect with ' + receiver.get_name())
        if not self.stop:
            self.connect_timer = threading.Timer(10, self.keep_connecting) # new thread starting here for 10s
            self.connect_timer.start()

    def disconnect(self):
        log_info('Closing connection')
        self.stop = True
        self.connect_timer.cancel()
        self.sending_timer.cancel()
        for receiver in self.receivers:
            receiver.close()

    def receivers_ready(self):
        ready = True
        for receiver in self.receivers:
            if receiver.connected():
                ready = ready and receiver.is_ready()
                if not ready:
                    log_warning('{} is slowing down'.format(receiver.get_name()))
        return ready

    def reset_ready_flags(self):
        for receiver in self.receivers:
            receiver.reset_ready_flag()

    def detonate(self):
        try:
            if (not self.receivers_ready()) and (not self.stop):
                self.schedule_time_sending()
                return
            for receiver in self.receivers:
                if not receiver.connected():
                    continue
                receiver.write_time(self.timestamp)

            self.timestamp += 1
            self.reset_ready_flags()

        except ConnectionException:
            log_error('Error: Connection lost')
        if not self.stop:
            self.schedule_time_sending()    # running new thread

    def server_ready_to_send(self):
        print('callback called!')

        self.ready_to_send = True

    def send_values_to_receivers(self):
        try:
            if self.ready_to_send:
                print('Values can be send')
                for receiver in self.receivers:
                    # if not receiver.connected():
                    #     continue
                    #
                    print('sending to some receiver...')
                    if 'Building' in receiver.name:
                        print('sending to building')
                        receiver.write_value(200, self.T_zco)
                    if 'Regulator' in receiver.name:
                        print('sending to regulator')
                        receiver.write_value(200, self.T_zco)
                    # what about T_pm value?
                    #
                self.ready_to_send = False
            else:
                print('Cannot send values')
        except ConnectionException:
            log_error('Error: Connection lost with')
        if not self.stop:
            # running new thread
            self.sending_timer = threading.Timer(0.2, self.send_values_to_receivers)
            self.sending_timer.start()

    def schedule_time_sending(self):
        self.sending_timer = threading.Timer(1.0 / self.boost_factor, self.detonate)
        self.sending_timer.start()

    def schedule_id_sending(self):
        self.sending_timer = threading.Timer(1.0 / self.boost_factor, self.detonate_id)
        self.sending_timer.start()

    def schedule_value_sending(self):
        self.sending_timer = threading.Timer(1.0 / self.boost_factor, self.detonate_new_value)
        self.sending_timer.start()


######################