## pyvcloud System Tests

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
2. Execute the script as follows: `run_system_tests..sh vcd_connection`
