import ClientServerClasses


receiver1 = ClientServerClasses.Receiver('192.168.0.108', 5555, 'receiver1')
#heatExchanger = ClientServerClasses.Receiver('192.168.0.15', 503, 'Heat exchanger')

sender = ClientServerClasses.Sender()
sender.add_receiver(receiver1)
#sender.add_receiver(heatExchanger)
sender.keep_connecting()
sender.detonate()

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
            sender.set_boost_factor(boost_factor)

    except ValueError:
        print('Boost factor must be a number')
    except KeyboardInterrupt:
        close = True

sender.disconnect()

print('Done')