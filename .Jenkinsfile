// Jenkins multi-branch pipeline build script. 
// This script depends on file $HOME/vcd_connection with valid vCD 
// connection parameters. 

// Helper function to send email. 
def sendEmail() {
    if (currentBuild.result == currentBuild.previousBuild.result) {
        return
    }

    emailext(
        subject: currentBuild.result + ': ' + env.${BRANCH_NAME} + ' - BuildNr: ' + env.${BUILD_NUMBER},
        body: 'Build location URL' + env.BUILD_URL,
        recipientProviders: [[env.${EMAIL}]]
    )
}

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
                // Remove and checkout current branch from git.
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
                sh """
                    set +x
                    . test-env/bin/activate
                    cd system_tests
                    ./run_system_tests.sh 
                """
            }
        }
        stage('cleanup') {
            steps {
                echo "We don't do any clean-up for now."
            }
        }
    }
    post { 
        failure { 
            echo "Job failed; will post email"
        }
        success { 
            echo "Job succeeded; will post email on recovery from failure"
            echo "This is where we can restore the vCD installation snapshot!"
        }
    }
}
