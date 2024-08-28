import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-clean-up-registry-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description("""This job cleans up registry of provided environment.""",
    "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(50, 50)
    concurrentBuild(true)

        parameters {
            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
            choiceParam('ENV', Defaults.rv_env_list, 'Choose environment you want to install')

            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
            booleanParam('DELETE_NODE_IMAGES', false, 'Choose to delete docker images tagged to k8s-registry on both master and worker nodes. Requires access to master/cp VM')
            choiceParam('CONTROLLER_ENV', Defaults.controllersList, 'The server that is used to execute procedures')
            stringParam('JOB_TIMEOUT', Defaults.JOB_TIMEOUT, 'Fail the build after exceeding the specified timeout which is set in minutes')

            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
            stringParam('GERRIT_BRANCH', Defaults.DEFAULT_BRANCH, 'eo-gr-testing repository branch')
            stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'refs to run from eo-gr-testing repository commit')
            stringParam('GERRIT_BRANCH_EO_INSTALL', Defaults.DEFAULT_BRANCH, 'eo-install repository branch')
            stringParam('GERRIT_REFSPEC_EO_INSTALL', '', 'refs to run from eo-install repository commit')
        }

    wrappers {
        buildName('#${BUILD_NUMBER}_${ENV}')
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
                'CLEAN_ECCD': true,
                'GIT_REPO': Defaults.TEST_FRAMEWORK_GIT_REPO,
                'EO_INSTALL': Defaults.EO_INSTALL,
            ]
        )
    }
    steps {
        shell(Defaults.pullFromCommitShellCommand)

        shell(Defaults.set_up_eo_install_submodule('${GERRIT_BRANCH_EO_INSTALL}', '${GERRIT_REFSPEC_EO_INSTALL}'))

        // install docker config with permissions to the new DOCKER_CONFIG_JSON location
        shell(Defaults.install_docker_config_json())

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}', '${EO_INSTALL}'))

        shell('''
        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock \
            --env ENV \
            --env LOG_LEVEL \
            --env CONTROLLER_ENV \
            --env CLEAN_ECCD \
            --env DELETE_NODE_IMAGES \
            --env GIT_REPO \
            --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
            --env PYTHONPATH=/workdir/${EO_INSTALL} \
            ${TEST_DOCKER_IMAGE} \
            /bin/bash -c "cd ${EO_INSTALL} && source venv/bin/activate && python tools/cluster_cleanup/cleanup_mgr.py"
        ''')
    }

    publishers {
        archiveArtifacts{
            pattern('${EO_INSTALL}/*.log')
            allowEmpty(true)
            onlyIfSuccessful(false)
        }
    }
}
