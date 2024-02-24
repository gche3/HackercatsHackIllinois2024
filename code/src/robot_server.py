
from enum import Enum
import functools
import inspect
import itertools
import json
# Remember to set start method to forkserver for thread safety
# TODO: fix semaphore leak (doesn't seem to impact shared memory usage after termination.)
import signal
from threading import Thread
import time
import traceback

import numpy as np

from phone_sensors import PhoneSensors

def print_log_info(obj):
    print(obj)

def print_log_warn(obj):
    print(obj)

def print_log_error(obj):
    print(obj)

class MotionStatus(Enum):
    STOPPED=0
    BOOTING=1   # In process of startup
    RUNNING=2
    PAUSED=3    # Robot is ativated but motion commands are paused
    SHUTDOWN=4  # In process of shutdown

# XMLRPC registering
_registered_methods = []

"""Object exposing the API of the Motion server.
Mapping from function name to a pair (has_retval: bool, <function signature object>)"""
SERVER_API = {}

def xmlrpc_export(*args, **kwargs):
    """Mark a function as to be exported through XMLRPC.

    Marked functions will be exported when `Motion.setup_xmlrpc_server()` is called.

    Usage:
    ```
    @xmlrpc_export(...kwargs)
    def my_xmlrpc_method(self, arg1, arg2...):
        ... code here
    ```

    OR:

    ```
    @xmlrpc_export
    def my_xmlrpc_method2(self, arg1, arg2...):
        ... code here
    ```

    Parameters:
    ------------
    name: Name to register method under. Default: method.__name__ (the name you see in python)
    has_retval: Whether or not this method's return value should be returned to the caller.
                Calls to methods with return values are blocking by default on motion client side.
    """

    # Invocation with keyword arguments only. Defer invocation and bind keyword args.
    if len(args) == 0:
        return lambda func: xmlrpc_export(func, **kwargs)

    # Wrap the target function to print the full stack trace (xmlrpcserver does not do this by default).
    def log_error_wrapper(f):
        @functools.wraps(f)
        def log_error(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise e
        return log_error

    # Argument-less invocation (tag syntax)
    f = args[0]
    name = kwargs.get('name', f.__name__)
    has_retval = kwargs.get('has_retval', False)

    # Register the function (and its signature) in the method list and api.
    _registered_methods.append((name, log_error_wrapper(f)))
    params = list(inspect.signature(f).parameters.items())[1:]
    SERVER_API[name] = (has_retval, params)
    return f

class Motion:
    """Class representing the motion module.

    Keeps an internal representation of the robot's state using a Klampt RobotModel.

    Updates this state (and can send commands to a physical robot) by using a set of Controllers, defined
    for subparts of the robot.

    Can be run in physical mode ("real" robot drivers) or kinematic simulation.
    Kinematic simulation may not reflect real robot behavior (ex. does not implement dynamics notably).
    """



    def setup_xmlrpc_server(self, ip, port) -> "SimpleXMLRPCServer":
        """Starts an xmlrpc server for Motion.
        Spins up the rpc server and registers functions.

        Returns the server. (Doesn't actually start listening)
        """
        from xmlrpc.server import SimpleXMLRPCServer
        from xmlrpc.client import Marshaller
        Marshaller.dispatch[np.float64] = Marshaller.dump_double
        Marshaller.dispatch[np.ndarray] = Marshaller.dump_array

        server = SimpleXMLRPCServer((ip, port), logRequests=False, allow_none=True)
        server.register_introspection_functions()
        for name, func in _registered_methods:
            print_log_info(f"Server: Registering function [{name}]")
            def wrapper(*args, __f=func, **kwargs):
                return __f(self, *args, **kwargs)
            server.register_function(wrapper, name)

        return server

    def __init__(self):
        """
        """
        self.loop_thread = None
        self.server_time = -1
        self.phone_sensors = PhoneSensors("10.194.232.216:8080")

    @xmlrpc_export(has_retval=True)
    def ping(self):
        return "Poing!"

    @xmlrpc_export(name='status', has_retval=True)
    def get_status(self) -> str:
        return self.status.value

    @xmlrpc_export(has_retval=True)
    def startup(self):
        """Start all motion components.
        Doesn't start the xmlrpc server.
        Starts the motion loop in a separate thread.
        """
        def loop_func():
            while True:
                self._loop()
                self.server_time = time.monotonic()
                time.sleep(0.05)

        self.loop_thread = Thread(group=None, target=loop_func, name="motion:loop")
        self.loop_thread.start()

    def _loop(self):
        """Main loop of motion. Should poll sensors and push commands to component drivers."""
        self.phone_sensors.loop()


    @xmlrpc_export
    def shutdown(self):
        """Shut down the motion xml rpc server. Shuts down each component and updates status of the robot."""
        pass

    @xmlrpc_export
    def get_time(self):
        return self.server_time


if __name__ == "__main__":
    import faulthandler
    faulthandler.enable()

    import argparse
    parser = argparse.ArgumentParser(description='Runs the motion server')
    parser.add_argument('-a','--ip', default='localhost', type=str, help='Server\'s IP address')
    parser.add_argument('-p','--port', default=8081, type=int, help='Server\'s port number')
    args = parser.parse_args()

    print_log_info("Starting motion server...")
    motion_inst = Motion()

    print("MOTIONSERVER", args.ip, args.port)
    server = motion_inst.setup_xmlrpc_server(args.ip, args.port)

    import signal
    def sigint_handler(signum, frame):
        motion_inst.shutdown()
        print("Server exiting")
        raise KeyboardInterrupt()
    signal.signal(signal.SIGINT, sigint_handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server exited")

