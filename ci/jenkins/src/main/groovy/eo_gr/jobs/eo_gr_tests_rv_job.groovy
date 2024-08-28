import eo_gr.defaults.Defaults


for ( def jobType : ['', '-debug'])
{
    def jobTitle = Defaults.DEFAULT_PREFIX + "-tests-rv${jobType}-job"
    def isJobNameContainsDebug = jobType.contains('-debug')
    def isJobNameContainsRv = jobType.contains('-rv')
    freeStyleJob("${jobTitle}") {
        description Defaults.description(
            "This is job to execute EO GR tests on environments with RV EO GR setup.",
            "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
        )

        label Defaults.DOCKER_SLAVE_LABEL_FEM_5
        logRotator(7)
        concurrentBuild()

        parameters {
            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
            choiceParam('ACTIVE_SITE', Defaults.rv_env_list, 'Select an ACTIVE SITE (environment) to use. For selected option, a config file should be present in config/envs folder in the repo. Eg: env_prod1.yaml file is present for value prod1')
            choiceParam('PASSIVE_SITE', Defaults.rv_env_list_passive_site_default, 'Select an PASSIVE SITE (environment) to use. For selected option, a config file should be present in config/envs folder in the repo. Eg: env_prod1.yaml file is present for value prod1')
            choiceParam('VIM', Defaults.vim_list, 'Select a vim to use. For selected option, a config file should be present in config/vims folder in the repo. Eg: vim_mycloud12A-test.yaml file is present for mycloud12A-test')
            booleanParam('USE_LOCAL_DNS', true, "If checked job runs with local DNS server settings, otherwise global DNS will be used. Make sure local DNS Server is up for environment.")

            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.TEST_PARAMETERS))
            stringParam('TEST_TAG', '', Defaults.TEST_TAG_DESCRIPTION_WITH_PYTEST_INI_LINK)
            stringParam('GR_STAGE_SHARED_NAME', "default-name", 'Provide unique name for VMVNFM or CVNFM tests. This needed to create or get openstack assets (VMVNFM) or CVNFM assets.')

            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
            stringParam('GERRIT_BRANCH', Defaults.DEFAULT_BRANCH, 'Please specify branch for execution.')
            stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', "Please use for running from commit, example 'refs/changes/43/7079843/1'")

            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
            stringParam('DEPLOYMENT_MANAGER_VERSION', "", "OPTIONAL. Provide numeric DM version otherwise DM version will be obtained from workdir.")
            booleanParam('COLLECT_SWITCHOVER_LOGS', false, "true if collect switchover logs required else false")
            booleanParam('EO_LOG_COLLECTION', true, 'true if needed to collect EO applications logs and attache it to current job from both sites')
            stringParam('LOG_PREFIX', "", "OPTIONAL. Add prefix to log name: '{LOG_PREFIX}_{ENV_NAME}_{ORIGINAL_LOG_NAME}'. Used in post-build actions.")
            booleanParam('ADDITIONAL_PARAM_FOR_CHANGE_PKG', true, 'true if additional parameters for CNF package needed else false')
            booleanParam('RESOURCES_CLEAN_UP', false, 'true if last stage should do clean up else false')
            booleanParam('PRETTY_API_LOGS', false, 'true if API logs needed to be output in pretty format else false')
            booleanParam('EO_VERSIONS_COLLECTION', true, 'true if needed to collect EO applications versions from provided ACTIVE_SITE and add them to pytest-report else false')
            booleanParam('ENABLE_VMVNFM_DEBUG_LOG_LEVEL', false, 'true if needed to set debug log level for VMVNFM. By default INFO level is used. NOTE: changing of logging level may take some time, which may increase the total time of the job execution.')
            choiceParam('DM_LOG_LEVEL', Defaults.dm_log_levels, 'Provide log level for deployment manager logger. By default INFO level will used')
            if (isJobNameContainsDebug) {
                booleanParam('RANDOMIZE_VNFD', false, 'true if randomize vnfd needed else false. Please use this option only in case of debugging')
            }
            stringParam('OVERRIDE', '', '''Optional parameter. Overriding parameters specified in config folder.
            Basic rules for parameters override:
                - The parameters should be separated by # symbol:
                    Eg: OPENSTACK_CLIENT_HOST=0000.0000.0000.0000#OPENSTACK_CLIENT_USERNAME=test
                - The config/artifacts.yaml has nested structure and parameters path should be separated by | symbol::
                    Eg: artefacts|spider_app_multi_a|package_path=package.csar#artefacts|spider_app_multi_a|cnf_descriptor_id=CNF-124863124''')
            stringParam('JOB_TIMEOUT', Defaults.JOB_TIMEOUT, 'Fail the build after exceeding the specified timeout')
        }

        wrappers {
            preBuildCleanup()
            timestamps()
            buildName('#${BUILD_NUMBER}_${PROJECT_NAME}_${ACTIVE_SITE}_${TEST_TAG}')
            credentialsBinding {
                file('DOCKER_AUTH_CONFIG', Defaults.DOCKER_SECRET_AUTH_CONFIG)
            }
            timeout {
                absolute('${JOB_TIMEOUT}')
                failBuild()
                writeDescription('The build was automatically failed as its execution time exceeded ${JOB_TIMEOUT} minutes')
            }
            environmentVariables {
                env('GIT_REPO', Defaults.TEST_FRAMEWORK_GIT_REPO)
                env('TEST_REPORT_DIR', Defaults.TEST_REPORT_DIR)
                env('TEST_REPORT_NAME', Defaults.TEST_REPORT_NAME)
                env('TEST_REPORT_TEMPLATE', Defaults.TEST_REPORT_TEMPLATE)
                env('TEST_DOCKER_IMAGE', Defaults.TEST_DOCKER_IMAGE + ':${GERRIT_BRANCH}')
                env('RV_SETUP', true)
                env('DOCKER_CONFIG_JSON', Defaults.DOCKER_CONFIG_JSON)
            }
        }

        scm {
            git {
                remote {
                    url(Defaults.TEST_FRAMEWORK_GIT_REPO)
                    credentials()
                }
                branch(GERRIT_BRANCH)
            }
        }

        steps {
            shell(Defaults.pullFromCommitShellCommand)

            // install docker config with permissions to the new DOCKER_CONFIG_JSON location
            shell(Defaults.install_docker_config_json())

            shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}'))

            shell(Defaults.defineDnsIpAndDnsFlagEnvVars('${TEST_DOCKER_IMAGE}', '${ACTIVE_SITE}')) // --> DNS_FLAG, DNS_SERVER_IP
            environmentVariables { propertiesFile(Defaults.ENV_PROPERTY_FILE) }

            shell('''
            echo "Setup post build task that should be executed depends on provided conditions."
            if [ "${EO_LOG_COLLECTION}" = true ]; then
                echo "Task: collect EO and VNFM logs"  # this text is needed for post-install task run. Do not rename or delete
            fi

            if [ "${COLLECT_SWITCHOVER_LOGS}" = true ]; then

                echo "Task: collect switchover logs"  # this text is needed for post-install task run. Do not rename or delete

                echo -e "\n-------- Clean up EO Node log folder before switchover --------\n"
                docker run --init --rm -v \$(pwd):/workdir --workdir /workdir/ -v /var/run/docker.sock:/var/run/docker.sock \
                    --env ACTIVE_SITE=${ACTIVE_SITE} \
                    --env PASSIVE_SITE=${PASSIVE_SITE} \
                    --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
                    --env PYTHONPATH=/workdir \
                    ${TEST_DOCKER_IMAGE} \
                    /bin/bash -c "source venv/bin/activate && python util_scripts/logging_scripts/collect_switchover_logs.py --pre-install"
            fi
            ''')

            shell('''
            echo -e "\n-------- Run tests --------\n"
            echo "TEST_TAG --> ${TEST_TAG}"
            echo "Workspace Folder --> ${WORKSPACE}"
            echo "ADDITIONAL_PARAM_FOR_CHANGE_PKG --> ${ADDITIONAL_PARAM_FOR_CHANGE_PKG}"
            echo "RESOURCES_CLEAN_UP --> ${RESOURCES_CLEAN_UP}"
            echo "GR_STAGE_SHARED_NAME --> ${GR_STAGE_SHARED_NAME}"
            echo "DEPLOYMENT_MANAGER_VERSION --> ${DEPLOYMENT_MANAGER_VERSION}"
            echo "GR_STAGE_SHARED_NAME --> ${GR_STAGE_SHARED_NAME}"
            echo "DM_LOG_LEVEL --> ${DM_LOG_LEVEL}"
            echo "ENABLE_VMVNFM_DEBUG_LOG_LEVEL --> ${ENABLE_VMVNFM_DEBUG_LOG_LEVEL}"
            echo "GR Test Report Dir --> ${WORKSPACE}/${TEST_REPORT_DIR}"
            echo "Docker image that is used --> ${TEST_DOCKER_IMAGE}"
            echo "RV_SETUP --> ${RV_SETUP}"

            echo -e "\n-------- Starting Test(s) execution in docker container with mark ${TEST_TAG} --------\n"

            docker run --init --rm -v \$(pwd):/workdir --workdir /workdir/ -v /var/run/docker.sock:/var/run/docker.sock \
                 $DNS_FLAG \
                   --env ACTIVE_SITE \
                   --env PASSIVE_SITE \
                   --env VIM \
                   --env ADDITIONAL_PARAM_FOR_CHANGE_PKG \
                   --env RESOURCES_CLEAN_UP \
                   --env GR_STAGE_SHARED_NAME \
                   --env PRETTY_API_LOGS \
                   --env RANDOMIZE_VNFD \
                   --env EO_VERSIONS_COLLECTION \
                   --env OVERRIDE \
                   --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
                   --env RV_SETUP \
                   --env DEPLOYMENT_MANAGER_VERSION \
                   --env DM_LOG_LEVEL \
                   --env ENABLE_VMVNFM_DEBUG_LOG_LEVEL \
                   --env DNS_SERVER_IP \
                   ${TEST_DOCKER_IMAGE} \
                   /bin/bash -c \
                        "source venv/bin/activate && \
                         pytest -m ${TEST_TAG} \
                            --log-cli-level=DEBUG \
                            --template=${TEST_REPORT_TEMPLATE} \
                            --report=${TEST_REPORT_DIR}/${TEST_REPORT_NAME}"
            ''')
        }

        publishers {
            publishHtml {
                report('${TEST_REPORT_DIR}') {
                    reportName('GR Test Report')
                    reportFiles('${TEST_REPORT_NAME}')
                    keepAll()
                    allowMissing(false)
                    alwaysLinkToLastBuild(false)
                }
            }

            postBuildTask {
                task('Task: collect switchover logs', '''
                echo -e "\n-------- Download logs from EO Node--------\n"
                echo "COLLECT_SWITCHOVER_LOGS --> ${COLLECT_SWITCHOVER_LOGS}"
                echo "RV_SETUP --> ${RV_SETUP}"
                if [ "${COLLECT_SWITCHOVER_LOGS}" = true ]; then
                    docker run --init --rm -v \$(pwd):/workdir --workdir /workdir/ -v /var/run/docker.sock:/var/run/docker.sock \
                        --env ACTIVE_SITE=${ACTIVE_SITE} \
                        --env PASSIVE_SITE=${PASSIVE_SITE} \
                        --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
                        --env PYTHONPATH=/workdir \
                        ${TEST_DOCKER_IMAGE} \
                        /bin/bash -c "source venv/bin/activate && python util_scripts/logging_scripts/collect_switchover_logs.py --post-install"
                fi
            ''')
            task('Task: collect EO and VNFM logs', '''
                echo -e "\n-------- Download logs from EO Node--------\n"
                echo "EO_LOG_COLLECTION --> ${EO_LOG_COLLECTION}"
                echo "RV_SETUP --> ${RV_SETUP}"
                if [ "${EO_LOG_COLLECTION}" = true ]; then
                    if [ -z "$LOG_PREFIX" ]; then
                        LOG_PREFIX=${TEST_TAG}
                    fi
                    docker run --init --rm -v \$(pwd):/workdir --workdir /workdir/ -v /var/run/docker.sock:/var/run/docker.sock \
                        --env ACTIVE_SITE=${ACTIVE_SITE} \
                        --env PASSIVE_SITE=${PASSIVE_SITE} \
                        --env LOG_PREFIX=${LOG_PREFIX} \
                        --env DEPLOYMENT_MANAGER_VERSION=${DEPLOYMENT_MANAGER_VERSION} \
                        --env PYTHONPATH=/workdir \
                        ${TEST_DOCKER_IMAGE} \
                        /bin/bash -c "source venv/bin/activate && python util_scripts/logging_scripts/collect_logs_script.py"
                fi
            ''')
            }

            archiveArtifacts {
                pattern('${TEST_REPORT_DIR}/*.*,downloaded_logs/**')
                allowEmpty(true)
                onlyIfSuccessful(false)
            }
        }
    }
}
