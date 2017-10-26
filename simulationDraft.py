import matplotlib.pyplot as plt
import numpy as np
import time
from threading import Thread


def fun1():
    for i in range(5):
        time.sleep(1)
        print('fun1')


def fun2():
    for i in range(5):
        time.sleep(2)
        print('fun2')


if __name__ == '__main__':
    Thread(target=fun1()).start()
    Thread(target=fun2()).start()
