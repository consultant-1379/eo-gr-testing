import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-deploy-bur-sftp-server-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description("""This a job contains script for deploy BUR SFTP server for GR backups.
    SFTP Server is already predefined for GR envs in oss-integration-ci/site-values/eo/ci/override/gr/{ ENV }/site-values-override.yaml.
    <br>This script also performs the following GR pre-install steps:
    <br>- Checks connectivity and permissions from both GR cluster to newly deployed SFTP server.
    <br>- Measures link bandwidth between the SFTP server and both clusters.
    """, 
    "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(50, 50)
    concurrentBuild(true)

    parameters {
        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
        choiceParam('ACTIVE_SITE', Defaults.all_env_list, 'Select a Site (environment) for which BUR SFTP server will be deployed. BUR SFTP server runs for sites pair and a shared config file should be present in config/sftps. For example for ci476 env conf file: sftp_ci476_ci480.yaml')
        choiceParam('PASSIVE_SITE', Defaults.all_env_list_passive_site_default, 'Select a Passive Site (environment)')

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
        booleanParam('SKIP_BANDWIDTH_MEASUREMENT', false, 'Define if needed to skip bandwidth measurement.')

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
                'DOCKER_CONFIG_JSON': Defaults.DOCKER_CONFIG_JSON,  // change default DOCKER_CONFIG location
                ]
            )
        }

        shell(Defaults.pullFromCommitShellCommand)
        // install docker config with permissions to the new DOCKER_CONFIG_JSON location
        shell(Defaults.install_docker_config_json())

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}'))

        shell('''
        SKIP_BANDWIDTH_MEASUREMENT_OPTION=$( [ "${SKIP_BANDWIDTH_MEASUREMENT}" == true ] && echo "--disable-bandwidth-measurement" || echo "" )

        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock \
                --env ACTIVE_SITE \
                --env PASSIVE_SITE \
                --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
                --env PYTHONPATH=/workdir \
                 ${TEST_DOCKER_IMAGE} \
                    /bin/bash -c "source venv/bin/activate && \
                     python util_scripts/gr/deploy_sftp.py $SKIP_BANDWIDTH_MEASUREMENT_OPTION"
        ''')
    }
}
