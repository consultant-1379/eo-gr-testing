#!/usr/bin/env groovy

/**
 * This pipeline sets up the environment and executes test_global_registry_impact_on_gr (OTC-14102).
 * For detailed information on the stages, please refer to EO-169953.
 */

pipeline {
    agent {
        node {
            label env.SLAVE_LABEL
        }
    }

    environment {
        ACTIVE_SITE = "${env.ACTIVE_SITE}"
        PASSIVE_SITE = "${env.PASSIVE_SITE}"
        GR_STAGE_SHARED_NAME = "${env.GR_STAGE_SHARED_NAME}-${env.BUILD_NUMBER}"
        VIM = "${env.VIM}"
        PRETTY_API_LOGS = "${env.PRETTY_API_LOGS}"
        EO_VERSION = "${env.EO_VERSION}"
        ENABLE_VM_VNFM_HA = "${env.ENABLE_VM_VNFM_HA}"
        GERRIT_BRANCH = "${env.GERRIT_BRANCH}"
        GERRIT_REFSPEC = "${env.GERRIT_REFSPEC}"
        GERRIT_BRANCH_EO_INSTALL = "${env.GERRIT_BRANCH_EO_INSTALL}"
        GERRIT_REFSPEC_EO_INSTALL = "${GERRIT_REFSPEC_EO_INSTALL}"
        NAMESPACE = "${env.NAMESPACE}"
        USE_LOCAL_DNS = true
        DEPLOYMENT_MANAGER_VERSION = "${env.DEPLOYMENT_MANAGER_VERSION}"
        EO_LOG_COLLECTION = "${env.EO_LOG_COLLECTION}"
        SKIP_EO_DEPLOY_AND_CONFIGURE = "${env.SKIP_EO_DEPLOY_AND_CONFIGURE}"
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
                expression {
                    return env.SKIP_EO_DEPLOY_AND_CONFIGURE == 'false';
                }
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
        stage('Running test scenario') {
            steps {
                script {
                    build job: 'eo-gr-tests-rv-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                        string(name: 'VIM', value: env.VIM),
                        string(name: 'TEST_TAG', value: 'global_registry_impact_on_gr'),
                        booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                        string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                        string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                        string(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                        booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                    ]
                }
            }
        }
    }
    post {
        always {
            script {
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
}
