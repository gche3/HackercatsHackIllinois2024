import inspect
from xmlrpc.client import ServerProxy, Marshaller
import time
import sys
import os
import numpy as np
import robot_server

# These two lines are needed to automatically convert ("marshal") numpy arrays and numpy floats
# into the appropriate formats for sending over XMLRPC.
Marshaller.dispatch[np.ndarray] = Marshaller.dump_array
Marshaller.dispatch[np.bool_] = Marshaller.dump_bool
Marshaller.dispatch[np.float64] = Marshaller.dump_double

class MotionClient:
    """XMLRPC Client for the motion module.

    A thin wrapper around `xmlrpc.client.ServerProxy`, that allows named arguments
    and default arguments to be mixed with positional arguments.

    DOES NOT allow general *args or **kwargs.   #TODO

    DEV NOTE: possibly refactor this into a subclass of ServerProxy.

    Usage:

    ```
    robot = MotionClient(server_address)
    robot.start()   # function calls forwarded to xmlrpc server
    robot.set_joint_config('left_limb', [0, 0, 0, 0, 0, 0], {})
    ...
    robot.shutdown()
    ```

    NOTE:
    For more information about what functions are available, see Motion/motion.py
    """

    def __init__(self, address: str = 'localhost', port: str = '8081'):
        """Create a MotionClient.
        Creates a connection to the specified xmlrpc server.

        Parameters:
        ----------
        address:    Address of the xmlrpc server to connect to, or 'auto' to read it from settings.
        """
        redis_sub = None
        print("MOTIONCLIENT", address, port)
        self.s = ServerProxy(f'http://{address}:{port}', allow_none=True)
        self.shut_down = False

    def __getattr__(self, fname: str):
        """Python hackery to emulate named arguments and default arguments through the XMLRPC interface.
        
        Used as follows:
        ```
        robot = MotionClient(server_address)
        robot.start()   # equivalent to `robot.__getattr__('start')()`
        ```

        Parameters:
        ----------
        fname:  name of the attribute (assumed to be a function) that is being requested.

        Return:
        ----------
        function corresponding to the attribute name. Actually returns a wrapper around the function,
            to allow passing of named arguments and default arguments.
        """
        func_parameters = robot_server.SERVER_API[fname][1]
        func = lambda *args: self.s.__getattr__(fname)(*args)
        def wrap_func(*args, **kwargs):
            arglist = []
            arg_idx = 0
            for k, v in func_parameters:
                if arg_idx < len(args):
                    arglist.append(args[arg_idx])
                    arg_idx += 1
                    continue
                elif k in kwargs:
                    arglist.append(kwargs[k])
                    del kwargs[k]
                elif v.default != inspect._empty:
                    arglist.append(v.default)
                else:
                    raise TypeError("Not enough arguments to function " + fname)
            if len(args) > arg_idx:
                raise TypeError("Too many arguments to function " + fname)
            if len(kwargs) > 0:
                print("[WARN] MotionClient: unused keyword arguments for function " + fname)
            return func(*arglist)
        return wrap_func

if __name__ == "__main__":
    robot = MotionClient()
    robot.startup()
    while True:
        print(robot.ping())
        print(robot.get_time())
        time.sleep(2)
        continue
    robot.shutdown()
