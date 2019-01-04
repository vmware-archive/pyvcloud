// This file contains methods used by Jenkinsfile to support the
// Jenkins pipeline. The contents are loaded after the target
// git repository is checked out.

// Declare global variables so they can be used in all pipeline methods. 
credentialsArray = []
environmentArray = []
temporaryFiles = []

// Process job parameters and determine which credentials or environment
// variables are required for proper processing.
def init() {
    // Determine if a credentials ID has been provided, or if the default should be used.
    def vcdConnectionCredentialsID = params.VCD_CONNECTION_CREDENTIALS_ID
    if (vcdConnectionCredentialsID.toLowerCase() == 'default') {
        vcdConnectionCredentialsID = env.DEFAULT_VCD_CONNECTION_CREDENTIALS_ID
    }

    // Check for a parameter containing the VCD_CONNECTION content
    // Write that to a file if available, or use a Jenkins credential file
    if (env.VCD_CONNECTION_CONTENTS != null && env.VCD_CONNECTION_CONTENTS != "") {
        def tmpdir = pwd(tmp:true)
        def vcdPath = "${tmpdir}/jenkins_vcd_connection"

        println "Write VCD_CONNECTION_CONTENTS to ${vcdPath}"
        writeFile(file: vcdPath, text: env.VCD_CONNECTION_CONTENTS)
        environmentArray << "VCD_CONNECTION=${vcdPath}"
        temporaryFiles << vcdPath
    } else if (vcdConnectionCredentialsID.toLowerCase() != "") {
        // Ensure the path to a VCD parameters file is loaded into the appropriate
        // environment variable for testing scripts to use.
        credentialsArray << [
            $class: 'SSHUserPrivateKeyBinding',
            credentialsId: vcdConnectionCredentialsID,
            variable: 'VCD_CONNECTION'
        ]
    }
}

def install() {
    // Set up Python virtual environment and install pyvcloud. 
    withEnv(environmentArray) {
        sh "support/run_in_docker.sh support/install.sh"
    }
}

def runToxFlake8() {
    // Run tox. 
    withEnv(environmentArray) {
        sh "support/run_in_docker.sh support/tox.sh"
    }
}

def runSamples() {
    //withCredentials(credentialsArray) {
    // Execute samples.
    withEnv(environmentArray) {
        sh "support/run_in_docker.sh examples/run_examples.sh"
    }
    //}
}

def runSystemTests() {
    //withCredentials(credentialsArray) {
        // Run the default system test list.
    withEnv(environmentArray) {
        sh "support/run_in_docker.sh system_tests/run_system_tests.sh"
    }
    //}
}

def cleanupSystemTests() {
    //withCredentials(credentialsArray) {
    // Cleanup all system tests.
    withEnv(environmentArray) {
        sh "support/run_in_docker.sh system_tests/run_system_tests.sh cleanup_test.py"
    }
    //}
}

def cleanupWorkspace() {
    // Remove temporary files
    temporaryFiles.each {
        println "Remove ${it}"
        sh "if [ -f ${it} ]; then rm ${it}; fi"
    }
}

// Call the init method to ensure the environment and credentials are ready. 
init()

// Return a reference to this file to allow the pipeline to call methods. 
return this