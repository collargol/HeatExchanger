import ClientServerClasses
import time


# creating new server
server = ClientServerClasses.Server('192.168.0.108', 5555)   # should be 192.168.1.69 for Heat Exchanger
# run the server
server.run()
print('Server is running')
# creating client
watchmaker = ClientServerClasses.Watchmaker()
# building1 = ClientServerClasses.Receiver('192.168.1.201', 5555, 'Building Jan')
# building2 = ClientServerClasses.Receiver('192.168.1.202', 5555, 'Building Dominik')
# building3 = ClientServerClasses.Receiver('192.168.1.203', 5555, 'Building Artur')
# building4 = ClientServerClasses.Receiver('192.168.1.204', 5555, 'Building Adam')
regulator = ClientServerClasses.Receiver('192.168.0.108', 5556, 'Regulator')
# heatProvider = ClientServerClasses.Receiver('192.168.1.13', 5555, 'Heat provider')

# watchmaker.add_receiver(building1)
# watchmaker.add_receiver(building1)
# watchmaker.add_receiver(building1)
# watchmaker.add_receiver(building1)
watchmaker.add_receiver(regulator)
# watchmaker.add_receiver(heatProvider)

watchmaker.keep_connecting()
watchmaker.send_values_to_receivers()

# server.set_time_callback(ClientServerClasses.print_time)
server.set_time_callback(watchmaker.server_ready_to_send)

#############################

close = False
while not close:
    try:
        # reading T_pco, F_zm, T_zm, T_o values and sending them to sender class
        print('reading values...')
        watchmaker.set_values(server.read_values())
        print('calculating new values...')
        # watchmaker.calculate_values_to_send() # calculating values only when watchmaker is ready!
        # timeValue = server.get_time()
        # print(server.holding_register_block.getValues(300))
        # print(server.holding_register_block.getValues(301))
        # print(server.holding_register_block.getValues(302))
        # print(server.holding_register_block.getValues(303))
        # print(watchmaker.ready_to_send)
        # print(server.holding_register_block.getValues(0))
        # print(server.holding_register_block.getValues(1))
        # print(server.holding_register_block.getValues(2))
        time.sleep(0.5)
        # let know that you are ready for receive time
        server.set_ready_flag()
    except KeyboardInterrupt:
        close = True

# remember to stop server while closing your application
server.stop()
watchmaker.disconnect()
print('finished!')
