#!/usr/bin/env bash
# Virtual environment name:
VENV=picture_tools_venv

# Get script directory:
SCRIPT_DIR=$PWD

#=== Function ===========================
# Name: activate_virtual_env
# Description: Create / Activate a virtual environment
# Parameters:
#   $1 = name of the virtual environment
#   $2 = python version (e.g. 'python2.7' or 'python3.5')
#   $3 = name of the requirements file
#========================================
function activate_virtual_env()
{
    # Check if the virtual environment is present
    if [ ! -d "${SCRIPT_DIR}"/"${VENV}" ] ; then
        # Create the virtual environment if it is not available
        virtualenv -p "${2}" "${SCRIPT_DIR}"/"${VENV}"
    fi

    # Activate the virtual environment
    set +u
        source "${SCRIPT_DIR}"/"${VENV}"/bin/activate
    set -u

    # Make the location of the directory with Python site-packages available
    PYTHON_SITE_PACKAGES="${SCRIPT_DIR}"/"${VENV}"/lib/"${2}"/site-packages

    # Make sure latest version of requirements are available
    pip install -r "${SCRIPT_DIR}"/"${3}"

    return 0
}

# Activate the virtual environment for picture tools:
activate_virtual_env "${VENV}" "python3" "requirements_3.txt"

# Run picture tools:
nohup python3 "${SCRIPT_DIR}"/main.py > /dev/null 2>&1 &

