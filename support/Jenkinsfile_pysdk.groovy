// Jenkins multi-branch pipeline build script.
//
// Requirements:
// * At least one executor node labeled 'docker' with
//   support for building and running Docker containers.
// * A Jenkins file-type credential named 'pyvcloud_vcd_connection'
//   with the contents of a vcd_connection file.

// Global variable to hold methods from the 'lib.groovy' file.
externalMethods = null
def testbedJson = null;
// Pipeline definition.
pipeline {
    agent {
        label {
            label "$SITE_ID"
            customWorkspace "/data/jenkins/jenkins-${JOB_NAME}-${env.BUILD_NUMBER}"
            //customWorkspace "/tmp/jenkins-workspace/${JOB_NAME}-${env.BUILD_NUMBER}"
        }
    }
    options {
        timestamps()
        ansiColor('xterm')
        timeout(time: 8, unit: 'HOURS')
    }
    environment {
        VCD_USERNAME="spinfra"

        WORKSPACE_OUTPUT="$WORKSPACE/output"
        WORKSPACE_STF="$WORKSPACE_OUTPUT/stf"
        WORKSPACE_STF_PROPERTIES="$WORKSPACE_STF/stf.properties"
        WORKSPACE_STF_DEPLOYER_JSON="$WORKSPACE_OUTPUT/dot-stf.deployer.json"

        WORKSPACE_TESTBED_JSON="$WORKSPACE_OUTPUT/testbed.json"
        WORKSPACE_POSTBUILD_PROPERTIES="$WORKSPACE_OUTPUT/postbuild.properties"

        WORKSPACE_PYTHON="$WORKSPACE/python"
        WORKSPACE_DEPLOYER="$WORKSPACE_OUTPUT/deployer"
        WORKSPACE_DEPLOYER_PROPERTIES="$WORKSPACE_DEPLOYER/deployer.properties"
        WORKSPACE_DEPLOYER_CONFIGURATOR_PROPERTIES="$WORKSPACE_DEPLOYER/configurator.properties"
        WORKSPACE_DEPLOYER_CONFIGURATOR="$WORKSPACE_DEPLOYER/test-output-deployer-configurator"

        VCDA_CLI_WORK_AREA="$WORKSPACE/.vcda/cache"
        VCDA_CLI_TEST_VCD_TESTBED_ORG="$VCD_ORGANIZATION"
        VCDA_CLI_TEST_VCD_TESTBED_USERNAME="$VCD_USERNAME"
        VCDA_CLI_TEST_VCD_TESTBED_VCD_URL="$VCD_API_ENDPOINT"
        PYTHONWARNINGS="ignore"
        IS_DEPLOYER_BUILD_DOWNLOADED=false

        /*Build Web constants*/
        BUILD_API_BASE_URL='http://buildapi.eng.vmware.com'
        BUILD_WEB_BASE_URL='https://buildweb.eng.vmware.com'
        P4WEB_BASE_URL='https://p4web.eng.vmware.com:11700'
        P4WEB_SUFFIX_URL1='@md=d&cd=//&c=UXC@'
        P4WEB_SUFFIX_URL2='?ac=10'

        /* Slack configuration */
        SLACK_TEAM_DOMAIN="vca-bos"
        SLACK_TOKEN="9NVN8YstlFuv50YNTEaDz5OU"

        /* Upstream  build info */
        IS_BUILD_TRIGGERED_BY_UPSTREAM=false

        DEFAULT_VCD_CONNECTION_CREDENTIALS_ID = 'pyvcloud_vcd_connection'
        VIRTUAL_ENV_DIR = 'jenkins-venv'
        VCD_CONNECTION = "$WORKSPACE/vcd_connection"
    }
    parameters {
        string(name: 'VCD_CONNECTION_CREDENTIALS_ID', defaultValue: 'Default',
            description: 'A Jenkins file-type credential ID with the contents of a vcd_connection file.'
        )
        string(name: 'OVERRIDE_GIT_REPOSITORY', defaultValue: 'git@github.com:vmware/pyvcloud.git',
            description: 'The full git repository URL to clone from instead of the default.'
        )
        string(name: 'OVERRIDE_GIT_TREEISH', defaultValue: 'master',
            description: 'The branch name or commit SHA to test from OVERRIDE_GIT_TREEISH.'
        )
        string(name: 'VCD_SETUP_JSON_URL', defaultValue: '',
            description: 'The provided json will be used for running PySdk Test. No new vCD setup will be deployed.'
        )
        string(name: 'VCD_API_VERSION', defaultValue: '',
            description: 'API version for provided VCD json'
        )
        string(name: 'VCD_BUILD', defaultValue: '',
            description: 'A VCD Build required. If empty then fetch latest build from sp-main.'
        )
    }
    stages {
        stage("setup-vcda") {
            steps {
                script {
                    try {
                        println "Checking out vCloud Director Automation library ..."
                        dir('vcda') {
                            retry(5) {
                              checkout([$class: 'GitSCM',
                                branches: [[name: '*/master']],
                                doGenerateSubmoduleConfigurations: false,
                                extensions: [], submoduleCfg: [],
                                userRemoteConfigs: [
                                    [
                                        credentialsId: '7b4fa94e-8e42-446c-b2e2-9e20b1e9528f',
                                        url: 'git@gitlab.eng.vmware.com:vcd/tools/vcd-automation.git'
                                    ]
                                ]
                               ])

                            }
                        }
                    } catch (err) {
                        throwError("Could not checkout vcd-automation code.")
                    }
                    try {
                        println "Installing vCloud Director Automation library and vcd-cli ..."
                        def vcdaRetryCount = 1;
                        retry(3) {
                            println "Install vcda retry count: $vcdaRetryCount"
                            vcdaRetryCount++;
                            sh '''
                              echo "WORKSPACE: $WORKSPACE"
                              virtualenv --python="python3.6"  "$WORKSPACE_PYTHON"
                              source "$WORKSPACE_PYTHON"/bin/activate  2>&1
                              cd vcda/python
                              pip install -I . 2>&1

                              deactivate
                            '''
                        }
                    } catch (err) {
                        throwError("Error occurred while installing vcd-automation")
                    }

                    println "Successfully installed vcda and vcd-cli."
                    env.VCDA_BIN_PATH="$WORKSPACE_PYTHON/bin"
                }
            }
        }
        stage("find-latest-vcd-build") {
            steps {
             withEnv(["PATH+VCDA=$VCDA_BIN_PATH"], {
                    script {

                        if(env.VCD_BUILD == '') {
                            env.VCD_BUILD = sh (script: "vcda build_latest latest -branch=sp-main -product=vcloud -buildtype=release -buildsystem=ob ", returnStdout: true).trim()
                        }
                        checkBuildStatus("VCD_BUILD", env.VCD_BUILD)

                    }
                 })
             }
        }
        stage("deploy-vcd") {
            steps {
                script {
                    println "Build::"+ env.VCD_BUILD
                    try {
                       def testbedJsonUrl = env.VCD_SETUP_JSON_URL
                       println "Before vcd setup start, checking for json URL" + testbedJsonUrl
                       if (testbedJsonUrl  == '') {
                           def result = triggerRemoteJob(
                                auth: TokenAuth(apiToken: '4a43d5a348427139732d61c71d030e81', userName: 'rajeshk'),
                                job: 'Preflight-4.0-STF', maxConn: 1,
                                parameters:
                                    """TESTBED_DESCRIPTOR_NAME=simple-testbed-postgres.json.template
                                    VCD_BUILD=${VCD_BUILD}
                                    OWNER=rajeshk
                                    VCD_VAPP_PREFIX=python-sdk
                                    VCD_API_VERSION=VCLOUD_API_32_0
                                    CASSINI_API_VERSION=VCLOUD_API_31_0
                                    VCD_ORGANIZATION=Development
                                    VCD_API_ENDPOINT=https://cassini.eng.vmware.com/api
                                    VCD_ORG_VDC=DevelopmentOrgVdc
                                    VCD_ORG_VDC_NETWORK=CassiniDirectOrgVdcNetwork
                                    DELETE_FAILED_DEPLOYMENT=true""",
                                remoteJenkinsUrl: 'https://sp-taas-vcd-butler.svc.eng.vmware.com/', useCrumbCache: true, useJobInfoCache: true)
                           def buildUrl = result.buildUrl
                           testbedJsonUrl = buildUrl.toString() + "artifact/output/testbed.json"
                        }

                        println "testbedJson url: " + testbedJsonUrl
                        try {
                            retry(3) {
                                testbedJson = httpRequest(url: testbedJsonUrl,
                                validResponseCodes: '200').content
                            }
                        } catch(err) {
                            println "Error: " + error
                            throw err
                        }
                        println "JSON Data::"+ testbedJson

                   } catch(err) {
                        throw err
                   }
                }
           }
        }
        stage('checkout-pysdk') {
            steps {
                script {
                    try {
                        println "Checking out PyVcloud sdk code ..."
                        if (OVERRIDE_GIT_TREEISH == '') {
                            OVERRIDE_GIT_TREEISH = 'master'
                        }
                        if (OVERRIDE_GIT_REPOSITORY == '') {
                            OVERRIDE_GIT_REPOSITORY = 'git@github.com:vmware/pyvcloud.git'
                        }
                        println "Git repository branchAfter::"+OVERRIDE_GIT_TREEISH
                        println "Git repository::"+OVERRIDE_GIT_REPOSITORY
                        retry(5) {
                          checkout([$class: 'GitSCM',
                            branches: [[name: OVERRIDE_GIT_TREEISH]],
                            doGenerateSubmoduleConfigurations: false,
                            extensions: [], submoduleCfg: [],
                            userRemoteConfigs: [
                                [
                                    credentialsId: 'pyvcloud_vcd_connection',
                                    url: OVERRIDE_GIT_REPOSITORY
                                ]
                            ]
                           ])

                        }
                        // Print configuration for later debugging.
                        println "Checkout PyVcloud sdk code succeeded..."
                        sh "git config --list"
                        sh "git branch"
                    } catch (err) {
                        throwError("Could not checkout PyVcloud sdk code.")
                    }
                }
            }
        }
        //Read test-info.json and create vcd_connection
        stage('read-testbed-json-and-create-vcd-connection') {
            steps {
                script {
                    def props = readJSON text: testbedJson
                    def cell = props['sites'][0]['cells'][0]
                    def vcd_username = cell['credentials']['username']
                    def vcd_password = cell['credentials']['password']

                    def vcd_hostname =
                    cell['deployment']['ovfProperties']['hostname']

                    def vc_server = props['sites'][0]['vcServers'][0]
                    def vc2_server = props['sites'][0]['vcServers'][1]
                    def vc_ip = vc_server['endPointURI'].replace('https://', "")
                    def vc_password = vc_server['credentials']['password']
                    def vc2_ip = ''
                    def vc2_password = ''
                    if (vc2_server != null) {
                        vc2_ip = vc2_server['endPointURI'].replace('https://', "")
                        vc2_password = vc2_server['credentials']['password']
                    }

                    if(vcd_password=='ca$hc0w') {
                        vcd_password = 'ca\\$hc0w'
                        println vcd_password
                    }

                    if (VCD_API_VERSION == '') {
                        VCD_API_VERSION = 32.0
                    }
                    println 'API Version::'+VCD_API_VERSION
                    writeFile file: 'vcd_connection', text:"""
                    VCD_HOST=$vcd_hostname
                    VCD_API_VERSION=$VCD_API_VERSION
                    VCD_ORG=System
                    VCD_USER=$vcd_username
                    VCD_PASSWORD=$vcd_password
                    VC_IP=$vc_ip
                    VC_PASSWORD=$vc_password
                    VC2_IP=$vc2_ip
                    VC2_PASSWORD=$vc2_password
                    """.stripIndent()
                }
            }
        }
        stage('prepare') {
            steps {
                script {
                    // All code is available now, load the methods to do real work
                    externalMethods = load 'support/lib_spmain.groovy'
                }
            }
        }
        stage('install') {
            steps {
                script {
                    // Run this method from the lib.groovy file
                    externalMethods.install()
                }
            }
        }
        stage('run-tox-flake8') {
            steps {
        		script {
                    // Run this method from the lib.groovy file
                    externalMethods.runToxFlake8()
                }
            }
        }
        stage('run-samples') {
            steps {
                script {
                    // Run this method from the lib.groovy file
                    externalMethods.runSamples()
                }
            }
        }
        stage('run-system-test') {
            steps {
                script {
                    externalMethods.runSystemTests()
                }
            }
        }
    }
    post {
        failure {
            echo "Job failed! System test environment will not be cleared."
            script {
                if (externalMethods != null) {
                    // Run this method from the lib.groovy file
                    externalMethods.cleanupWorkspace()
                }
            }
        }
        success {
            echo "Job succeeded! Cleaning up system test environment"
            script {
                if (externalMethods != null) {
                    // Run these methods from the lib.groovy file
                    externalMethods.cleanupSystemTests()
                    externalMethods.cleanupWorkspace()
                }
            }
        }
    }
}
def checkBuildStatus(String buildName, String build) {
    info("Waiting for $buildName '$build' to complete")

    try {
        sh "vcda build -bld $build wait"
    } catch(err) {
        throwError("Error occurred while waiting for build $build")
    }

    def buildStatus = "False"
    try {
        buildStatus = sh (script: "vcda build -bld $build success", returnStdout: true).trim()
    } catch(err) {
        println err
    }

    println "buildStatus: "+ buildStatus
    if(buildStatus != "True") {
        throwError("Failure of $buildName '$build'")
    }
}
/*
    Logs message in red color and throws error
*/
def throwError(message = "") {
    //println "\u001b[31;1m \e[5m ERROR \e[25m: $message \u001b[0m"
    message = message ? message.trim() : ""
    def lineItems = message.split("\n");
    println "\u001b[31;1m [ERROR] ${lineItems[0]} \u001b[0m"
    for(int i = 0; i < lineItems.size(); i++) {
       if(i > 0) {
          println "\u001b[31;1m ${lineItems[i]} \u001b[0m"
       }
    }
    //println "\u001b[31;1m $message \u001b[31;1m \u001b[0m"
    error(message) //signal error
}
/*
    Logs message in blue color
*/
def info(def message = "") {
    //println "\u001b[34;1m INFO: $message \u001b[0m"
    message = message ? message.trim() : ""
    def lineItems = message.split("\n");
    println "\u001b[34;1m [INFO] ${lineItems[0]} \u001b[0m"
    for(int i = 0; i < lineItems.size(); i++) {
       if(i > 0) {
          println "\u001b[34;1m ${lineItems[i]} \u001b[0m"
       }
    }
}