// Jenkins multi-branch pipeline build script. 
// This script depends on file $HOME/vcd_connection with valid vCD 
// connection parameters. 

// Pipeline definition.
pipeline {
    agent { 
        node { 
            // Label on Jenkins node that runs this test. 
            label 'docker-runner' 
            // Required to get around problems with long file names when 
            // Jenkins generates the workspace name automatically. 
            customWorkspace "/var/jenkins/workspace/${JOB_NAME}"
        }
    }
    stages {
        stage('checkout') {
            steps {
                // Remove and checkout current branch from git using built-in
                // Jenkins commands exposed in groovy. 
                deleteDir()
                checkout scm
                // Print configuration for later debugging. 
                sh "git config --list"
                sh "git branch"
            }
        }
        stage('install') {
            steps {
                // Set up Python virtual environment and install pyvcloud. 
                sh """
                    python3 --version
                    rm -rf test-env
                    python3 -m venv test-env
                    . test-env/bin/activate
                    pip3 install -r requirements.txt
                    python setup.py install
                """
            }
        }
        stage('run-tox-flake8') {
            steps {
		// Run tox. 
                sh """
                    . test-env/bin/activate
                    pip3 install -r test-requirements.txt
                    tox -e flake8
                """
            }
        }
        stage('run-samples') {
            steps {
                // Execute samples. 
                sh """
                    set +x
                    . test-env/bin/activate
                    cd examples
                    ./run_examples.sh 
                """
            }
        }
        stage('run-system-test') {
            steps {
                // Run the default system test list. 
                sh """
                    set +x
                    . test-env/bin/activate
                    cd system_tests
                    ./run_system_tests.sh 
                """
            }
        }
    }
    post { 
        failure { 
            echo "Job failed! System test environment will not be cleared."
        }
        success { 
            echo "Job succeeded! Cleaning up system test environment"
            sh """
                set +x
                . test-env/bin/activate
                cd system_tests
                ./run_system_tests.sh cleanup_test.py
            """
        }
    }
}
