#!/usr/bin/env groovy

/**
 * This pipeline sets up the environment and executes next GR related stages:
 *  1. Active site become unavailable and trigger switchover with provided backup id
 *  2. Active site become available and trigger switchover
 * For detailed information on the stages, please refer to EO-170894.
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
        SLAVE_LABEL = "${env.SLAVE_LABEL}"
        PRETTY_API_LOGS = "${env.PRETTY_API_LOGS}"
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
        EO_VERSIONS_COLLECTION = "${env.EO_VERSIONS_COLLECTION}"
        EO_LOG_COLLECTION = "${env.EO_LOG_COLLECTION}"
        SKIP_SFTP_BANDWIDTH_MEASUREMENT = "${env.SKIP_SFTP_BANDWIDTH_MEASUREMENT}"
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
                        booleanParam(name: 'SKIP_SFTP_BANDWIDTH_MEASUREMENT', value: env.SKIP_SFTP_BANDWIDTH_MEASUREMENT),
                        booleanParam(name: 'SKIP_CLEANUP_REGISTRY', value: env.SKIP_CLEANUP_REGISTRY),
                    ]
                }
            }
        }
        stage('CVNFM/VMVNFM tests phase A') {
            parallel {
                stage('CVNFM tests phase A') {
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
                                    string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                                    string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                    string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                    string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                                    string(name: 'OVERRIDE', value: env.OVERRIDE),
                                    booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                                    booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                                ]
                            }
                        }
                    }
                }
                stage('VMVNFM tests phase A') {
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
                                    string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                                    string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                    string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                    string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
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
        stage('Make site A unavailable and trigger switchover site A -> site B') {
            steps {
                script {
                    build job: 'eo-gr-tests-rv-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                        string(name: 'VIM', value: env.VIM),
                        string(name: 'TEST_TAG', value: 'switchover_active_site_not_available'),
                        booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                        string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                        booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                        string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                        booleanParam(name: 'COLLECT_SWITCHOVER_LOGS', value: true),
                        booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                    ]
                }
            }
        }
        stage('Workaround for certificates EO-170463') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-tests-rv-job',
                        parameters: [
                            string(name: 'ACTIVE_SITE', value: env.PASSIVE_SITE),
                            string(name: 'PASSIVE_SITE', value: env.ACTIVE_SITE),
                            string(name: 'TEST_TAG', value: 'restart_api_gateway_pod'),
                            booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                            string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                            string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                            string(name: 'OVERRIDE', value: env.OVERRIDE),
                            booleanParam(name: 'EO_LOG_COLLECTION', value: false)
                        ]
                    }
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
                            booleanParam(name: 'RUN_WITH_LOCAL_DNS', value: env.RUN_WITH_LOCAL_DNS),
                            string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                            string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        ]
                    }
                }
            }
        }
        stage('CVNFM/VMVNFM tests phase B') {
            parallel {
                stage('CVNFM tests phase B') {
                    steps {
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            script {
                                build job: 'eo-gr-tests-rv-job',
                                parameters: [
                                    string(name: 'ACTIVE_SITE', value: env.PASSIVE_SITE),
                                    string(name: 'PASSIVE_SITE', value: env.ACTIVE_SITE),
                                    string(name: 'VIM', value: env.VIM),
                                    string(name: 'TEST_TAG', value: 'cvnfm_phase_B'),
                                    string(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                                    string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                                    string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                    string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                    string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                                    string(name: 'OVERRIDE', value: env.OVERRIDE),
                                    booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                                    booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                                ]
                            }
                        }
                    }
                }
                stage('VMVNFM tests phase B') {
                    steps {
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            script {
                                build job: 'eo-gr-tests-rv-job',
                                parameters: [
                                    string(name: 'ACTIVE_SITE', value: env.PASSIVE_SITE),
                                    string(name: 'PASSIVE_SITE', value: env.ACTIVE_SITE),
                                    string(name: 'VIM', value: env.VIM),
                                    string(name: 'TEST_TAG', value: 'vmvnfm_phase_B'),
                                    string(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                                    string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                                    string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                    string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                    string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
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
        stage('Switch DNS settings to the Active site before switchback') {
            steps {
                script {
                    build job: 'eo-gr-deploy-dns-server-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                    ]
                }
            }
        }
        stage('Make site B available and trigger switchover site B -> site A') {
            steps {
                script {
                    build job: 'eo-gr-tests-rv-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.PASSIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'VIM', value: env.VIM),
                        string(name: 'TEST_TAG', value: 'make_passive_site_available_and_run_switchover'),
                        booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                        string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                        booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                        string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                        booleanParam(name: 'COLLECT_SWITCHOVER_LOGS', value: true),
                        booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                    ]
                }
            }
        }
        stage('CVNFM/VMVNFM tests phase C') {
            parallel {
                stage('CVNFM tests phase C') {
                    steps {
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            script {
                                build job: 'eo-gr-tests-rv-job',
                                parameters: [
                                    string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                                    string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                                    string(name: 'VIM', value: env.VIM),
                                    string(name: 'TEST_TAG', value: 'cvnfm_phase_C'),
                                    booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                                    string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                                    string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                    string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                    string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                                    string(name: 'OVERRIDE', value: env.OVERRIDE),
                                    booleanParam(name: 'PRETTY_API_LOGS', value: env.PRETTY_API_LOGS),
                                    booleanParam(name: 'EO_LOG_COLLECTION', value: env.EO_LOG_COLLECTION),
                                ]
                            }
                        }
                    }
                }
                stage('VMVNFM tests phase C') {
                    steps {
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            script {
                                build job: 'eo-gr-tests-rv-job',
                                parameters: [
                                    string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                                    string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                                    string(name: 'VIM', value: env.VIM),
                                    string(name: 'TEST_TAG', value: 'vmvnfm_phase_C'),
                                    booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                                    string(name: 'DEPLOYMENT_MANAGER_VERSION', value: env.DEPLOYMENT_MANAGER_VERSION),
                                    string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                    string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                    string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
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
