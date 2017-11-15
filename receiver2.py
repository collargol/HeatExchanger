import ClientServerClasses
import time
# -------------------------------------------
# ----------------- Example usage-------------
# --------------------------------------------
# start new server
server = ClientServerClasses.Server('192.168.0.108', 5556)
# add a callback function which will be called with new timestamp each time new time is received
server.set_time_callback(ClientServerClasses.print_time)
server.set_value_callback(server.holding_register_block.show_received_value)
# run the server
server.run()
print('Server is running')

# do whatever you want

close = False
while not close:
    try:
        # of course you can also read the timestamp any time you want
        print(server.holding_register_block.getValues(200))
        print(server.holding_register_block.getValues(201))
        print('nothing to do...')
        time.sleep(0.5)
        # set ready flag when you finish your job! it is really very important
        server.set_ready_flag()
    except KeyboardInterrupt:
        close = True


# remember to stop server while closing your application
server.stop()

print('finished!')