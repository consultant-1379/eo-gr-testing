import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-copy-kms-key-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description("""This job contains script that copies KMS Master key from Active Site to Passive Site.
    This is one of the required steps for the GR Switchover operation""",
    "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(50, 50)
    concurrentBuild(true)

    parameters {
        choiceParam('ACTIVE_SITE', Defaults.all_env_list, 'Select an ACTIVE SITE (environment) to use. For selected option, a config file should be present in config/envs folder in the repo. Eg: env_ci476.yaml file is present for value ci476')
        choiceParam('PASSIVE_SITE', Defaults.all_env_list_passive_site_default, 'Select an PASSIVE SITE (environment) to use. For selected option, a config file should be present in config/envs folder in the repo. Eg: env_ci476.yaml file is present for value ci476')
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
                'DOCKER_CONFIG_JSON': Defaults.DOCKER_CONFIG_JSON,  // change default DOCKER_CONFIG location
                ]
            )
        }

        shell(Defaults.pullFromCommitShellCommand)
        // install docker config with permissions to the new DOCKER_CONFIG_JSON location
        shell(Defaults.install_docker_config_json())

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}'))

        shell('''
        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /var/run/docker.sock:/var/run/docker.sock \
                --env ACTIVE_SITE \
                --env PASSIVE_SITE \
                --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
                --env PYTHONPATH=/workdir \
                 ${TEST_DOCKER_IMAGE} \
                    /bin/bash -c "source venv/bin/activate && \
                     python util_scripts/gr/copy_kms_key_script.py"
        ''')
    }
}
