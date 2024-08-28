#!/usr/bin/env groovy

/* DESCRIPTION:
 * This pipeline verifies SFTP server unavailability impact on CVNFM functionality
 * For detailed information on the stages, please refer to EO-170890.
 */

pipeline {
    agent {
        label env.SLAVE_LABEL
    }
    environment {
        ACTIVE_SITE = "${env.ACTIVE_SITE}"
        PASSIVE_SITE = "${env.PASSIVE_SITE}"
        GR_STAGE_SHARED_NAME = "${env.GR_STAGE_SHARED_NAME}"
        VIM = "${env.VIM}"
        EO_VERSION = "${env.EO_VERSION}"
        USE_LOCAL_DNS = true
        DEPLOYMENT_MANAGER_VERSION = "${env.DEPLOYMENT_MANAGER_VERSION}"
        PRETTY_API_LOGS = "${env.PRETTY_API_LOGS}"
        GERRIT_BRANCH = "${env.GERRIT_BRANCH}"
        GERRIT_REFSPEC = "${env.GERRIT_REFSPEC}"
        GERRIT_BRANCH_EO_INSTALL = "${env.GERRIT_BRANCH_EO_INSTALL}"
        GERRIT_REFSPEC_EO_INSTALL = "${GERRIT_REFSPEC_EO_INSTALL}"
        NAMESPACE = "${env.NAMESPACE}"
        OVERRIDE = "${env.OVERRIDE}"
        SKIP_EO_DEPLOY_AND_CONFIGURE = "${SKIP_EO_DEPLOY_AND_CONFIGURE}"
        SLAVE_LABEL = "${SLAVE_LABEL}"
        SKIP_CLEANUP_REGISTRY = "${env.SKIP_CLEANUP_REGISTRY}"
    }
    stages {
        stage('Set build name') {
            steps {
                script {
                    currentBuild.displayName = "${env.BUILD_NUMBER}_${env.ACTIVE_SITE}_${env.PASSIVE_SITE}_${env.EO_VERSION}"
                }
            }
        }
        stage('Deploy and configure environments') {
            when {
                environment name: 'SKIP_EO_DEPLOY_AND_CONFIGURE', value: 'false'
            }
            steps {
                script {
                    build job: 'eo-gr-deploy-and-configure-rv-environments-job',
                    parameters: [
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
                        booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                        booleanParam(name: 'SKIP_CLEANUP_REGISTRY', value: env.SKIP_CLEANUP_REGISTRY),
                    ]
                }
            }
        }
        stage('Run test CVNFM when SFTP is unavailable before switchover (Phase A)') {
            steps {
                script {
                    build job: 'eo-gr-tests-rv-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                        string(name: 'VIM', value: env.VIM),
                        string(name: 'TEST_TAG', value: 'cvnfm_sftp_unavailable_before_switchover'),
                        string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                        booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                        string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                        string(name: 'OVERRIDE', value: env.OVERRIDE),
                        booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                        booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                    ]
                }
            }
        }
        stage('Switch DNS settings to upcoming new Active Site') {
            steps {
                script {
                    build job: 'eo-gr-deploy-dns-server-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.PASSIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                    ]
                }
            }
        }
        stage('Run switchover with available backup Id') {
            steps {
                script {
                    build job: 'eo-gr-tests-rv-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                        string(name: 'VIM', value: env.VIM),
                        string(name: 'TEST_TAG', value: 'switchover_with_available_backup_id_without_backup_update_check'),
                        string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                        booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                        string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                        booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                        booleanParam(name: 'COLLECT_SWITCHOVER_LOGS', value: true),
                        booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                    ]
                }
            }
        }
        stage('Install certificates for signed CNF packages on the new Active site') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-install-cvnfm-certificates-job',
                            parameters: [
                            string(name: 'ACTIVE_SITE', value: env.PASSIVE_SITE),
                            booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                            string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                            string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        ]
                    }
                }
            }
        }
        stage('Run test CVNFM when SFTP is unavailable after switchover (Phase B)') {
            steps {
                script {
                    build job: 'eo-gr-tests-rv-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.PASSIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'VIM', value: env.VIM),
                        string(name: 'TEST_TAG', value: 'cvnfm_sftp_unavailable_after_switchover'),
                        booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                        string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                        string(name: 'OVERRIDE', value: env.OVERRIDE),
                        booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                        booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                    ]
                }
            }
        }
    }
    post {
        always {
            build job: 'eo-gr-clean-up-test-assets-and-dns',
            parameters: [
                string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                string(name: 'VIM', value: env.VIM),
                booleanParam(name: 'DELETE_ALL', value: false),
                string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
            ]
        }
    }
}
