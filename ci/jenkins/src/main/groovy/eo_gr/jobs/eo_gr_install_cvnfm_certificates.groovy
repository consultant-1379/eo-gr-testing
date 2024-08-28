import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-install-cvnfm-certificates-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description(
        """This is EO GR post-install job that installs CVNFM certificates for signed packages on both GR sites""",
        "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(50, 50)
    concurrentBuild(true)

    parameters {
        choiceParam('ACTIVE_SITE', Defaults.all_env_list, 'Select GR Active Site environment for which you need to install CVNFM certificates.')
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
        env('AM_INTEGRATION_CHARTS_REPO', Defaults.AM_INTEGRATION_CHARTS_REPO)
        env('EO_INTEGRATION_CI_REPO', Defaults.EO_INTEGRATION_CI_REPO)
    }

    steps {
        shell(Defaults.pullFromCommitShellCommand)
        // install docker config with permissions to the new DOCKER_CONFIG_JSON location
        shell(Defaults.install_docker_config_json())

        shell(Defaults.pythonVirtualEnvAndInstallDependenciesSetUpInDocker('${TEST_DOCKER_IMAGE}'))

        shell(Defaults.defineDnsIpAndDnsFlagEnvVars('${TEST_DOCKER_IMAGE}', '${ACTIVE_SITE}')) // --> DNS_FLAG, DNS_SERVER_IP
        environmentVariables { propertiesFile(Defaults.ENV_PROPERTY_FILE) }

        shell(Defaults.is_rv_setup() + '''
        echo "Docker image that is used --> ${TEST_DOCKER_IMAGE}"

        if [ "${RV_SETUP}" == false ]; then
            REPO_WITH_CERT="eo-integration-ci"
        else
            REPO_WITH_CERT="eo-install"
        fi

        echo "Submodule with intermediate certificate: ${REPO_WITH_CERT}"

        git submodule update --init --recursive --remote --depth=1 ./am-integration-charts ./${REPO_WITH_CERT}

        docker run --init --rm -v $(pwd):/workdir --workdir /workdir/ -v /etc/hosts:/etc/hosts -v /var/run/docker.sock:/var/run/docker.sock \
             $DNS_FLAG \
                --env ACTIVE_SITE \
                --env RV_SETUP \
                --env DNS_SERVER_IP \
                --env DOCKER_CONFIG=${DOCKER_CONFIG_JSON} \
                --env PYTHONPATH=/workdir \
                 ${TEST_DOCKER_IMAGE} \
                    /bin/bash -c "source venv/bin/activate && \
                     python util_scripts/evnfm/install_cvnfm_certificates.py"
        ''')
    }
}
