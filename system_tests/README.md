# pyvcloud System Tests

## Running Tests

This directory contains system tests that exercise pyvcloud API functions. 
You can run tests individually as follows.

1. Fill in required values in base_config.yaml.  
2. Execute the test as a Python unit test, e.g.: 
```
python3 -m unittest idisk_tests.py
```

To run system tests in a build, follow the steps below.

1. Copy ../examples/vcd_connection.sample to vcd_connection and fill in 
connection data.
2. Export VCD_CONNECTION, e.g., `export VDC_CONNECTION=$PWD/VCD_CONNECTION`
3. Execute the script as follows: `./run_system_tests.sh`

This will run a default list of tests.  You can specify different tests 
by listing the file names on the command line, e.g.,
`./run_system_tests.sh my_test.py`.

## Writing New Tests

System tests are based on Python unittest but depend on a customized test
superclass named BaseTestCase because we need a working vCD installation
to do anything useful.  BaseTestCase calls the Environment class to set up
basic fixtures automatically before the test runs.  It creates fixtures
if they are missing; otherwise it reuses what is already there. 

You can also call Environment yourself to get usable references to users,
test orgs, vapps and the like for your test code.

Here's a short description of how to develop a new test. 

Step 1: Start by copying an existing test to a new name such as my_test.py.

Step 2: Trim out extraneous code and add your own test cases.  Name the
cases to ensure they run in order.  We typically write tests to be
order-dependent as it allows us to share complex state across test cases.
Put in a docstring to describe what each test case is doing.

Step 3: Add setup and teardown as test cases at the start and end of the
test to set up and remove specialized fixtures required for your test.
You can skip this if no extra setup is required beyond what BaseTestCase
gives you for free.

Warning: If you unittest setup and teardown methods be aware that
these run on every case.  If they do anything complex your test will be
very slow.

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

Step 5: Fill out values in the base_config.yaml file to tell your
test where vCD is located and set other details necessary for operation.
Basic tests just need vCD host and admin credentials to run; more complex
tests will require more.

Step 6: Run your test!  You can use the run_system_tests.sh script
described above or invoke your test manually as shown below.

```
# Set location of config if it's something other than base_config.yaml.
export VCD_TEST_BASE_CONFIG_FILE=my_base_config.yaml
python3 -m unittest my_test.py
```

Before checking in, please run flake8 and correct any errors you find.  
