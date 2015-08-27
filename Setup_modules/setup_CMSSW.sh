#!/bin/bash

###############################################################
###############################################################
##
## Script checks and sets up CMSSW environment
##
###############################################################
###############################################################


## Script's parameters
######################

SCRAM_ARCH_VER_CHOICE=slc6_amd64_gcc491
CMSSW_VER_CHOICE=CMSSW_7_4_7
START_DIR=${PWD}


## Script's execution code
##########################

# Check if scram is available
if command -v scram > /dev/null 2>&1; then
	# Check if CMSSW environment is the chosen one and is set-up
	if [ "${CMSSW_VERSION}" = "${CMSSW_VER_CHOICE}" ] && [ -d "${CMSSW_BASE}" ]; then
		echo "The CMSSW environment is already properly set. Version: ${CMSSW_VERSION}. Architecture: ${SCRAM_ARCH}."
	else
		if [ -d "${CMSSW_VER_CHOICE}" ]; then
			# Try using an existing CMSSW area
			cd ${CMSSW_VER_CHOICE}/src/
			cmsenv
			cd ${START_DIR}
		else
			# Try getting a new CMSSW area
			export SCRAM_ARCH=${SCRAM_ARCH_VER_CHOICE}

			scram project ${CMSSW_VER_CHOICE}
			cd ${CMSSW_VER_CHOICE}/src/
			cmsenv
			# This one needed to later use git cms-addpkg
			git cms-init
			cd ${START_DIR}
		fi
		
		# At this point CMSSW should be fine. Let us check.
		if [ "${CMSSW_VERSION}" = "${CMSSW_VER_CHOICE}" ] && [ -d "${CMSSW_BASE}" ]; then
			echo "The CMSSW environment is properly set. Version: ${CMSSW_VERSION}. Architecture: ${SCRAM_ARCH}."
		else
			echo "ERROR: A script has failed to set the CMSSW environment." 1>&2
		fi
	fi
else
	echo "ERROR: scram is not available. Is this a proper machine?" 1>&2
fi
