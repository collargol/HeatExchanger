import ClientServerClasses


receiver1 = ClientServerClasses.Receiver('192.168.0.108', 5555, 'receiver1')
#heatExchanger = ClientServerClasses.Receiver('192.168.0.15', 503, 'Heat exchanger')

watchmaker = ClientServerClasses.Watchmaker()
watchmaker.add_receiver(receiver1)
#watchmaker.add_receiver(heatExchanger)
watchmaker.keep_connecting()
watchmaker.detonate()

close = False
while not close:
    try:
        input_str = input('>>')
        if input_str == 'set info':
            ClientServerClasses.logger.setLevel(ClientServerClasses.logging.INFO)
        elif input_str == 'set error':
            ClientServerClasses.logger.setLevel(ClientServerClasses.logging.ERROR)
        else:
            boost_factor = float(input_str)
            watchmaker.set_boost_factor(boost_factor)

    except ValueError:
        print('Boost factor must be a number')
    except KeyboardInterrupt:
        close = True

watchmaker.disconnect()

print('Done')