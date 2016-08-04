#! python2
# -*- coding:utf-8 -*-
import re
import json
import time
import sys
import threading
import Queue
import requests
from datetime import timedelta
from dateutil.parser import parse
from pyquery import PyQuery as pq

"""一般来说，使用线程有两种模式, 一种是创建线程要执行的函数, 把这个函数传递进Thread对象里，
让它来执行. 另一种是直接从Thread继承，创建一个新的class，把线程执行的代码放到这个新的class里,
1.在构造函数中传入用于线程运行的函数(这种方式更加灵活)
2.在子类中重写threading.Thread基类中run()方法(只重写__init__()和run()方法)"""

"""关于守护进程的一些知识:A thread can be flagged as a "daemon thread".
 The significance of this flag is that the entire Python program exits when only daemon threads are left.
  The initial value is inherited from the creating thread."""

"""Some threads do background tasks, like sending keepalive packets, or performing periodic garbage collection,
or whatever. These are only useful when the main program is running,
 and it's okay to kill them off once the other, non-daemon, threads have exited."""

"""Without daemon threads, you'd have to keep track of them, and tell them to exit,
 before your program can completely quit. By setting them as daemon threads, you can let them run and forget about them,
 and when your program quits, any daemon threads are killed automatically."""

"""A boolean value indicating whether this thread is a daemon thread (True) or not (False).
This must be set before start() is called, otherwise RuntimeError is raised.
Its initial value is inherited from the creating thread;
the main thread is not a daemon thread and therefore all threads created in the main thread default to daemon = False.
The entire Python program exits when no alive non-daemon threads are left."""

"""setDaemon:主线程A启动了子线程B,调用b,setDaemon(True),这主线程结束时，会把子线程B也杀死，与C/C++中的默认效果是一样的"""
"""爬虫是IO密集型任务  就是说 时间大都消耗在 IO上..在爬虫里也就是网络通信
守护进程类似于额.. 常驻系统的进程
做一些监测等任务
"""

"""是否采用多任务的第二个考虑是任务的类型。我们可以把任务分为计算密集型和IO密集型。

计算密集型任务的特点是要进行大量的计算，消耗CPU资源，比如计算圆周率、对视频进行高清解码等等，全靠CPU的运算能力。这种计算密集型任务虽然也可以用多任务完成，但是任务越多，花在任务切换的时间就越多，CPU执行任务的效率就越低，所以，要最高效地利用CPU，计算密集型任务同时进行的数量应当等于CPU的核心数。

计算密集型任务由于主要消耗CPU资源，因此，代码运行效率至关重要。Python这样的脚本语言运行效率很低，完全不适合计算密集型任务。对于计算密集型任务，最好用C语言编写。

第二种任务的类型是IO密集型，涉及到网络、磁盘IO的任务都是IO密集型任务，这类任务的特点是CPU消耗很少，任务的大部分时间都在等待IO操作完成（因为IO的速度远远低于CPU和内存的速度）。对于IO密集型任务，任务越多，CPU效率越高，但也有一个限度。常见的大部分任务都是IO密集型任务，比如Web应用。

IO密集型任务执行期间，99%的时间都花在IO上，花在CPU上的时间很少，因此，用运行速度极快的C语言替换用Python这样运行速度极低的脚本语言，完全无法提升运行效率。对于IO密集型任务，最合适的语言就是开发效率最高（代码量最少）的语言，脚本语言是首选，C语言最差。"""


class Worker(threading.Thread):  # 处理工作请求
    def __init__(self, work_queue, result_queue, **kwargs):
        # threading.Thread.__init__(self, **kwargs)
        super(Worker, self).__init__()
        self.setDaemon(True)
        self.work_queue = work_queue
        self.result_queue = result_queue
        self.kwargs = kwargs

    def run(self):
        while True:
            try:
                call, args, kwargs = self.work_queue.get(False)  # get task

                """非阻塞，Otherwise (block is false), return an item if one is immediately available,
                else raise the Empty exception (timeout is ignored in that case)"""

                res = call(*args, **kwargs)
                self.result_queue.put(res)  # put result
            except Queue.Empty:
                break


class WorkManager:
    def __init__(self, num_of_workers=10):
        self.work_queue = Queue.Queue()  # 请求队列
        self.result_queue = Queue.Queue()  # 输出结果队列
        self.workers = []
        self._recruit_threads(num_of_workers)

    def _recruit_threads(self, num_of_workers):
        for i in range(num_of_workers):
            worker = Worker(self.work_queue, self.result_queue)  # 创建工作线程
            self.workers.append(worker)  # 加入到线程队列

    def start(self):
        for w in self.workers:
            w.start()

    def wait_for_complete(self):
        while len(self.workers):
            worker = self.workers.pop()
            worker.join()

            """As join() always returns None, you must call isAlive() after join() to decide whether a timeout happened
            这里的join是为了阻塞调用线程，只有当worker线程结束后才允许主线程结束。
            调用join不会使is_alive为true吧，只有当线程结束执行或者超时了is_alive才是True"""

            if worker.isAlive() and not self.work_queue.empty():
                self.workers.append(worker)
        print('All jobs were complete.')

    def add_job(self, call, *args, **kwargs):
        self.work_queue.put((call, args, kwargs))  # 向工作队列中加入请求

    def get_result(self, *args, **kwargs):
        return self.result_queue.get(*args, **kwargs)


def download_file(url):
    return requests.get(url).text


def main():
    try:
        num_of_threads = int(sys.argv[1])
    except:
        num_of_threads = 10
    _st = time.time()
    wm = WorkManager(num_of_threads)
    print(num_of_threads)
    urls = ['http://www.baidu.com'] * 1000
    for i in urls:
        wm.add_job(download_file, i)
    wm.start()
    wm.wait_for_complete()
    print(time.time() - _st)


if __name__ == '__main__':
    main()

