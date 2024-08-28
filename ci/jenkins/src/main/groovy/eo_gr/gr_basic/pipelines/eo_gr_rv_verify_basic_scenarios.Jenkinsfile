#!/usr/bin/env groovy

/**
 * This pipeline runs one by one selected basic GR RV scenarios (pipelines):
 * - Positive End-to-end Scenario
 * - Switchover When Active Site Not Available Scenario
 */

pipeline {
    agent {
        label env.SLAVE_LABEL
    }
    environment {
        ACTIVE_SITE = "${env.ACTIVE_SITE}"
        PASSIVE_SITE = "${env.PASSIVE_SITE}"
        VIM = "${env.VIM}"
        SLAVE_LABEL = "${env.SLAVE_LABEL}"
        PRETTY_API_LOGS = "${env.PRETTY_API_LOGS}"
        EO_LOG_COLLECTION = "${EO_LOG_COLLECTION}"
        EO_VERSIONS_COLLECTION = "${EO_VERSIONS_COLLECTION}"
        EO_VERSION = "${env.EO_VERSION}"
        DEPLOYMENT_MANAGER_VERSION = "${env.DEPLOYMENT_MANAGER_VERSION}"
        ENABLE_VM_VNFM_HA = "${env.ENABLE_VM_VNFM_HA}"
        GERRIT_BRANCH = "${env.GERRIT_BRANCH}"
        GERRIT_REFSPEC = "${env.GERRIT_REFSPEC}"
        GERRIT_BRANCH_EO_INSTALL = "${env.GERRIT_BRANCH_EO_INSTALL}"
        GERRIT_REFSPEC_EO_INSTALL = "${GERRIT_REFSPEC_EO_INSTALL}"
        NAMESPACE = "${env.NAMESPACE}"
        USE_LOCAL_DNS = true
        OVERRIDE = "${env.OVERRIDE}"
        SKIP_EO_DEPLOY_AND_CONFIGURE = "${env.SKIP_EO_DEPLOY_AND_CONFIGURE}"
        SKIP_SFTP_BANDWIDTH_MEASUREMENT = "${env.SKIP_SFTP_BANDWIDTH_MEASUREMENT}"
        SKIP_CLEANUP_REGISTRY = "${env.SKIP_CLEANUP_REGISTRY}"
        ENABLE_VMVNFM_DEBUG_LOG_LEVEL = "${ENABLE_VMVNFM_DEBUG_LOG_LEVEL}"
        // scenarios:
        POSITIVE_END_TO_END_SCENARIO = "${env.POSITIVE_END_TO_END_SCENARIO}"
        SWITCHOVER_WHEN_ACTIVE_SITE_NOT_AVAILABLE_SCENARIO = "${env.SWITCHOVER_WHEN_ACTIVE_SITE_NOT_AVAILABLE_SCENARIO}"

    }
    stages {
        stage('Set build name') {
            steps {
                script {
                    currentBuild.displayName = "${env.BUILD_NUMBER}_${env.ACTIVE_SITE}_${env.PASSIVE_SITE}_${env.EO_VERSION}"
                }
            }
        }
        stage('Run Positive End-to-end Scenario') {
            when {
                environment name: 'POSITIVE_END_TO_END_SCENARIO', value: 'true'
            }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-rv-verify-positive-end-to-end-basic-scenario',
                        parameters: getCommonScenarioParameters()
                    }
                }
            }
        }
        stage('Run Switchover When Active Site Not Available Scenario') {
            when {
                environment name: 'SWITCHOVER_WHEN_ACTIVE_SITE_NOT_AVAILABLE_SCENARIO', value: 'true'
            }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-rv-verify-active-site-not-available-basic-scenario',
                        parameters: getCommonScenarioParameters()
                    }
                }
            }
        }
    }
}


def getCommonScenarioParameters() {
        // Common Parameters that can be used in scenario pipeline job as 'parameters'
        return [
            string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
            string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
            string(name: 'SLAVE_LABEL', value: env.SLAVE_LABEL),
            string(name: 'VIM', value: env.VIM),
            string(name: 'EO_VERSION', value: env.EO_VERSION),
            booleanParam(name: 'ENABLE_VM_VNFM_HA', value: env.ENABLE_VM_VNFM_HA),
            string(name: 'NAMESPACE', value: env.NAMESPACE),
            booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
            string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
            string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
            string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
            string(name: 'GERRIT_BRANCH_EO_INSTALL', value: env.GERRIT_BRANCH_EO_INSTALL),
            string(name: 'GERRIT_REFSPEC_EO_INSTALL', value: env.GERRIT_REFSPEC_EO_INSTALL),
            string(name: 'OVERRIDE', value: env.OVERRIDE),
            booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
            booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
            booleanParam(name: 'EO_VERSIONS_COLLECTION', value: env.EO_VERSIONS_COLLECTION),
            booleanParam(name: 'SKIP_EO_DEPLOY_AND_CONFIGURE', value: env.SKIP_EO_DEPLOY_AND_CONFIGURE),
            booleanParam(name: 'SKIP_CLEANUP_REGISTRY', value: env.SKIP_CLEANUP_REGISTRY),
            booleanParam(name: 'ENABLE_VMVNFM_DEBUG_LOG_LEVEL', value: env.ENABLE_VMVNFM_DEBUG_LOG_LEVEL),
        ]
    }