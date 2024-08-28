#!/usr/bin/env groovy

/* DESCRIPTION:
 * This pipeline performs pre setup actions for run RV tests
 * - Cleanup test CNF namespaces
 * - Cleanup sites registries
 * - Install EO on the Active and Passive sites
 * - Setup SFTP server
 * - Create superuser password on both sites
 * - Copy KMS key
 * - Switch DNS settings to Active Site
 * - Create new EVNFM user
 * - Install certificates for signed CNF packages on the Active site
 */

pipeline {
    agent {
        label env.SLAVE_LABEL
    }

    environment {
        ACTIVE_SITE = "${env.ACTIVE_SITE}"
        PASSIVE_SITE = "${env.PASSIVE_SITE}"
        VIM = "${env.VIM}"
        EO_VERSION = "${env.EO_VERSION}#${env.DEPLOYMENT_MANAGER_VERSION}"
        USE_LOCAL_DNS = true
        PRETTY_API_LOGS = "${env.PRETTY_API_LOGS}"
        GERRIT_BRANCH = "${env.GERRIT_BRANCH}"
        GERRIT_REFSPEC = "${env.GERRIT_REFSPEC}"
        GERRIT_BRANCH_EO_INSTALL = "${env.GERRIT_BRANCH_EO_INSTALL}"
        GERRIT_REFSPEC_EO_INSTALL = "${GERRIT_REFSPEC_EO_INSTALL}"
        NAMESPACE = "${env.NAMESPACE}"
        SKIP_CLEANUP_REGISTRY = "${env.SKIP_CLEANUP_REGISTRY}"
        SKIP_CREATE_SUPERUSER_PASSWORD_STAGE = "${env.SKIP_CREATE_SUPERUSER_PASSWORD_STAGE}"
        SKIP_COPY_KMS_KEYS_AFTER_SITES_INSTALLATION = "${env.SKIP_COPY_KMS_KEYS_AFTER_SITES_INSTALLATION}"
        SKIP_SFTP_BANDWIDTH_MEASUREMENT = "${env.SKIP_SFTP_BANDWIDTH_MEASUREMENT}"
    }

    stages {
        stage('Set build name') {
            steps {
                script {
                    currentBuild.displayName = "${env.BUILD_NUMBER}_${env.ACTIVE_SITE}_${env.PASSIVE_SITE}_${env.EO_VERSION}"
                }
            }
        }
        stage('Cleanup VIM zone, CNF namespaces and previous DNS configurations') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-clean-up-test-assets-and-dns',
                        parameters: [
                            string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                            string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                            string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                            string(name: 'VIM', value: env.VIM),
                            booleanParam(name: 'DELETE_ALL', value: true),
                            string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                            string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        ]
                    }
                }
            }
        }
        stage('Configure DNS settings') {
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
        stage('Setup SFTP server') {
            steps {
                script {
                    build job: 'eo-gr-deploy-bur-sftp-server-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                        booleanParam(name: 'SKIP_BANDWIDTH_MEASUREMENT', value: env.SKIP_SFTP_BANDWIDTH_MEASUREMENT),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                    ]
                }
            }
        }
        stage('Cleanup sites registries') {
            when {
                environment name: 'SKIP_CLEANUP_REGISTRY', value: 'false'
            }
            parallel {
                stage('Cleanup Active Site registry') {
                    steps {
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            script {
                                build job: 'eo-gr-clean-up-registry-job',
                                parameters: [
                                    string(name: 'ENV', value: env.ACTIVE_SITE),
                                    booleanParam(name: 'DELETE_NODE_IMAGES', value: false),
                                    string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                    string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                    string(name: 'GERRIT_BRANCH_EO_INSTALL', value: env.GERRIT_BRANCH_EO_INSTALL),
                                    string(name: 'GERRIT_REFSPEC_EO_INSTALL', value: env.GERRIT_REFSPEC_EO_INSTALL),
                                ]
                            }
                        }
                    }
                }
                stage('Cleanup Passive Site registry'){
                    steps {
                        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                            script {
                                build job: 'eo-gr-clean-up-registry-job',
                                parameters: [
                                    string(name: 'ENV', value: env.PASSIVE_SITE),
                                    booleanParam(name: 'DELETE_NODE_IMAGES', value: true),
                                    string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                    string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                    string(name: 'GERRIT_BRANCH_EO_INSTALL', value: env.GERRIT_BRANCH_EO_INSTALL),
                                    string(name: 'GERRIT_REFSPEC_EO_INSTALL', value: env.GERRIT_REFSPEC_EO_INSTALL),
                                ]
                            }
                        }
                    }
                }
            }
        }
        stage('Install EO on the Active and Passive sites') {
            parallel {
                stage('Install Active site') {
                    steps {
                        script {
                            build job: 'eo-gr-install-site-job',
                            parameters: [
                                string(name: 'ENV', value: env.ACTIVE_SITE),
                                string(name: 'EO_VERSION', value: env.EO_VERSION),
                                booleanParam(name: 'ENABLE_VM_VNFM_HA', value: env.ENABLE_VM_VNFM_HA),
                                booleanParam(name: 'ENABLE_GR', value: true),
                                string(name: 'CLUSTER_ROLE', value: 'PRIMARY'),
                                string(name: 'NEIGHBOR_ENV', value: env.PASSIVE_SITE),
                                string(name: 'NAMESPACE', value: env.NAMESPACE),
                                string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                string(name: 'GERRIT_BRANCH_EO_INSTALL', value: env.GERRIT_BRANCH_EO_INSTALL),
                                string(name: 'GERRIT_REFSPEC_EO_INSTALL', value: env.GERRIT_REFSPEC_EO_INSTALL),
                            ]
                        }
                    }
                }
                stage('Install Passive site') {
                    steps {
                        script {
                            build job: 'eo-gr-install-site-job',
                            parameters: [
                                string(name: 'ENV', value: env.PASSIVE_SITE),
                                string(name: 'EO_VERSION', value: env.EO_VERSION),
                                booleanParam(name: 'ENABLE_VM_VNFM_HA', value: env.ENABLE_VM_VNFM_HA),
                                booleanParam(name: 'ENABLE_GR', value: true),
                                string(name: 'CLUSTER_ROLE', value: 'SECONDARY'),
                                string(name: 'NEIGHBOR_ENV', value: env.ACTIVE_SITE),
                                string(name: 'NAMESPACE', value: env.NAMESPACE),
                                string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                                string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                                string(name: 'GERRIT_BRANCH_EO_INSTALL', value: env.GERRIT_BRANCH_EO_INSTALL),
                                string(name: 'GERRIT_REFSPEC_EO_INSTALL', value: env.GERRIT_REFSPEC_EO_INSTALL),
                            ]
                        }
                    }
                }
            }
        }
        stage('Create superuser password on both sites') {
            when {
                environment name: 'SKIP_CREATE_SUPERUSER_PASSWORD_STAGE', value: 'false'
            }
            steps {
                script {
                    build job: 'eo-gr-update-superuser-password-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                    ]
                }
            }
        }
        stage('Copy KMS key') {
            when {
                environment name: 'SKIP_COPY_KMS_KEYS_AFTER_SITES_INSTALLATION', value: 'false'
            }
            steps {
                script {
                    build job: 'eo-gr-copy-kms-key-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                    ]
                }
            }
        }
        stage('Create new EVNFM user') {
            steps {
                script {
                    build job: 'eo-gr-create-new-evnfm-user-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                        booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                    ]
                }
            }
        }
        stage('Install certificates for signed CNF packages on the Active site') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-install-cvnfm-certificates-job',
                        parameters: [
                            string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                            booleanParam(name: 'USE_LOCAL_DNS', value: env.USE_LOCAL_DNS),
                            string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                            string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        ]
                    }
                }
            }
        }
        stage('Collect EO logs') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-collecting-logs-job',
                        parameters: [
                            string(name: 'SITE_NAME', value: env.ACTIVE_SITE),
                            string(name: 'ADDITIONAL_SITE_NAME', value: env.PASSIVE_SITE),
                            string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                            string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                            booleanParam(name: 'SKIP_VMVNFM_LOGS_COLLECTION', value: true),
                        ]
                    }
                }
            }
        }
    }
}
