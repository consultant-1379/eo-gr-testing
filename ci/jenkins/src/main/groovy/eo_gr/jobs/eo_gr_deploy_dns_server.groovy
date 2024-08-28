import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-deploy-dns-server-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description("""This job runs script that deploys a DNS server (dnsmasq) that makes re-routing for the dedicated EO cluster
    """, 
    "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(50, 50)
    concurrentBuild(true)

    parameters {
        choiceParam('ACTIVE_SITE', Defaults.all_env_list, 'A site (environment) hostnames and IP of which will be used for the DNS masquerading')
        choiceParam('PASSIVE_SITE', Defaults.all_env_list_passive_site_default, 'A site (environment) global registry IP of which will be used for the DNS masquerading')
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
                'DOCKER_CONFIG_DIR': Defaults.DOCKER_CONFIG_DIR,  // change default DOCKER_CONFIG location
                'DOCKER_CONFIG_JSON': Defaults.DOCKER_CONFIG_JSON,
                ]
            )
        }

        shell(Defaults.pullFromCommitShellCommand)
        // install docker config with permissions to the new Docker config.json location
        shell(Defaults.install_docker_config_json())

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}'))

        shell('''
        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock \
                -v ${DOCKER_CONFIG_DIR}:/workdir/.docker \
                --env ACTIVE_SITE=${ACTIVE_SITE} \
                --env PASSIVE_SITE=${PASSIVE_SITE} \
                --env DOCKER_CONFIG=/workdir/.docker/config.json  \
                --env PYTHONPATH=/workdir \
                 ${TEST_DOCKER_IMAGE} \
                    /bin/bash -c "source venv/bin/activate && \
                     python util_scripts/gr/deploy_dnsmasq.py"
        ''')
    }
}
