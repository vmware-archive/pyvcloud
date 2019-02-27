from pyvcloud.system_test_framework.environment import Environment


def depends(*args):
    """Decorator run a function with dependency.

    The decorator either execute or skip the function on the basis of
        dependent function.
    It will skip the function if any of dependent function return False.

    :param list args: list of dependent functions.
    :return: a wrapper function that execute or skip the function.
    :rtype: function
    """

    def wrap(function):
        def wrapped_f(self):
            is_execute_func = True
            for func in args:
                if not func(self):
                    is_execute_func = False
                    break
            if is_execute_func:
                function(self)
            else:
                Environment.get_default_logger().debug(
                    'Skipping ' + function.__name__ +
                    ' due to depandancy failure.')

        return wrapped_f

    return wrap
