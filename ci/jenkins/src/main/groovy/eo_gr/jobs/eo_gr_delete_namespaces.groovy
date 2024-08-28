import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-delete-cnf-namespaces-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description(
        "This job contains script for delete cnf namespaces from cluster(s).",
        "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(50, 50)
    concurrentBuild(true)

    parameters {
        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
        choiceParam('ACTIVE_SITE', Defaults.all_env_list, 'Select a active environment to update.')
        choiceParam('PASSIVE_SITE', Defaults.all_env_list_empty_default, 'OPTIONAL. Select an additional environment to update.')

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
        booleanParam('DELETE_ALL', true, 'Check if needed to delete all CVNFM namespaces.<br>GR_STAGE_SHARED_NAME will be ignored if it checked.')
        stringParam('GR_STAGE_SHARED_NAME', 'default-name', 'OPTIONAL. Provide shared name to delete specific namespace from cluster(s). If empty then default name will be used.<br>Applicable only if DELETE_ALL is unchecked.')

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
        stringParam('GERRIT_BRANCH', Defaults.DEFAULT_BRANCH, 'Please specify branch for execution.')
        stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'Please use for running from commit, example: refs/changes/43/7079843/1')
    }

    wrappers {
        preBuildCleanup()
        timestamps()
        buildName('#${BUILD_NUMBER}_${PROJECT_NAME}_${ACTIVE_SITE}_${PASSIVE_SITE}')
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
                'DOCKER_CONFIG_JSON': Defaults.DOCKER_CONFIG_JSON,
                ]
            )
        }

        shell(Defaults.pullFromCommitShellCommand)
        // install docker config with permissions to the new DOCKER_CONFIG_JSON location
        shell(Defaults.install_docker_config_json())

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}'))

        shell('''
        DELETE_ALL_OPTION=$( [ "${DELETE_ALL}" == true ] && echo "--delete-all" || echo "" )

        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock \
                --env ACTIVE_SITE \
                --env PASSIVE_SITE \
                --env GR_STAGE_SHARED_NAME \
                --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
                --env PYTHONPATH=/workdir \
                 ${TEST_DOCKER_IMAGE} \
                    /bin/bash -c "source venv/bin/activate && \
                     python util_scripts/evnfm/delete_cnf_namespaces_script.py $DELETE_ALL_OPTION"
        ''')
    }
}
