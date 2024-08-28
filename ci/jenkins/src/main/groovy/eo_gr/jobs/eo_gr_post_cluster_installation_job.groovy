import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-post-cluster-installation-steps-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description(
    """This job runs scripts that perform required EO cluster post-installation activities on provided site:
    <br>-Update kubeconfig on the cluster's master nodes.
    <br>-Create and mount network file storage class for VMVNFM HA feature.
    """,
    "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(10, 10)
    concurrentBuild(true)

    parameters {
        choiceParam('ENV', Defaults.rv_env_list, 'Select a Site (environment, cluster) to use')
        stringParam('GERRIT_BRANCH', Defaults.DEFAULT_BRANCH, 'Please specify branch for execution.')
        stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'Please use for running from commit, example: refs/changes/43/7079843/1')
    }

    wrappers {
        preBuildCleanup()
        timestamps()
        buildName('#${BUILD_NUMBER}_${PROJECT_NAME}_${ENV}')
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
        // install docker config with permissions to the new Docker config.json location
        shell(Defaults.install_docker_config_json())
        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}'))

        shell('''
        echo "Start running post-install cluster scripts...."

        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock \
                -v $WORKSPACE/.docker:/workdir/.docker \
                --env ACTIVE_SITE=${ENV} \
                --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
                --env PYTHONPATH=/workdir \
                 ${TEST_DOCKER_IMAGE} \
                    /bin/bash -c "source venv/bin/activate && \
                     python util_scripts/cluster_post_install/update_kubeconfig_script.py && \
                     python util_scripts/cluster_post_install/create_network_file_storage_class_script.py"
        ''')
    }
}
