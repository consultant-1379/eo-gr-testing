import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-install-cluster-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description("""This job install K8s CAPO (Cluster API Provider OpenStack) cluster.""",
    "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(10, 10)
    concurrentBuild(true)

        parameters {
            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
            choiceParam('ENV', Defaults.rv_env_list, 'Choose the environment you want to install')
            choiceParam('CONTROLLER_ENV', Defaults.controllersList, 'The server that is used to execute procedures')
            stringParam('ECCD_LINK', Defaults.ECCD_RELEASE_LINK, 'Provide link to download CAPO package.')
            stringParam('MASTER_DIMENSIONS', '3, 6, 8, 50', 'Provide info about master node.<br> Node Count, VCPUs per node, Memory per node (GB), Root Volume per node (GB).<br> Please contact REM engineer for the most up-to-date data.')
            stringParam('WORKER_DIMENSIONS', '4, 20, 32, 169', 'Provide info about worker (control plane) node.<br> Node Count, VCPUs per node, Memory per node (GB), Root Volume per node (GB).<br> Please contact REM engineer for the most up-to-date data.')

            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
            stringParam('GERRIT_BRANCH', Defaults.DEFAULT_BRANCH, 'eo-gr-testing repository branch')
            stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'refs to run from eo-gr-testing repository commit')
            stringParam('GERRIT_BRANCH_EO_INSTALL', Defaults.DEFAULT_BRANCH, 'eo-install repository branch')
            stringParam('GERRIT_REFSPEC_EO_INSTALL', '', 'refs to run from eo-install repository commit')

            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
            stringParam('JOB_TIMEOUT', Defaults.JOB_TIMEOUT, 'Fail the build after exceeding the specified timeout')
        }

    wrappers {
        buildName('#${BUILD_NUMBER}_install_${ENV}')
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

    steps {
        environmentVariables {
            envs([
                'TEST_DOCKER_IMAGE': Defaults.TEST_DOCKER_IMAGE + ':${GERRIT_BRANCH}',
                'DOCKER_CONFIG_JSON': Defaults.DOCKER_CONFIG_JSON, // change default DOCKER_CONFIG location
                'DOCKERFILE_PATH': Defaults.DOCKERFILE_PATH,
                'LOG_LEVEL': 'DEBUG',
                'PYTHON_PATH' : Defaults.PYTHON_PATH,
                'GIT_REPO': Defaults.TEST_FRAMEWORK_GIT_REPO,
                'INSTALL_CAPO': true,
                'EO_INSTALL': Defaults.EO_INSTALL,
                ]
            )
        }

        shell(Defaults.pullFromCommitShellCommand)

        shell(Defaults.set_up_eo_install_submodule('${GERRIT_BRANCH_EO_INSTALL}', '${GERRIT_REFSPEC_EO_INSTALL}'))

        // install docker config with permissions to the new DOCKER_CONFIG_JSON location
        shell(Defaults.install_docker_config_json())

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}', '${EO_INSTALL}'))

        shell('''
        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock \
            --env ENV \
            --env ECCD_LINK \
            --env CONTROLLER_ENV \
            --env MASTER_DIMENSIONS \
            --env WORKER_DIMENSIONS \
            --env INSTALL_CAPO \
            --env LOG_LEVEL \
            --env GIT_REPO \
            --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
            --env PYTHONPATH=/workdir/${EO_INSTALL} \
            ${TEST_DOCKER_IMAGE} \
            /bin/bash -c "cd ${EO_INSTALL} && source venv/bin/activate && python eo_install/main.py"
        ''')
    }

    publishers {
        archiveArtifacts{
            pattern('${EO_INSTALL}/*.log,${EO_INSTALL}/*.tar.*')
            allowEmpty(true)
            onlyIfSuccessful(false)
        }
    }
}
