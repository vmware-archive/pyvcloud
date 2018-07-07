# Intiialize the PYVCLOUD_VENV_DIR variable to set the
# Python virtualenv directory for all pipeline scripts
PYVCLOUD_VENV_DIR=${PYVCLOUD_VENV_DIR:-test-env}

# Test the current environment for python3 and pip3
# If not available, the requested script will be run inside Docker
if [ "$PYTHON3_IN_DOCKER" == "" ]; then
    PYTHON3_PATH=`which python3 | cat`
    PIP3_PATH=`which pip3 | cat`

    if [ "$PYTHON3_PATH" == "" ]; then
        PYTHON3_IN_DOCKER=1
    fi

    if [ "$PIP3_PATH" == "" ]; then
        PYTHON3_IN_DOCKER=1
    fi
fi

# Ensure the PYTHON3_IN_DOCKER variable is initialized for testing
if [ "$PYTHON3_IN_DOCKER" == "" ]; then
    PYTHON3_IN_DOCKER=0
fi

# Ensure the VCD_CONNECTION variable is provided or set in the environment
set_vcd_connection() {
    # If provided the file name must be absolute. 
    if [ -n "$1" ]; then
        VCD_CONNECTION=$1
    fi

    if [ -z "$VCD_CONNECTION" ]; then
        VCD_CONNECTION=$HOME/vcd_connection
        if [ -e $HOME/vcd_connection ]; then
            echo "Using default vcd_connection file location: $VCD_CONNECTION"
        else
            echo "Must have $VCD_CONNECTION or give alternative file as argument"
            exit 1
        fi
    fi
}

run_in_docker() {
    # Build the Docker image using the current uid/gid so
    # repeat iterations of the Jenkins environment can 
    # properly cleanup the workspace.
    DOCKER_BUILD=`docker build -q \
        --build-arg build_user=${USER} \
        --build-arg build_uid=$(id -u) \
        --build-arg build_gid=$(id -g) \
        -f support/Dockerfile.build \
        support`
    DOCKER_IMAGE=`echo $DOCKER_BUILD | awk -F: '{print $2}'`

    # Include VCD_CONNECTION as a mounted file and environment variable
    VCD_ARGS=""
    if [ "$VCD_CONNECTION" != "" ]; then
        VCD_ARGS="-eVCD_CONNECTION=$VCD_CONNECTION -v$VCD_CONNECTION:$VCD_CONNECTION"
    fi

    # Run the Docker container with source code mounted along
    # with additional files and environment variables
    docker run --rm \
        -ePYTHON3_IN_DOCKER=0 \
        -ePYVCLOUD_VENV_DIR=$PYVCLOUD_VENV_DIR \
        $VCD_ARGS \
        -v$SRCROOT:$SRCROOT \
        -w$SRCROOT \
        $DOCKER_IMAGE \
        /bin/bash -c "$*"

    EC=$?
    if [ $EC -ne 0 ]; then
        exit $EC
    fi
}