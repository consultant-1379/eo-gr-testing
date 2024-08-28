#!/usr/bin/env groovy

/**
 * This pipeline runs one by one all existed GR RV scenarios (pipelines):
 * - Switchover Rollback When BUR Pod Restarts Scenario
 * - Switchover Rollback When BRO Pod Restarts Scenario
 * - Global Registry Impact On GR Scenario
 * - Update Recovery State Scenario
 * - SFTP server unavailability impact on CVNFM functionality
 * - BRO pod no free memory impact on GR switchover
 * - Disabling Node Networks Scenario
 * - IDAM Leader Unavailability Scenario
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
        SKIP_CLEANUP_REGISTRY = "${env.SKIP_CLEANUP_REGISTRY}"
        ENABLE_VMVNFM_DEBUG_LOG_LEVEL = "${ENABLE_VMVNFM_DEBUG_LOG_LEVEL}"
        // scenarios:
        SWITCHOVER_ROLLBACK_BUR_POD_SCENARIO = "${env.SWITCHOVER_ROLLBACK_BUR_POD_SCENARIO}"
        SWITCHOVER_ROLLBACK_BRO_POD_SCENARIO = "${env.SWITCHOVER_ROLLBACK_BRO_POD_SCENARIO}"
        GLOBAL_REGISTRY_IMPACT_ON_GR_SCENARIO = "${env.GLOBAL_REGISTRY_IMPACT_ON_GR_SCENARIO}"
        UPDATE_RECOVERY_STATE_SCENARIO = "${env.UPDATE_RECOVERY_STATE_SCENARIO}"
        SFTP_SERVER_UNAVAILABILITY_IMPACT_ON_CVNFM_SCENARIO = "${SFTP_SERVER_UNAVAILABILITY_IMPACT_ON_CVNFM_SCENARIO}"
        BRO_NO_FREE_MEMORY_IMPACT_ON_GR_SCENARIO = "${BRO_NO_FREE_MEMORY_IMPACT_ON_GR_SCENARIO}"
        DISABLING_NODE_NETWORKS_SCENARIO = "${DISABLING_NODE_NETWORKS_SCENARIO}"
        IDAM_LEADER_UNAVAILABILITY_SCENARIO = "${IDAM_LEADER_UNAVAILABILITY_SCENARIO}"

    }
    stages {
        stage('Set build name') {
            steps {
                script {
                    currentBuild.displayName = "${env.BUILD_NUMBER}_${env.ACTIVE_SITE}_${env.PASSIVE_SITE}_${env.EO_VERSION}"
                }
            }
        }
        stage('Run Switchover Rollback When BUR Pod Restarts Scenario') {
            when {
                environment name: 'SWITCHOVER_ROLLBACK_BUR_POD_SCENARIO', value: 'true'
            }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-rv-verify-pod-restart-impact-robustness-scenario',
                        parameters: getCommonScenarioParameters() + [
                            string(name: 'TEST_SCENARIO', value: 'switchover_rollback_bur_pod')
                        ]
                    }
                }
            }
        }
        stage('Run Switchover Rollback When BRO Pod Restarts Scenario') {
            when {
                environment name: 'SWITCHOVER_ROLLBACK_BRO_POD_SCENARIO', value: 'true'
            }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-rv-verify-pod-restart-impact-robustness-scenario',
                        parameters: getCommonScenarioParameters() + [
                            string(name: 'TEST_SCENARIO', value: 'switchover_rollback_bro_pod')
                        ]
                    }
                }
            }
        }
        stage('Run Verify Global Registry Impact On GR Scenario') {
            when {
                environment name: 'GLOBAL_REGISTRY_IMPACT_ON_GR_SCENARIO', value: 'true'
            }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-rv-verify-global-registry-impact-robustness-scenario',
                        parameters: getCommonScenarioParameters()
                    }
                }
            }
        }
        stage('Run Update Recovery State Scenario') {
            when {
                environment name: 'UPDATE_RECOVERY_STATE_SCENARIO', value: 'true'
            }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-rv-verify-update-recovery-state-robustness-scenario',
                        parameters: getCommonScenarioParameters()
                    }
                }
            }
        }
        stage('Run SFTP Server Unavailability Impact On CVNFM Functionality Scenario') {
            when {
                environment name: 'SFTP_SERVER_UNAVAILABILITY_IMPACT_ON_CVNFM_SCENARIO', value: 'true'
            }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-rv-verify-sftp-unavailability-impact-on-cvnfm-robustness-scenario',
                        parameters: getCommonScenarioParameters()
                    }
                }
            }
        }
        stage('Run Verify BRO Pod No Free Memory Impact On GR Switchover Scenario') {
            when {
                environment name: 'BRO_NO_FREE_MEMORY_IMPACT_ON_GR_SCENARIO', value: 'true'
            }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-rv-verify-bro-no-free-memory-impact-robustness-scenario',
                        parameters: getCommonScenarioParameters()
                    }
                }
            }
        }
        stage('Run Verify Disabling Networks on BUR Worker Node of Active Site Impact on GR Scenario') {
            when {
                environment name: 'DISABLING_NODE_NETWORKS_SCENARIO', value: 'true'
            }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-rv-verify-disabling-node-networks-robustness-scenario',
                        parameters: getCommonScenarioParameters()
                    }
                }
            }
        }
        stage('Run Verify Idam Leader Pod Unavailability Impact on GR Scenario') {
            when {
                environment name: 'IDAM_LEADER_UNAVAILABILITY_SCENARIO', value: 'true'
            }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-rv-verify-idam-leader-unavailability-impact-robustness-scenario',
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