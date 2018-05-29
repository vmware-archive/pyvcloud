# pyvcloud System Tests

## Running Tests

This directory contains system tests that exercise pyvcloud API functions. 
You can run tests individually as follows.

1. Fill in required values in `base_config.yaml`.  
2. Execute the test as a Python unit test, e.g.: 
```
python3 -m unittest idisk_tests.py
```

To run system tests in a build, follow the steps below.

1. Copy `../examples/vcd_connection.sample` to `vcd_connection` and fill in 
connection data.
2. Export `VCD_CONNECTION`, e.g., `export VDC_CONNECTION=$PWD/vcd_connection`
3. Execute the script as follows: `./run_system_tests.sh`

This will run a default list of tests.  You can specify different tests 
by listing the file names on the command line, e.g.,
`./run_system_tests.sh my_test.py`.

## Writing New Tests

System tests are based on the [Python unittest framework](https://docs.python.org/3/library/unittest.html) 
but depend on a customized test superclass named BaseTestCase because we
need a working vCD installation to do anything useful.  BaseTestCase calls
the Environment class to set up basic fixtures such as a test org, users, or
VDC automatically before the test runs.  It creates fixtures if
they are missing; otherwise it reuses what is already there.  Both of
these classes may be found in the `pyvcloud.system_test_framework` module.

Parameters for the test are supplied by file `base_config.yml`, which
is located in the `system_tests` directory. You can copy this file to
another location to set custom values and tell BaseTestCase where it is 
located using the `VCD_TEST_BASE_CONFIG_FILE` environmental variable. 

Here's a short description of steps to develop a new test. 

Step 1: Start by copying an existing test to a new name such as `my_test.py`.

Step 2: Trim out extraneous code and add your own test cases.
We typically write tests to be order-dependent as it allows us to share
complex state across test cases.  Minimum method naming and documentation
conventions are as follows:

* Name test case methods with a number to ensure run order plus a meaningful suffix such as `test_0030_get_disk_by_id`. 
* Add a docstring that summarizes what the case verifies.
* Private helper methods should be preceded with underscore, e.g., `_setup_stuff`.

Step 3: Add setup and teardown as test cases at the start and end of the
test to set up and remove specialized fixtures required for your test.
(You can skip this if no extra setup is required beyond what BaseTestCase
gives you for free.)  The conventional names are as follows:

* `test_0000_setup` -- Create custom state required for test
* `def test_9999_teardown` -- Remove custom state

To make tests easier to debug you can add the @developerModeAware tag
to the teardown method so that it does not run when developer mode is
set in the `base_config.yaml` file, thereby leaving state in place for
you to look at later.  Here's an example:

```
@developerModeAware
def test_9999_teardown(self):
"""Remove stuff, etc."""
```

Note: You can also use the standard Python unittest `setUp()` and
`tearDown()` methods.  Bear in mind that these run for each test method,
so if they construct or remove state your test may run very slowly.

Step 4: Use calls to Environment class methods to get references required
for testing.  For example, the following code fetches an Org admin client
object:

```
org_admin_client = Environment.get_client_in_default_org(
    CommonRoles.ORGANIZATION_ADMINISTRATOR)
```

The Environment methods are easy to understand.  Have a look through
the class to find what you need and add extra methods if you discover
something useful is missing. 

You can also access `base_config.yml` parameter values directly, as 
shown in the following example: 

```
vcd_host = Environment._config['vcd']['host']
sysadmin = Environment._config['vcd']['sys_admin_username']
```

Step 5: Fill out values in the `base_config.yaml` file to tell your
test where vCD is located and set other details necessary for operation.
Basic tests just need vCD host and admin credentials to run; more complex
tests will require more.

Step 6: Run your test!  You can use the `run_system_tests.sh` script
described above or invoke your test directly as shown below.

```
# Set location of config if it's something other than base_config.yaml.
export VCD_TEST_BASE_CONFIG_FILE=my_base_config.yaml
python3 -m unittest my_test.py
```

Step 7: Before checking in, run flake8 and correct any errors you find.  
