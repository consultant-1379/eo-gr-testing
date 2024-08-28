import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-install-site-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description("""This job install sites for EO GR setup. WARNING: manual job configuration might broke the post-build actions!""",
    "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(50, 50)
    concurrentBuild(true)

        parameters {
            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
            choiceParam('ENV', Defaults.rv_env_list, 'Choose environment you want to install')
            stringParam('EO_VERSION', '', 'Provide with the version of packages should be installed (e.g. 2.7.0-310#1.42.0-451)')
            booleanParam('ENABLE_VM_VNFM_HA', false, 'Check to enable VM VNFM HA. Available starting from helmfile 2.22.x')
            stringParam('HELM_TIMEOUT', '1800', 'Provide the EO installation timeout in seconds (e.g. 3600). The default value is 1800 seconds')
            booleanParam('ENABLE_GR', false, 'Check to enable GR during EVNFM installation')
            booleanParam('DELETE_PACKAGES_AFTER_INSTALL', false, 'Check to delete EO packages after install')
            choiceParam('CLUSTER_ROLE', ['PRIMARY', 'SECONDARY'], 'Choose role for your environment. User PRIMARY if ENV is Original ACTIVE, use SECONDARY if ENV is Original PASSIVE')
            choiceParam('NEIGHBOR_ENV', Defaults.rv_env_list_passive_site_default, 'Choose the neighbor environment')
            booleanParam('DOWNLOAD_PACKAGES', true, 'Use only when packages already present in the workdir!')
            stringParam('NAMESPACE', '', 'Provide for specific needs only.')
            booleanParam('INSTALL_VM_VNFM', true, 'Check to install VM VNFM')
            booleanParam('INSTALL_C_VNFM', true, 'Check to install CVNFM')
            stringParam('CONTROLLER_ENV', 'eo_node_ie', 'The controller VM used for installation')
            stringParam('JOB_TIMEOUT', Defaults.JOB_TIMEOUT, 'Fail the build after exceeding the specified timeout')

            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
            stringParam('GERRIT_BRANCH', 'master', 'eo-gr-testing repository branch')
            stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'refs to run from eo-gr-testing repository commit')
            stringParam('GERRIT_BRANCH_EO_INSTALL', Defaults.DEFAULT_BRANCH, 'eo-install repository branch')
            stringParam('GERRIT_REFSPEC_EO_INSTALL', '', 'refs to run from eo-install repository commit')

            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
            booleanParam('REMOVE_STUCK_VOLUMES', true, 'Enable it if all stuck VIM zone volumes should be removed before the EO installation')
            booleanParam('POST_BUILD_STEPS', true, 'true if need to run post build steps: Collection EO installation logs and Setting debug log level for BUR Orchestrator')
        }


    wrappers {
        buildName('#${BUILD_NUMBER}_install_${ENV}_version_${EO_VERSION}')
        preBuildCleanup()
        timestamps()
        credentialsBinding {
            file('DOCKER_AUTH_CONFIG', Defaults.DOCKER_SECRET_AUTH_CONFIG)
        }
        timeout {
            absolute('${JOB_TIMEOUT}')
            failBuild()
            writeDescription('The build was automatically failed as its execution time exceeded ${JOB_TIMEOUT} minutes')
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

    environmentVariables {
        envs(
            [
                'TEST_DOCKER_IMAGE': Defaults.TEST_DOCKER_IMAGE + ':${GERRIT_BRANCH}',
                'DOCKER_CONFIG_JSON': Defaults.DOCKER_CONFIG_JSON, // change default DOCKER_CONFIG location
                'DOCKERFILE_PATH': Defaults.DOCKERFILE_PATH,
                'LOG_LEVEL': 'DEBUG',
                'PYTHON_PATH' : Defaults.PYTHON_PATH,
                'GIT_REPO': Defaults.TEST_FRAMEWORK_GIT_REPO,
                'EO_INSTALL': Defaults.EO_INSTALL,
                'INSTALL_EVNFM': true,
            ]
        )
    }
    steps {
        shell(Defaults.pullFromCommitShellCommand)

        shell(Defaults.set_up_eo_install_submodule('${GERRIT_BRANCH_EO_INSTALL}', '${GERRIT_REFSPEC_EO_INSTALL}'))

        // install docker config with permissions to the new DOCKER_CONFIG_JSON location
        shell(Defaults.install_docker_config_json())

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}'))

        shell(Defaults.set_global_registry_env_var('${TEST_DOCKER_IMAGE}', '${ENV}'))  // GLOBAL_REGISTRY definition
        environmentVariables { propertiesFile(Defaults.ENV_PROPERTY_FILE) }

        shell(Defaults.remove_stuck_volumes('${REMOVE_STUCK_VOLUMES}', '${ENV}'))

        shell(Defaults.clean_up_dm_logs_from_eo_node('${TEST_DOCKER_IMAGE}'))

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}', '${EO_INSTALL}'))

        shell('''
        echo "POST_BUILD_STEPS -> ${POST_BUILD_STEPS}"

        if [ "${POST_BUILD_STEPS}" == true ]; then
            # following needed for post-build task run. Do not rename or delete!
            echo "Post build steps are ENABLED"
            echo "Collection of DM installation logs will be done in the post build steps"
            echo "Setting up debug log level for BUR Orchestrator will be done in the post build steps if the build is successful"
        fi

        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock \
            --env ENV=${ENV} \
            --env EO_VERSION=${EO_VERSION} \
            --env ENABLE_VM_VNFM_HA=${ENABLE_VM_VNFM_HA} \
            --env HELM_TIMEOUT=${HELM_TIMEOUT} \
            --env ENABLE_GR=${ENABLE_GR} \
            --env DELETE_PACKAGES_AFTER_INSTALL=${DELETE_PACKAGES_AFTER_INSTALL} \
            --env CLUSTER_ROLE=${CLUSTER_ROLE} \
            --env NEIGHBOR_ENV=${NEIGHBOR_ENV} \
            --env GLOBAL_REGISTRY=${GLOBAL_REGISTRY} \
            --env DOWNLOAD_PACKAGES=${DOWNLOAD_PACKAGES} \
            --env NAMESPACE=${NAMESPACE} \
            --env INSTALL_VM_VNFM=${INSTALL_VM_VNFM} \
            --env INSTALL_C_VNFM=${INSTALL_C_VNFM} \
            --env LOG_LEVEL=${LOG_LEVEL} \
            --env GIT_REPO=${GIT_REPO} \
            --env INSTALL_EVNFM=${INSTALL_EVNFM} \
            --env CONTROLLER_ENV=${CONTROLLER_ENV} \
            --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
            --env PYTHONPATH=/workdir/${EO_INSTALL} \
            ${TEST_DOCKER_IMAGE} \
            /bin/bash -c "cd ${EO_INSTALL} && source venv/bin/activate && python eo_install/main.py"
        ''')
    }

    publishers {
        postBuildTask {
            task('Collection of DM installation logs', Defaults.collect_dm_logs_from_eo_node('${TEST_DOCKER_IMAGE}'))
            task(
                'Setting up debug log level for BUR Orchestrator',
                Defaults.set_bur_orchestrator_log_level('${TEST_DOCKER_IMAGE}'),
                false, // escalate script execution status to job status
                true  // run script only if all previous steps were successful
            )
        }
        archiveArtifacts{
            pattern('${EO_INSTALL}/*.log,${EO_INSTALL}/site_values_*.yaml,downloaded_logs/*.*')
            allowEmpty(true)
            onlyIfSuccessful(false)
        }
    }
}
