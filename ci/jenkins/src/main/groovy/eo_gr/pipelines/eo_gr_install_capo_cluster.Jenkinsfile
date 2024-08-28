#!/usr/bin/env groovy

/* DESCRIPTION:
 * This pipeline performs cluster CAPO installation:
 *  - install K8s CAPO (Cluster API Provider OpenStack) cluster.
 *  - Update kubeconfig on the cluster's master nodes and on Artifactory.
 *  - Create network file storage class.
 */

pipeline {
    agent {
        label env.SLAVE_LABEL
    }
    environment {
        ENV = "${env.ENV}"
        CONTROLLER_ENV = "${env.CONTROLLER_ENV}"
        ECCD_LINK = "${env.ECCD_LINK}"
        MASTER_DIMENSIONS = "${env.MASTER_DIMENSIONS}"
        WORKER_DIMENSIONS = "${env.WORKER_DIMENSIONS}"
        GERRIT_BRANCH = "${env.GERRIT_BRANCH}"
        GERRIT_REFSPEC = "${env.GERRIT_REFSPEC}"
        GERRIT_BRANCH_EO_INSTALL = "${env.GERRIT_BRANCH_EO_INSTALL}"
        GERRIT_REFSPEC_EO_INSTALL = "${GERRIT_REFSPEC_EO_INSTALL}"
    }
    stages {
        stage('Set build name') {
            steps {
                script {
                    currentBuild.displayName = "${env.BUILD_NUMBER}_install_${env.ENV}"
                }
            }
        }
        stage('Install CAPO cluster') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        build job: 'eo-gr-install-cluster-job',
                        parameters: [
                            string(name: 'ENV', value: env.ENV),
                            string(name: 'CONTROLLER_ENV', value: env.CONTROLLER_ENV),
                            string(name: 'ECCD_LINK', value: env.ECCD_LINK),
                            string(name: 'MASTER_DIMENSIONS', value: env.MASTER_DIMENSIONS),
                            string(name: 'WORKER_DIMENSIONS', value: env.WORKER_DIMENSIONS),
                            string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                            string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                            string(name: 'GERRIT_BRANCH_EO_INSTALL', value: env.GERRIT_BRANCH_EO_INSTALL),
                            string(name: 'GERRIT_REFSPEC_EO_INSTALL', value: env.GERRIT_REFSPEC_EO_INSTALL),
                        ]
                    }
                }
            }
        }
        stage('Post-installation steps') {
            steps {
                script {
                    build job: 'eo-gr-post-cluster-installation-steps-job',
                    parameters: [
                        string(name: 'ENV', value: env.ENV),
                        string(name: 'GERRIT_BRANCH', value: env.GERRIT_BRANCH),
                        string(name: 'GERRIT_REFSPEC', value: env.GERRIT_REFSPEC),
                    ]
                }
            }
        }
    }
}