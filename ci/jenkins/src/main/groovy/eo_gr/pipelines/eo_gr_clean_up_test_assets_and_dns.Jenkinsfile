#!/usr/bin/env groovy

/* DESCRIPTION:
 * This pipeline performs post-setup cleanup actions:
 * cleans up test assets on VIM
 * removes DNS container and cleans up dns data from cluster's configmap
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
        DELETE_ALL = "${DELETE_ALL}"
        GERRIT_BRANCH = "${env.GERRIT_BRANCH}"
        GERRIT_REFSPEC = "${env.GERRIT_REFSPEC}"
    }
    stages {
        stage('Set build name') {
            steps {
                script {
                    currentBuild.displayName = "${env.BUILD_NUMBER}_${env.ACTIVE_SITE}_${env.PASSIVE_SITE}_delete_all_${DELETE_ALL}"
                }
            }
        }
        stage('Cleanup VIM zone test assets') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-clean-up-vim-job',
                        parameters: [
                            string(name: 'VIM', value: env.VIM),
                            string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                            booleanParam(name: 'DELETE_ALL', value: env.DELETE_ALL),
                            string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                            string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        ]
                    }
                }
            }
        }
        stage('Cleanup CVNFM namespaces created by tests') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-delete-cnf-namespaces-job',
                        parameters: [
                            string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                            string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                            string(name: 'GR_STAGE_SHARED_NAME', value: env.GR_STAGE_SHARED_NAME),
                            booleanParam(name: 'DELETE_ALL', value: env.DELETE_ALL),
                            string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                            string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                        ]
                    }
                }
            }
        }
        stage('Removing and cleanup DNS') {
            steps {
                script {
                    build job: 'eo-gr-remove-dns-server-job',
                    parameters: [
                        string(name: 'ACTIVE_SITE', value: env.ACTIVE_SITE),
                        string(name: 'PASSIVE_SITE', value: env.PASSIVE_SITE),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                    ]
                }
            }
        }
    }
}