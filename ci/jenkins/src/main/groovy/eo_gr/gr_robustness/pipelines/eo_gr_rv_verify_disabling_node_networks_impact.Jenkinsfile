#!/usr/bin/env groovy

/*
 * This pipeline sets up the environment and executes switchover with disable networks on bur worker node of Active Site scenario:
 * For detailed information on the stages and test scenario please refer to OTC-14062 and EO-170895.
*/

pipeline {
    agent {
        label env.SLAVE_LABEL
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
        OVERRIDE = "${env.OVERRIDE}"
        DEPLOYMENT_MANAGER_VERSION = "${env.DEPLOYMENT_MANAGER_VERSION}"
        SKIP_EO_DEPLOY_AND_CONFIGURE = "${env.SKIP_EO_DEPLOY_AND_CONFIGURE}"
        EO_LOG_COLLECTION = "${env.EO_LOG_COLLECTION}"
        SKIP_CLEANUP_REGISTRY = "${env.SKIP_CLEANUP_REGISTRY}"
        ENABLE_VMVNFM_DEBUG_LOG_LEVEL = "${ENABLE_VMVNFM_DEBUG_LOG_LEVEL}"
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
                        string(name: 'GERRIT_BRANCH_EO_INSTALL', value: env.GERRIT_BRANCH_EO_INSTALL),
                        string(name: 'GERRIT_REFSPEC_EO_INSTALL', value: env.GERRIT_REFSPEC_EO_INSTALL),
                        string(name: 'NAMESPACE', value: env.NAMESPACE),
                        booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                        string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                        booleanParam(name: 'ENABLE_VM_VNFM_HA', value: env.ENABLE_VM_VNFM_HA),
                        booleanParam(name: 'SKIP_CLEANUP_REGISTRY', value: env.SKIP_CLEANUP_REGISTRY),
                    ]
                }
            }
        }
        stage('Running CVNFM and VMVNFM tests phase A') {
            parallel {
                stage('Run CVFNM phase A') {
                    steps {
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            script {
                                build job: 'eo-gr-tests-rv-job',
                                parameters: [
                                    string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                                    string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                                    string(name: 'VIM', value: env.VIM),
                                    string(name: 'TEST_TAG', value: 'cvnfm_phase_A'),
                                    booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                                    string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                                    string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                                    string(name: 'OVERRIDE', value: env.OVERRIDE),
                                    string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                    string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                    booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                                    booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                                ]
                            }
                        }
                    }
                }
                stage('Run VMVNFM phase A'){
                    steps {
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            script {
                                build job: 'eo-gr-tests-rv-job',
                                parameters: [
                                    string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                                    string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                                    string(name: 'VIM', value: env.VIM),
                                    string(name: 'TEST_TAG', value: 'vmvnfm_phase_A'),
                                    booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                                    string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                                    string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                                    string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                    string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                    booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                                    booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                                    booleanParam(name: 'ENABLE_VMVNFM_DEBUG_LOG_LEVEL', value: env.ENABLE_VMVNFM_DEBUG_LOG_LEVEL),
                                ]
                            }
                        }
                    }
                }
            }
        }
        stage('Switch DNS settings to the Passive site before switchover') {
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
        stage('Running Switchover with disabling network interfaces on worker node where BUR pod of Active Site located scenario') {
            steps {
                script {
                    build job: 'eo-gr-tests-rv-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                        string(name: 'VIM', value: env.VIM),
                        string(name: 'TEST_TAG', value: "switchover_disable_network_on_bur_worker_node_active_site"),
                        booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                        string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                        string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                        booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                        booleanParam(name: 'COLLECT_SWITCHOVER_LOGS', value: true),
                        booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                    ]
                }
            }
        }
        stage('Install certificates for signed CNF packages on the Passive site') {
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
        stage('Running CVNFM and VMVNFM tests phase B') {
            parallel {
                stage('Run CVFNM phase B') {
                    steps {
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            script {
                                build job: 'eo-gr-tests-rv-job',
                                parameters: [
                                    string(name: 'ACTIVE_SITE', value: env.PASSIVE_SITE),
                                    string(name: 'PASSIVE_SITE', value: env.ACTIVE_SITE),
                                    string(name: 'VIM', value: env.VIM),
                                    string(name: 'TEST_TAG', value: 'cvnfm_phase_B'),
                                    booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                                    string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                                    string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                                    string(name: 'OVERRIDE', value: env.OVERRIDE),
                                    string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                    string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                    booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                                    booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                                ]
                            }
                        }
                    }
                }
                stage('Run VMVNFM phase B') {
                    steps {
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            script {
                                build job: 'eo-gr-tests-rv-job',
                                parameters: [
                                    string(name: 'ACTIVE_SITE', value: env.PASSIVE_SITE),
                                    string(name: 'PASSIVE_SITE', value: env.ACTIVE_SITE),
                                    string(name: 'VIM', value: env.VIM),
                                    string(name: 'TEST_TAG', value: 'vmvnfm_phase_B'),
                                    booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                                    string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                                    string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                                    string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                    string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                    booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                                    booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                                    booleanParam(name: 'ENABLE_VMVNFM_DEBUG_LOG_LEVEL', value: env.ENABLE_VMVNFM_DEBUG_LOG_LEVEL),
                                ]
                            }
                        }
                    }
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
