import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-collecting-logs-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description("""This job collects logs by Deployment Manager tool and get VM VMVNFM logs from service pod (only for 'Active' site).
    <br>Logs will be available in Build Artifacts.
    <br>NOTE: Available for RV Installed environment only!""",
    "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(50, 50)
    concurrentBuild(true)

    parameters {
        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
        choiceParam('SITE_NAME', Defaults.all_env_list, 'Select an Site (environment) for which needed to collect logs')
        choiceParam('ADDITIONAL_SITE_NAME', Defaults.all_env_list_empty_default, 'OPTIONAL. Select a second site (environment) for which needed to collect logs or leave it empty')

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
        stringParam('DEPLOYMENT_MANAGER_VERSION', "", "OPTIONAL. Provide numeric DM version otherwise DM version will be obtained from workdir.")
        stringParam('LOG_PREFIX', "", "OPTIONAL. Add prefix to log name: '{LOG_PREFIX}_{ENV_NAME}_{ORIGINAL_LOG_NAME}''")
        booleanParam('SKIP_VMVNFM_LOGS_COLLECTION', false, 'Check if needed to skip VMVNFM logs collection.')

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
        stringParam('GERRIT_BRANCH', Defaults.DEFAULT_BRANCH, 'Please specify branch for execution.')
        stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'Please use for running from commit, example: refs/changes/43/7079843/1')
    }

    wrappers {
        preBuildCleanup()
        timestamps()
        buildName('#${BUILD_NUMBER}_${PROJECT_NAME}_${SITE_NAME}')
        credentialsBinding {
            file('DOCKER_AUTH_CONFIG', Defaults.DOCKER_SECRET_AUTH_CONFIG)
        }
        timeout {
            absolute(Defaults.JOB_TIMEOUT)
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

    steps {
        environmentVariables {
            envs([
                'GIT_REPO': Defaults.TEST_FRAMEWORK_GIT_REPO,
                'TEST_DOCKER_IMAGE': Defaults.TEST_DOCKER_IMAGE + ':${GERRIT_BRANCH}',
                'DOCKER_CONFIG_JSON': Defaults.DOCKER_CONFIG_JSON, // change default DOCKER_CONFIG location
                ]
            )
        }

        shell(Defaults.pullFromCommitShellCommand)
        // install docker config with permissions to the new DOCKER_CONFIG_JSON location
        shell(Defaults.install_docker_config_json())

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}'))

        shell('''
        echo "DEPLOYMENT_MANAGER_VERSION --> ${DEPLOYMENT_MANAGER_VERSION}"
        echo "SKIP_VMVNFM_LOGS_COLLECTION --> ${SKIP_VMVNFM_LOGS_COLLECTION}"

        SKIP_VMVNFM_LOGS_COLLECTION=$( [ "${SKIP_VMVNFM_LOGS_COLLECTION}" == true ] && echo "--skip-vmvnfm-logs" || echo "" )

        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock \
                --env ACTIVE_SITE=${SITE_NAME} \
                --env PASSIVE_SITE=${ADDITIONAL_SITE_NAME} \
                --env DEPLOYMENT_MANAGER_VERSION \
                --env LOG_PREFIX \
                --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
                --env PYTHONPATH=/workdir \
                 ${TEST_DOCKER_IMAGE} \
                    /bin/bash -c "source venv/bin/activate && \
                     python util_scripts/logging_scripts/collect_logs_script.py $SKIP_VMVNFM_LOGS_COLLECTION"
        ''')
        shell ('echo "--------------- Logs should be available in Build Artifacts ---------------"')
    }

    publishers {
        archiveArtifacts {
                pattern('downloaded_logs/**')
                allowEmpty(true)
                onlyIfSuccessful(false)
        }
    }
}
