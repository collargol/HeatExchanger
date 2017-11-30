# for server==receiver
from __future__ import print_function
from pymodbus.server.sync import ModbusTcpServer
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

from threading import Thread
import _thread
import datetime
import subprocess
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

value_address = 300
time_address = 1
ready_flag_address = 1


class HoldingRegisterDataBlock(ModbusSparseDataBlock):

    def __init__(self, values):
        super(HoldingRegisterDataBlock, self).__init__(values)
        self.timestamp = 0
        self.time_callback = None
        self.value_callback = 300

    def setValues(self, address, values):
        super(HoldingRegisterDataBlock, self).setValues(address, values)
        if address == time_address:
            print('Time changed!')
            t = threading.Thread(target=self.time_callback)
            t.start()
        elif address == value_address or address == value_address + 1:
            print('Value changed!')
            # t = threading.Thread(target=self.value_callback, args=(address,))
            # t.start()

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
        ts = HoldingRegisterDataBlock.__calculate_timestamp__([self.holding_register_block.getValues(1)[0], self.holding_register_block.getValues(2)[0]])
        values.append(ts)                                             # time

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
        self.initialization = False


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
        self.receiving_server = None
        # flag if values should be pushed do receivers
        self.ready_to_send = False
        # received values
        self.T_pco = 0
        self.F_zm = 0
        self.T_zm = 0
        self.T_o = 0
        self.time = 0
        self.time_previous = 0
        self.time_actual = 0
        # values to send
        self.T_zco = 28800
        self.T_pm = 28800    # should be const?
        # constants
        self.M_m = 3000
        self.M_co = 3000
        self.c_wym = 2700
        self.c_w = 4200
        self.rho = 1000
        self.k_w = 250000
        self.F_zco = 0.035
        # F_zm = 0.015
        # running simulation to create file for data
        args = ['wymiennik.exe', '0']
        subprocess.call(args)


    def set_boost_factor(self, factor):
        self.boost_factor = factor

    def add_receiver(self, receiver):
        self.receivers.append(receiver)

    def set_values(self, values):
        self.T_pco = values[0] / 100    # scaling here? probably /100
        self.F_zm = values[1] / 1000000 # ????
        self.T_zm = values[2] / 100
        self.T_o = values[3] / 100
        self.time = values[4]
        f = open('heat_exchanger_data.txt', 'r')
        content = f.readlines()
        f.close()
        f = open('heat_exchanger_data.txt', 'w')
        f.writelines([str(self.F_zco) + '\n', str(self.F_zm) + '\n', str(self.T_pco) + '\n', str(self.T_zm) + '\n'])
        f.writelines(content[4:])
        f.close()

    def calculate_values_to_send(self):
        self.time_previous = self.time_actual
        self.time_actual = self.time
        delta_t = int(self.time_actual - self.time_previous)
        args = ['wymiennik.exe', str(delta_t)]
        subprocess.call(args)
        f = open('heat_exchanger_data.txt', 'r')
        content = f.readlines()
        f.close()
        self.T_pm = int(100 * float(content[4]))
        self.T_zco = int(100 * float(content[5]))
        '''
        if delta_t > 1000:
            print('Program works slow af')
            delta_t = 1.0
        print('delta: ' + str(delta_t))
        dt = 1.0
        for i in range(int(delta_t)):
            # should replace dt by delta_t
            T_zco_temp = self.T_zco / 100 + dt * (((-self.F_zm * self.rho * self.c_w) / (self.M_m * self.c_wym)) * (self.T_zco / 100 - self.T_pco) + (self.k_w / (self.M_m * self.c_wym)) * (self.T_pm / 100 - self.T_zco / 100))
            T_pm_temp = self.T_pm / 100 + dt * (((self.F_zco * self.rho * self.c_w) / (self.M_m * self.c_wym)) * (self.T_zm - self.T_pm / 100) + (-self.k_w / (self.M_m * self.c_wym)) * (self.T_pm / 100 - self.T_zco / 100))
            self.T_zco = int(round(T_zco_temp * 100))
            # self.T_zco += 1       # to connection tests only
            self.T_pm = int(round(T_pm_temp * 100))
        print(self.T_zco)
        '''

    def keep_connecting(self):
        for receiver in self.receivers:
            if not receiver.connect():
                log_error('Error: cannot connect with ' + receiver.get_name())
        if not self.stop:
            self.connect_timer = threading.Timer(10, self.keep_connecting)  # new thread starting every 10s
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
            self.set_values(self.receiving_server.read_values())
            if self.ready_to_send:
                print('Values can be send')
                self.calculate_values_to_send()
                for receiver in self.receivers:
                    if not receiver.connected():
                        continue
                    print('sending to some receiver...')

                    if 'Building' in receiver.name:
                        print('sending to ' + receiver.name)
                        receiver.write_value(200, int(self.T_zco))
                    if 'Regulator' in receiver.name:
                        print('sending to ' + receiver.name)
                        receiver.write_value(200, int(self.T_zco))
                    if 'Logger' in receiver.name:
                        print('sending to ' + receiver.name)
                        receiver.write_value(200, int(self.T_zco))
                        # receiver.write_value(   , int(self.T_pm))
                    # what about T_pm value?
                    #
                self.ready_to_send = False
                self.receiving_server.set_ready_flag()
            # else:
               # print('Cannot send values')
        except Exception as e:
            print(e)
            self.ready_to_send = False
        except ConnectionException:
            log_error('Error: Connection lost with')
        if not self.stop:
            # running new thread
            # self.sending_timer = threading.Timer(0.2, self.send_values_to_receivers)
            # self.sending_timer.start()
            t = threading.Thread(target=self.send_values_to_receivers)
            t.start()

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