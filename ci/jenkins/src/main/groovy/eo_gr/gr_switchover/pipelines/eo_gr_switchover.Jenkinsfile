#!/usr/bin/env groovy

/* IMPORTANT:
 *
 * In order to make this pipeline work, the following configuration on Jenkins is required:
 * - slave with a specific label (see pipeline.agent.label below)
 * - Credentials Plugin should be installed and have the secrets with the following names:
 *   + c12a011-config-file (admin.config to access c12a011 cluster)
 */

// DSL script ci/jenkins/src/main/groovy/eo_gr/pipeline_jobs/eo_gr_switchover_job.groovy

def bob = "bob/bob -r \${WORKSPACE}/rulesets/rulesets2.0_switchover.yaml"
def RETRY_ATTEMPT = 1


pipeline {
    agent {
        node {
            label env.SLAVE_LABEL
        }
    }
    options {
          timeout(time: 3, unit: 'HOURS')
      }

    environment {
        USE_TAGS = 'true'
        STATE_VALUES_FILE = "site_values_${params.INT_CHART_VERSION}.yaml"
        CSAR_STORAGE_URL = get_csar_storage_url("${params.CI_DOCKER_IMAGE}")
        CSAR_STORAGE_API_URL = get_csar_storage_api_url("${params.CI_DOCKER_IMAGE}")
        PATH_TO_HELMFILE = "${params.INT_CHART_NAME}/helmfile.yaml"
        CSAR_STORAGE_INSTANCE = 'arm.seli.gic.ericsson.se'
        CSAR_STORAGE_REPO = 'proj-eric-oss-drop-generic-local'
        FETCH_CHARTS = 'true'
        HELMFILE_CHART_NAME = "${params.INT_CHART_NAME}"
        HELMFILE_CHART_VERSION = "${params.INT_CHART_VERSION}"
        HELMFILE_CHART_REPO = "${params.INT_CHART_REPO}"
        DOCKER_CONFIG = "${env.WORKSPACE}/.docker"
        JENKINS_USER_AGENT_HOME = store_jenkins_user_agent_home()
        HOME = "${env.WORKSPACE}"
        ACTIVE_SITE = "${env.ACTIVE_SITE}"
        PYTEST_REPORT_DIR = 'pytest_reports'
        PYTEST_REPORT_NAME = 'report.html'
    }
    stages {
        stage('Set build name') {
            steps {
                script {
                    currentBuild.displayName = "${env.BUILD_NUMBER} ${env.ACTIVE_SITE} -> ${env.PASSIVE_SITE}".toLowerCase()
                }
            }
        }
         stage('Clone eo-gr-testing repository') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: env.GERRIT_BRANCH]],
                    userRemoteConfigs: [[
                        url: '${GERRIT_CENTRAL_HTTP}/OSS/EO-Parent/com.ericsson.oss.orchestration.eo.testware/eo-gr-testing',
                        credentialsId: "eoadm100-user-credentials"
                    ]]
                ])
            }}
        stage('Prepare') {
            environment {
                HOME = "${env.JENKINS_USER_AGENT_HOME}"
            }
            steps {
                retry(count: 5){
                    script{
                        if (RETRY_ATTEMPT > 1) {
                            echo "Rerunning the \"Prepare\" stage. Retry ${RETRY_ATTEMPT} of 5. Sleeping before retry..."
                            sleep(180)
                        }
                        else {
                            echo "Running the \"Prepare\" stage. Try ${RETRY_ATTEMPT} of 5"
                        }
                        RETRY_ATTEMPT = RETRY_ATTEMPT + 1

                        if (env.GERRIT_REFSPEC != "refs/heads/master" && env.GERRIT_REFSPEC) {
                            echo "Installing git changes from provided refspec: '${GERRIT_REFSPEC}'"
                            sh 'git fetch origin ${GERRIT_REFSPEC} && git checkout FETCH_HEAD'
                        }

                        sh "git submodule update --init --recursive --remote --depth=1 bob oss-integration-ci"
                        sh "${bob} git-clean"

                        RETRY_ATTEMPT = 1
                    }
                }
            }
        }
        stage('Install Docker Config') {
            steps {
                script {
                    // replace :default tag of provided image to actual VERSION_PREFIX value from oss-integration-ci repo
                    env.CI_DOCKER_IMAGE = get_ci_docker_image_url("${params.CI_DOCKER_IMAGE}")
                    echo "New value for CI_DOCKER_IMAGE: $CI_DOCKER_IMAGE"

                    // install docker config in workdir
                    withCredentials([file(credentialsId: params.ARMDOCKER_USER_SECRET, variable: 'DOCKERCONFIG')]) {
                        sh 'install -m 600 -D ${DOCKERCONFIG} ${DOCKER_CONFIG}/config.json'
                    }
                }
            }
        }
        stage('Get Helmfile') {
            steps {
                retry(count: 5){
                    script{
                        if (RETRY_ATTEMPT > 1) {
                            echo "Rerunning the \"Get Helmfile\" stage. Retry ${RETRY_ATTEMPT} of 5. Sleeping before retry..."
                            sleep(180)
                        }
                        else {
                            echo "Running the \"Get Helmfile\" stage. Try ${RETRY_ATTEMPT} of 5"
                        }
                        RETRY_ATTEMPT = RETRY_ATTEMPT + 1

                        if(params.FUNCTIONAL_USER_TOKEN.trim().toUpperCase() == "NONE" || params.FUNCTIONAL_USER_TOKEN.isEmpty()){
                            withCredentials([usernamePassword(credentialsId: params.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME', passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                                sh "${bob} helmfile:fetch-helmfile"
                            }
                        }else{
                            withCredentials([string(credentialsId: params.FUNCTIONAL_USER_TOKEN, variable: 'FUNCTIONAL_USER_TOKEN')]) {
                                sh "${bob} helmfile:fetch-helmfile-using-token"
                            }
                        }
                        RETRY_ATTEMPT = 1
                    }
                }
            }
        }
        stage('Set Deployment Manager Version') {
            steps {
                retry(count: 5){
                    script{
                        if (RETRY_ATTEMPT > 1) {
                            echo "Rerunning the \"Set Deployment Manager Version\" stage. Retry ${RETRY_ATTEMPT} of 5. Sleeping before retry..."
                            sleep(180)
                        }
                        else {
                            echo "Running the \"Set Deployment Manager Version\" stage. Try ${RETRY_ATTEMPT} of 5"
                        }
                        RETRY_ATTEMPT = RETRY_ATTEMPT + 1

                        sh "${bob} helmfile:extract-helmfile helmfile:get-dm-full-url-version"

                        RETRY_ATTEMPT = 1

                        env.DEPLOYMENT_MANAGER_DOCKER_IMAGE = sh (
                            script: "cat IMAGE_DETAILS.txt | grep ^IMAGE | sed 's/.*=//'",
                            returnStdout: true
                        ).trim()
                    }
                }
            }
        }
        stage('Prepare Working Directory') {
            steps {
                sh "${bob} untar-and-copy-helmfile-to-workdir fetch-site-values"
            }
        }
        stage('Update Global Registry within Site Values') {
            when {
                anyOf {
                    environment ignoreCase: true, name: 'DOCKER_REGISTRY', value: 'armdocker.rnd.ericsson.se'
                    allOf {
                        not {
                            environment ignoreCase: true, name: 'DOCKER_REGISTRY', value: 'armdocker.rnd.ericsson.se'
                        }
                        environment ignoreCase: true, name: 'FLOW_AREA', value: 'eiapaas'
                    }
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: params.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME', passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                    sh "${bob} update-site-values-registry:substitute-global-registry-details"
                }
            }
        }
        stage('Update local Registry within Site Values') {
            when {
                allOf {
                    not {
                        environment ignoreCase: true, name: 'DOCKER_REGISTRY', value: 'armdocker.rnd.ericsson.se'
                    }
                    not {
                        environment ignoreCase: true, name: 'FLOW_AREA', value: 'eiapaas'
                    }
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: params.DOCKER_REGISTRY_CREDENTIALS, usernameVariable: 'DOCKER_REGISTRY_USERNAME', passwordVariable: 'DOCKER_REGISTRY_PASSWORD')]) {
                    sh "${bob} update-site-values-registry:substitute-local-registry-details"
                }
            }
        }
        stage('Update Site Values') {
            steps {
                retry(count: 5){
                    script{
                        if (RETRY_ATTEMPT > 1) {
                            echo "Rerunning the \"Update Site Values'\" stage. Retry ${RETRY_ATTEMPT} of 5. Sleeping before retry..."
                            sleep(180)
                        }
                        else {
                            echo "Running the \"Update Site Values'\" stage. Try ${RETRY_ATTEMPT} of 5"
                        }
                        RETRY_ATTEMPT = RETRY_ATTEMPT + 1

                        withCredentials([usernamePassword(credentialsId: params.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME', passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                            sh "${bob} update-site-values:substitute-ipv6-enable"
                            sh "${bob} update-site-values:substitute-application-hosts"
                            sh "${bob} update-site-values:substitute-application-deployment-option"
                            sh "${bob} update-site-values:substitute-application-service-option"
                            sh "${bob} update-repositories-file"
                            RETRY_ATTEMPT = 1
                        }
                    }
                }
            }
        }
        stage('Build CSARs') {
            when {
                environment ignoreCase: true, name: 'DOWNLOAD_CSARS', value: 'false'
            }
            steps {
                retry(count: 5){
                    script{
                        if (RETRY_ATTEMPT > 1) {
                            echo "Rerunning the \"Build CSARs\" stage. Retry ${RETRY_ATTEMPT} of 5. Sleeping before retry..."
                            sleep(180)
                        }
                        else {
                            echo "Running the \"Build CSARs\" stage. Try ${RETRY_ATTEMPT} of 5"
                        }
                        RETRY_ATTEMPT = RETRY_ATTEMPT + 1

                        withCredentials([usernamePassword(credentialsId: params.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME', passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                            sh "${bob} get-release-details-from-helmfile"
                            sh "${bob} helmfile-charts-mini-csar-build"
                            sh "${bob} cleanup-charts-mini-csar-build"
                        }
                        RETRY_ATTEMPT = 1
                    }
                }
            }
        }
        stage('Download CSARs') {
            when {
                environment ignoreCase: true, name: 'DOWNLOAD_CSARS', value: 'true'
            }
            steps {
                withCredentials([usernamePassword(credentialsId: params.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME', passwordVariable: 'FUNCTIONAL_USER_PASSWORD'), file(credentialsId: params.KUBECONFIG_FILE, variable: 'KUBECONFIG')]) {
                    sh "${bob} get-app-details-from-helmfile"
                    sh "${bob} check-for-existing-csar-in-repo"
                    sh "${bob} download-csar-to-workspace"
                }
            }
        }
        stage('Pre Deployment Manager Configuration') {
            stages {
                stage('Deployment Manager Init') {
                    steps {
                        retry(count: 5){
                            script {
                                if (RETRY_ATTEMPT > 1) {
                                    echo "Rerunning the \"Deployment Manager Init'\" stage. Retry ${RETRY_ATTEMPT} of 5. Sleeping before retry..."
                                    sleep(180)
                                }
                                else {
                                    echo "Running the \"Deployment Manager Init'\" stage. Try ${RETRY_ATTEMPT} of 5"
                                }

                                RETRY_ATTEMPT = RETRY_ATTEMPT + 1

                                sh "${bob} deployment-manager-init:deployment-manager-init"

                                RETRY_ATTEMPT = 1
                            }
                        }
                    }
                }
                stage ('Copy Certs and Kube Config') {
                    steps {
                        withCredentials([file(credentialsId: params.KUBECONFIG_FILE, variable: 'KUBECONFIG')]) {
                            sh "${bob} copy-certificate-files"
                            sh 'install -m 600 ${KUBECONFIG} ./kube_config/config'
                        }
                    }
                }
                stage('Prepare Site Values using DM') {
                    when {
                        environment ignoreCase: true, name: 'USE_DM_PREPARE', value: 'true'
                    }
                    steps {
                        retry(count: 5){
                            script{
                                if (RETRY_ATTEMPT > 1) {
                                    if (fileExists('ci-script-executor-logs/ERROR_merge_yaml_files.properties')) {
                                        error("Stage \"Prepare Site Values using DM\" failed.")
                                        return
                                    }
                                    echo "Rerunning the \"Prepare Site Values using DM'\" stage. Retry ${RETRY_ATTEMPT} of 5. Sleeping before retry..."
                                    sleep(180)
                                }
                                else {
                                    echo "Running the \"Prepare Site Values using DM'\" stage. Try ${RETRY_ATTEMPT} of 5"
                                }
                                RETRY_ATTEMPT = RETRY_ATTEMPT + 1

                                sh "${bob} prepare-site-values:rename-ci-site-values"

                                sh "${bob} prepare-site-values:deployment-manager-prepare"

                                sh "${bob} prepare-site-values:populate-prepare-dm-site-values"
                                RETRY_ATTEMPT = 1
                            }
                        }
                    }
                }
            }
            post {
                failure {
                    archiveArtifacts allowEmptyArchive: true, artifacts: "logs/*", fingerprint: true
                }
            }
        }
        stage('Override Site Values') {
            when {
                not {
                    environment ignoreCase: true, name: 'PATH_TO_SITE_VALUES_OVERRIDE_FILE', value: 'NONE'
                }
            }
            steps {
                sh "${bob} override-site-values:override-site-values"
            }
        }
        stage('Update Site Values after Override') {
            steps {
                withCredentials([usernamePassword(credentialsId: params.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME', passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                    sh "${bob} update-site-values:substitute-ipv6-enable"
                    sh "${bob} update-site-values:substitute-application-hosts"
                    sh "${bob} update-site-values:substitute-application-deployment-option"
                    sh "${bob} update-site-values:substitute-application-service-option"
                }
            }
        }
        stage('Update Site Values using key values from the environment configuration file') {
            steps {
                withCredentials([usernamePassword(credentialsId: params.FUNCTIONAL_USER_SECRET, usernameVariable: 'FUNCTIONAL_USER_USERNAME', passwordVariable: 'FUNCTIONAL_USER_PASSWORD')]) {
                    sh "${bob} update-site-values:substitute-values-from-env-file"
                }
            }
        }
        stage('Install EO-GR testing Python dependencies') {
            steps {
                sh "${bob} eo-gr-testing:create-venv-and-install-dependencies"
            }
        }
        stage('Run Switchover') {
            steps {
                script {
                    if ("${env.SWITCHOVER_RULE}" == "run-switchover-while-active-site-unavailable") {
                        sh "${bob} eo-gr-testing:run-switchover-while-active-site-unavailable"
                    } else if ("${env.SWITCHOVER_RULE}" == "run-switchover-after-active-site-become-available") {
                        sh "${bob} eo-gr-testing:run-switchover-after-active-site-become-available"
                    } else {
                        sh "${bob} eo-gr-testing:run-switchover"
                    }
                }
            }
        }
    }
    post {
        always {
            script {
                if (getContext(hudson.FilePath)) {
                    archiveArtifacts allowEmptyArchive: true, artifacts: "artifact.properties, logs_*.tgz, logs/*, ${env.STATE_VALUES_FILE}, ${PYTEST_REPORT_DIR}/*", fingerprint: true
                    publishHTML target :[
                        allowMissing: false,
                        keepAll: true,
                        alwaysLinkToLastBuild: false,
                        reportDir: "${PYTEST_REPORT_DIR}",
                        reportFiles: "${PYTEST_REPORT_NAME}",
                        reportName: 'GR Test Report',
                    ]
                }
            }
        }
        failure {
            script {
                if (getContext(hudson.FilePath)) {
                    sh "printenv | sort"
                    archiveArtifacts artifacts: "ci-script-executor-logs/*", allowEmptyArchive: true, fingerprint: true
                }
            }
        }
        cleanup {
            script {
                if (env.CLEAN_UP_WORKDIR == 'true') {
                    cleanWs()
                }
            }
        }
    }
}

def get_csar_storage_url(ci_docker_image) {
    if (!(ci_docker_image.contains("proj-eric-oss-dev"))) {
        return "https://arm.seli.gic.ericsson.se/artifactory/proj-eric-oss-drop-generic-local/csars/";
    }
    return "https://arm.seli.gic.ericsson.se/artifactory/proj-eric-oss-drop-generic-local/eric-ci-helmfile/csars/";
}

def get_csar_storage_api_url(ci_docker_image) {
    if (!(ci_docker_image.contains("proj-eric-oss-dev"))) {
        return "https://arm.seli.gic.ericsson.se/artifactory/api/storage/proj-eric-oss-drop-generic-local/csars/";
    }
    return "https://arm.seli.gic.ericsson.se/artifactory/api/storage/proj-eric-oss-drop-generic-local/eric-ci-helmfile/csars/";
}

def get_ci_docker_image_url(ci_docker_image) {
    if (ci_docker_image.contains("default")) {
        String latest_ci_version = readFile "oss-integration-ci/VERSION_PREFIX"
        String trimmed_ci_version = latest_ci_version.trim()
        url = ci_docker_image.split(':');
        return url[0] + ":" + trimmed_ci_version;
    }
    return ci_docker_image
}

def store_jenkins_user_agent_home() {
    String value_storage = env.HOME
    return value_storage
}
