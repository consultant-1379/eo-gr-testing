import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-create-new-evnfm-user-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description(
        "This job contains script for create new EVNFM user after EO GR install.",
        "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(50, 50)
    concurrentBuild(true)

    parameters {
        choiceParam('ACTIVE_SITE', Defaults.all_env_list, 'Select a active environment to update.')
        booleanParam('USE_LOCAL_DNS', true, "If checked job runs with local DNS server settings, otherwise global DNS will be used. Make sure local DNS Server is up for environment.")
        stringParam('GERRIT_BRANCH', Defaults.DEFAULT_BRANCH, 'Please specify branch for execution.')
        stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'Please use for running from commit, example: refs/changes/43/7079843/1')
    }

    wrappers {
        preBuildCleanup()
        timestamps()
        buildName('#${BUILD_NUMBER}_${PROJECT_NAME}_${ACTIVE_SITE}')
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

    environmentVariables {
        env('GIT_REPO', Defaults.TEST_FRAMEWORK_GIT_REPO)
        env('TEST_DOCKER_IMAGE', Defaults.TEST_DOCKER_IMAGE + ':${GERRIT_BRANCH}')
        env('DOCKER_CONFIG_JSON', Defaults.DOCKER_CONFIG_JSON)
    }

    steps {
        shell(Defaults.pullFromCommitShellCommand)
        // install docker config with permissions to the new DOCKER_CONFIG_JSON location
        shell(Defaults.install_docker_config_json())

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}'))

        shell(Defaults.defineDnsIpAndDnsFlagEnvVars('${TEST_DOCKER_IMAGE}', '${ACTIVE_SITE}')) // --> DNS_FLAG, DNS_SERVER_IP
        environmentVariables { propertiesFile(Defaults.ENV_PROPERTY_FILE) }

        shell('''

        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock \
             $DNS_FLAG \
                --env ACTIVE_SITE \
                --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
                --env DNS_SERVER_IP \
                --env PYTHONPATH=/workdir \
                 ${TEST_DOCKER_IMAGE} \
                    /bin/bash -c "source venv/bin/activate && \
                     python util_scripts/evnfm/create_new_evnfm_user.py"
        ''')
    }
}
