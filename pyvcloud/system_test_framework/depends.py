from pyvcloud.system_test_framework.environment import Environment


def depends(*args):
    """Decorator function to run unit test with depandancy.

    :param list args: list of dependent function that return True
        If depandancy failed Else return False.

    :return: a function that either executes the decorated function or skips
        it, based on the value of a is_skip param.

    :rtype: function
    """

    def wrap(function):
        def wrapped_f(self):
            is_execute_func = True
            for func in args:
                if func(self):
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
