"""examples for bugs that can be difficult to debug using `print` statements"""
#%%imports
import asyncio
import logging
import random
import time
import threading
import traceback

#%%constants
logging.basicConfig()
logger = logging.getLogger(__name__)

#%%definitions

import inspect
def state(
    fstring:str="%-30s, %15i, %s",
    show_globals:bool=True,
    show_locals:bool=True,
    filter_dunder:bool=True
    ) -> None:
    """displays the current state

    - ONLY TO BE USED FROM WITHIN Pdb (PythonDebugger)!
    - displays
        - locals of current frame
        - globals of current frame
        - additional information for each

    Parameters
        - `fstring`
            - `str`, optional
            - some `%` format-string with 3 fields
                - `variable name`
                - `variable id`
                - `variable repr`
            - to format the output
            - the default is `"%-30s, %15i, %s"`
        - `show_globals`
            - `bool`, optional
            - whether to show global variables
            - the default is `True`
        - `show_locals`
            - `bool`, optional
            - whether to show local variables
            - the default is `True`
        - `filter_dunder`
            - `bool`, optional
            - whether to remove python dunder (`__<name>__`) variables
            - the default is `True`

    Raises

    Returns

    Dependencies
        - `inspect`

    """

    #get previous frame (`state()` creates a new frame)
    frame = inspect.currentframe().f_back

    if show_globals:
        print("GLOBALS:")
        print("--------")
        for k, v in frame.f_globals.items():
            if k.startswith("__") and k.endswith("__") and filter_dunder:
                continue
            print(fstring%(k, id(v), repr(v)))

    print("\n")
    if show_locals:
        print("LOCALS:")
        print("-------")
        for k, v in frame.f_locals.items():
            if k.startswith("__") and k.endswith("__") and filter_dunder:
                continue
            print(fstring%(k, id(v), repr(v)))
    return

def race_condition(rand_th:float=1e-3):
    """demonstrates race condition"""
    counter = 0 #private state variable
    n = 10_000

    def increment():
        nonlocal counter    #allows modifications to outer variables
        for _ in range(10_000):
            temp = counter

            #random delay
            if random.random() < rand_th:
                time.sleep(1e-3)
            counter = temp + 1

    t1 = threading.Thread(target=increment)
    t2 = threading.Thread(target=increment)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print(f"{counter=}, expected={n*2}")   #might not be 200_000
    return

def async_scheduling(rand_th:float=1e-1):
    """demonstrated async scheduling bug

    - results in race condition
    """
    counter = 0

    async def increment(name):
        nonlocal counter

        for _ in range(3):
            # print(name, "reading", counter) #can change the scheduling
            current = counter

            #random delay
            if random.random() < rand_th:
                #task switch can happen here
                await asyncio.sleep(1e-5)

            counter = current + 1
            print(name, "set counter to", counter)

    async def main():
        await asyncio.gather(
            increment("A"),
            increment("B")
        )

        print("final counter:", counter)    #expected: 6

    asyncio.run(main())
    return

def state_change():
    """demonstrates state change between print statements"""

    data = {"count": 0}

    def worker():
        time.sleep(1)
        data["count"] = 42
        print("[worker] Updated count to 42")

    thread = threading.Thread(target=worker)
    thread.start()

    print("[main] Before:", data)

    #simulate doing other work  (thread is still running)
    time.sleep(2)

    print("[main] After:", data)

    thread.join()

    return

def deadlock():
    """creates a deadlock"""

    #shared resources locks
    lock_a = threading.Lock()
    lock_b = threading.Lock()

    def thread_one_worker():
        with lock_a:        #thread 1 locks A
            time.sleep(1)   #force switch
            with lock_b:    #thread 1 waits for B
                pass

    def thread_two_worker():
        with lock_b:        #thread 2 locks B
            time.sleep(1)   #force switch
            with lock_a:    #thread 2 waits for A
                pass

    #start threads and observe them freeze
    t1 = threading.Thread(target=thread_one_worker)
    t2 = threading.Thread(target=thread_two_worker)
    t1.start(); t2.start()
    t1.join(); t2.join()

    return

def mutable_object_aliasing():
    """demonstrates bug due to object aliasing"""
    a = []
    b = a
    b.append(1)
    print(f"{a=} ({id(a)}), {b=} ({id(b)})")
    return

def swallowed_exception():
    """demonstrates a bug due to ignored exception"""


    a = range(0,5)[::-1]
    b = 0
    for ai in a:
        try:
            b = 1/ai
        except Exception:
            pass

        c = ai * b  #expected: 1
        print(f"{c=} (expected: 1.0)")

    return

def inf_loops(idx:int=0):
    """demonstrates infinite loop bugs"""

    if idx == 0:
        #float precision
        x = 0.0
        while x != 1.0:
            x += 0.1
    elif idx == 1:
        #list mutation while iterating
        numbers = [1, 2, 3]

        i = 0
        while i < len(numbers):
            print(i)
            if numbers[i] % 2 == 1:
                numbers.append(numbers[i] + 2)
            i += 1
    return

#%%main
def main():
    # race_condition(rand_th=1e-3)
    # race_condition(rand_th=0)

    # async_scheduling(rand_th=2e-1)
    # async_scheduling(rand_th=0)

    # state_change()

    # deadlock()

    # mutable_object_aliasing()

    breakpoint()
    swallowed_exception()

    # inf_loops(0)
    # inf_loops(1)
    pass

if __name__ == "__main__":
    main()
