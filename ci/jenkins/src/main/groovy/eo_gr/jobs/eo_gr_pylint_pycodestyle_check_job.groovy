import eo_gr.defaults.Defaults


def jobTitle = Defaults.DEFAULT_PREFIX + "-code-quality-check-pycodestyle-pylint-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description("""
        This is code quality check job that trigger only Pylint, Pycodestyle and Black checks on Patch set created Gerrit event.
    """, "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH")

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(50, 50)
    concurrentBuild(true)

    parameters {
        stringParam('GERRIT_BRANCH', Defaults.DEFAULT_BRANCH, 'Please specify branch for execution.')
        stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'Please use for running from commit, example: refs/changes/43/7079843/1')
    }

    triggers {
        gerrit {
            events {
                patchsetCreated()
            }
            project('plain:' + Defaults.TEST_FRAMEWORK_GIT_PROJECT_NAME, 'reg_exp:' + Defaults.ANY_BRANCH_REG)
        }
    }

    wrappers {
        preBuildCleanup()
        timestamps()
        buildName('#${BUILD_NUMBER}_${PROJECT_NAME}_${GERRIT_REFSPEC}')
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
                'CODE_CHECK_SCRIPT': Defaults.CODE_CHECK_SCRIPT
                ]
            )
        }

        shell(Defaults.pullFromCommitShellCommand)
        // install docker config with permissions to the new DOCKER_CONFIG_JSON location
        shell(Defaults.install_docker_config_json())

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}', '.', 'requirements-dev.txt'))

        shell('''
        chmod +rx ./${CODE_CHECK_SCRIPT}

        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock \
                --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
                --env PYTHONPATH=/workdir \
                 ${TEST_DOCKER_IMAGE} \
                    /bin/bash -c "source venv/bin/activate && /workdir/${CODE_CHECK_SCRIPT} /workdir"
        ''')
    }

}
