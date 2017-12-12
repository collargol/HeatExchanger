import ClientServerClasses
import time


# creating new server
server = ClientServerClasses.Server('192.168.1.69', 5555)   # should be 192.168.1.69 for Heat Exchanger
# run the server
server.run()
print('Server is running')
# creating client
sender = ClientServerClasses.Sender()
sender.receiving_server = server
building0 = ClientServerClasses.Receiver('192.168.1.201', 5555, 'Building Jan')
building1 = ClientServerClasses.Receiver('192.168.1.202', 5555, 'Building Dominik')
building2 = ClientServerClasses.Receiver('192.168.1.203', 5555, 'Building Artur')
building3 = ClientServerClasses.Receiver('192.168.1.204', 5555, 'Building Adam')
regulator = ClientServerClasses.Receiver('192.168.1.111', 5555, 'Regulator')    # should be 192.168.1.111 5555
dataLogger = ClientServerClasses.Receiver('192.168.1.222', 5555, 'Logger')
# heatProvider = ClientServerClasses.Receiver('192.168.1.13', 5555, 'Heat provider')

sender.add_receiver(building0)
sender.add_receiver(building1)
sender.add_receiver(building2)
sender.add_receiver(building3)
sender.add_receiver(regulator)
sender.add_receiver(dataLogger)
# sender.add_receiver(heatProvider)

sender.keep_connecting()
sender.send_values_to_receivers()

# server.set_time_callback(ClientServerClasses.print_time)
server.set_time_callback(sender.server_ready_to_send)

#############################

close = False
while not close:
    try:
        continue
        # reading T_pco, F_zm, T_zm, T_o values 4 times per second and sending them to sender class
        # print('reading values...')
        # print(server.holding_register_block.getValues(301))
        # sender.set_values(server.read_values())
        # print(server.holding_register_block.getValues(301))
        # time.sleep(0.25)
        # let know that you are ready for receive time
        # server.set_ready_flag()
    except KeyboardInterrupt:
        close = True

# remember to stop server while closing your application
server.stop()
sender.disconnect()
print('finished!')
