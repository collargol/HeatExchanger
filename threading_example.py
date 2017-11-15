import threading
import time


class Foo:

    def __init__(self):
        self.counter = 0

    def increment_counter(self):
        self.counter = input('provide counter value: ')
        print('you provide value ' + str(self.counter))
        t = threading.Thread(target=self.increment_counter)
        time.sleep(2.0)
        t.start()
        # t = threading.Timer(10.0, self.increment_counter)
        # t.start()

    def show_3_times_counter(self):
        print('here is th counter value:' + str(self.counter))
        t = threading.Timer(1.0, self.show_3_times_counter)
        t.start()


F = Foo()
F.increment_counter()
F.show_3_times_counter()
