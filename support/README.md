# Pipeline support directory

This directory contains files and scripts to support the build and test of pyvcloud from a Jenkins pipeline or in Docker containers on a developer machine.

The following scripts in the repository have been updated to work as part of the pipeline or in a Docker container. Other scripts may depend on additional requirements or configuration.

* `support/install.sh`
* `support/tox.sh`
* `examples/run_examples.sh`
* `system_tests/run_system_tests.sh`

# Jenkins configuration

1. Make sure you have a Jenkins executor with the label `docker`. The executor should be configured with the Docker Engine running and so that the executor user can launch containers in Docker.
1. Create a Jenkins credential with a file holding the contents of a file like `examples/vcd_connection.sample`. The ID of the credential should be set to `pyvcloud_vcd_connection`.
1. Install the `Pipeline: Multibranch` plugin along with all dependencies.
1. Add a `Multibranch Pipeline` job to Jenkins that pulls from your Git repository and reads the Jenkinsfile from `support/Jenkinsfile`.

The Jenkins job will scan the repository and create jobs for all branches containing the `support/Jenkinsfile` file. You can configure the job to run periodically or start it manually.

# Running the scripts locally

When run locally, the scripts will use several factors to determine if a Docker container will be started.

* Is `python3` in `$PATH`?
* Is `pip3` in `$PATH`?
* Is `$PYTHON3_IN_DOCKER` set to `0`, `1` or blank?

If `$PYTHON3_IN_DOCKER` is set to `0`, a Docker container will never be used. If it set to `1`, then a Docker container will always be used.

Otherwise, the scripts will search for `python3` and `pip3` in the user environment. If those commands are available, the scripts will be run locally. A Docker container will be used if those commands are not available in the user environment.
