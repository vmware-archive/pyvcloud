# Pipeline support directory

This directory contains files and scripts to support the build and test of 
pyvcloud from a Jenkins pipeline or in Docker containers on a developer 
machine.

The following scripts in the repository have been updated to work as part of 
the pipeline or in a Docker container. Other scripts may depend on additional 
requirements or configuration.

* `support/install.sh`
* `support/tox.sh`
* `examples/run_examples.sh`
* `system_tests/run_system_tests.sh`

# Jenkins configuration

1. Make sure you have a Jenkins executor with the label `docker`. The 
   executor should be configured with the Docker Engine running and so 
   that the executor user can launch containers in Docker.
2. Create a Jenkins credential with a file holding the contents of a file 
   like `examples/vcd_connection.sample`. The ID of the credential should 
   be set to `pyvcloud_vcd_connection`.
3. Install the `Pipeline: Multibranch` plugin along with all dependencies.
4. Add a `Multibranch Pipeline` job to Jenkins that pulls from your Git 
   repository and reads the Jenkinsfile from `support/Jenkinsfile`.

The Jenkins job will scan the repository and create jobs for all branches 
containing the `support/Jenkinsfile` file. You can configure the job to run 
periodically or start it manually.

# Running the scripts locally

```
pip3 install virtualenv
export VIRTUAL_ENV_DIR=auto.env
./support/install.sh
./support/tox.sh

export VCD_CONNECTION=/path/to/vcd_connection
./examples/run_examples.sh
./system_tests/run_system_tests.sh
```

# Running the scripts with an existing virtualenv

```
. .venv/bin/activate

./support/tox.sh

export VCD_CONNECTION=/path/to/vcd_connection
./examples/run_examples.sh
./system_tests/run_system_tests.sh
```

# Running the scripts in Docker

```
export VIRTUAL_ENV_DIR=auto.env
./support/run_in_docker.sh support/install.sh
./support/run_in_docker.sh support/tox.sh

export VCD_CONNECTION=/path/to/vcd_connection
./support/run_in_docker.sh examples/run_examples.sh
./support/run_in_docker.sh system_tests/run_system_tests.sh
```
