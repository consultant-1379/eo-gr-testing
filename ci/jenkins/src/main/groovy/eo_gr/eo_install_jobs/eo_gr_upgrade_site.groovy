import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-upgrade-site-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description(
    """This job upgrades one site of EO GR setup at a time""",
    "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(50, 50)
    concurrentBuild(true)

        parameters {
            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
            choiceParam('ENV', Defaults.rv_env_list, 'Choose environment you want to install')
            choiceParam('CLUSTER_ROLE', Defaults.cluster_roles, 'Choose a role for the environment you have selected in the ENV parameter')
            choiceParam('NEIGHBOR_ENV', Defaults.rv_env_list_passive_site_default, 'Choose a neighbor environment')
            stringParam('EO_VERSION', '', 'Provide with the version of packages should be installed (e.g. 2.7.0-310)')
            stringParam('DEPLOYMENT_MANAGER_VERSION', "", "OPTIONAL. Please provide a numeric DM version, otherwise DM version will be obtained from the workdir")
            booleanParam('ENABLE_VM_VNFM_HA', true, 'Check to enable VM VNFM HA. Available starting from helmfile 2.22.x')
            booleanParam('ENABLE_GR', true, 'Check to enable GR during EVNFM installation')
            booleanParam('DELETE_PACKAGES_AFTER_INSTALL', false, 'Check to delete EO packages after install')
            stringParam('NAMESPACE', '', 'Provide for specific needs only.')
            stringParam('HELM_TIMEOUT', '2400', 'Provide the EO upgrade timeout in seconds. The default value is 2400 seconds')
            stringParam('JOB_TIMEOUT', Defaults.JOB_TIMEOUT, 'Fail the build after exceeding the specified timeout which is set in minutes')
            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
            stringParam('GERRIT_BRANCH', Defaults.DEFAULT_BRANCH, 'eo-gr-testing repository branch')
            stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'refs to run from eo-gr-testing repository commit')
            stringParam('GERRIT_BRANCH_EO_INSTALL', Defaults.DEFAULT_BRANCH, 'eo-install repository branch')
            stringParam('GERRIT_REFSPEC_EO_INSTALL', '', 'refs to run from eo-install repository commit')

            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
            booleanParam('POST_BUILD_STEPS', true, 'true if need to run post build steps: Collecting EO upgrade logs and Setting debug log level for BUR Orchestrator')
        }


    wrappers {
        buildName('#${BUILD_NUMBER}_upgrade_${ENV}_to_${EO_VERSION}')
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
        envs([
            'EO_VERSION': '${EO_VERSION}',
            'TEST_DOCKER_IMAGE': Defaults.TEST_DOCKER_IMAGE + ':${GERRIT_BRANCH}',
            'DOCKER_CONFIG_JSON': Defaults.DOCKER_CONFIG_JSON, // change default DOCKER_CONFIG location
            'DOCKERFILE_PATH': Defaults.DOCKERFILE_PATH,
            'LOG_LEVEL': 'DEBUG',
            'PYTHON_PATH': Defaults.PYTHON_PATH,
            'GIT_REPO': Defaults.TEST_FRAMEWORK_GIT_REPO,
            'EO_INSTALL': Defaults.EO_INSTALL,
            'UPGRADE_EVNFM': true,
            'CONTROLLER_ENV': 'eo_node_ie',
            'ASSERT_UPGRADE_TIME': false,
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

        shell(Defaults.clean_up_dm_logs_from_eo_node('${TEST_DOCKER_IMAGE}'))

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}', '${EO_INSTALL}'))

        shell('''
        echo "POST_BUILD_STEPS -> ${POST_BUILD_STEPS}"

        if [ "${POST_BUILD_STEPS}" == true ]; then
            # following needed for post-build task run. Do not rename or delete!
            echo "Post build steps are ENABLED"
            echo "Collection of DM upgrade logs will be done in the post build steps"
            echo "Setting up debug log level for BUR Orchestrator will be done in the post build steps if the build is successful"
        fi

        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock \
            --env ENV=${ENV} \
            --env EO_VERSION="${EO_VERSION}#${DEPLOYMENT_MANAGER_VERSION}" \
            --env ENABLE_VM_VNFM_HA=${ENABLE_VM_VNFM_HA} \
            --env HELM_TIMEOUT=${HELM_TIMEOUT} \
            --env ENABLE_GR=${ENABLE_GR} \
            --env DELETE_PACKAGES_AFTER_INSTALL=${DELETE_PACKAGES_AFTER_INSTALL} \
            --env CLUSTER_ROLE=${CLUSTER_ROLE} \
            --env NEIGHBOR_ENV=${NEIGHBOR_ENV} \
            --env GLOBAL_REGISTRY=${GLOBAL_REGISTRY} \
            --env NAMESPACE=${NAMESPACE} \
            --env LOG_LEVEL=${LOG_LEVEL} \
            --env GIT_REPO=${GIT_REPO} \
            --env CONTROLLER_ENV=${CONTROLLER_ENV} \
            --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
            --env PYTHONPATH=/workdir/${EO_INSTALL} \
            --env UPGRADE_EVNFM=${UPGRADE_EVNFM} \
            --env ASSERT_UPGRADE_TIME=${ASSERT_UPGRADE_TIME} \
            ${TEST_DOCKER_IMAGE} \
            /bin/bash -c "cd ${EO_INSTALL} && source venv/bin/activate && python eo_install/main.py"
        ''')
    }

    publishers {
        postBuildTask {
            task('Collection of DM upgrade logs', Defaults.collect_dm_logs_from_eo_node('${TEST_DOCKER_IMAGE}'))
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
