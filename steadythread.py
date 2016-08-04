#! python2
# -*- coding:utf-8 -*-
"""固定线程"""
import threading
import time


class MyThread(threading.Thread):
    def __init__(self, thread_id, name, counter):
        super(MyThread, self).__init__()  # 调用父类的构造函数
        self.thread_id = thread_id
        self.name = name
        self.counter = counter

    def run(self):
        print('Starting'+self.name)
        print_time(self.name, self.counter, 5)
        print('Exiting'+self.name)


def print_time(thread_name, delay, counter):
    while counter:
        time.sleep(delay)
        print('%s %s' % (thread_name, time.ctime(time.time)))
        counter -= 1


def main():
    """创建新的线程"""
    thread1 = MyThread(1, 'Thread-1', 1)
    thread2 = MyThread(2, 'Thread-2', 2)

    """开启线程"""
    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
    print('Exiting Main Thread')


if __name__ == '__main__':
    main()


