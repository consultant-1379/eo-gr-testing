import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-publish-test-image-job"

freeStyleJob("${jobTitle}") {
    description Defaults.description("""This job publishes EO GR test image to the Docker registry""",
    "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )

    label Defaults.DOCKER_SLAVE_LABEL_FEM_5
    logRotator(10, 10)
    concurrentBuild(false)

    parameters {
        stringParam('GERRIT_BRANCH', Defaults.DEFAULT_BRANCH, 'Please specify branch for execution.')
        stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'Please use this parameter for running from commit, example: refs/changes/43/7079843/1')
        stringParam('IMAGE_TAG', '', 'OPTIONAL. Please use this parameter to create a custom docker image otherwise provided branch name will be used')
    }

    triggers {
        gerrit {
            events {
                changeMerged()
            }
            project('plain:' + Defaults.TEST_FRAMEWORK_GIT_PROJECT_NAME, 'reg_exp:' + Defaults.ANY_BRANCH_REG)
        }
    }
    wrappers {
        preBuildCleanup()
        timestamps()
        buildName('#${BUILD_NUMBER}_${PROJECT_NAME}_${GERRIT_BRANCH}_${IMAGE_TAG}')
        credentialsBinding {
            usernamePassword('DOCKER_USER_NAME', 'DOCKER_USER_PASSWORD', Defaults.DOCKER_AUTH_CREDS)
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
                'TEST_DOCKER_IMAGE': Defaults.TEST_DOCKER_IMAGE,
                'DOCKERFILE_PATH': Defaults.DOCKERFILE_PATH,
                'DOCKER_REGISTRY': Defaults.TEST_DOCKER_IMAGE.tokenize('/')[0]
                ]
            )
        }

        shell(Defaults.pullFromCommitShellCommand)

        shell('''
        IFS='/' read -r resources_dir dockerfile_dir file <<< ${DOCKERFILE_PATH}
        DOCKERFILE_DIR="${resources_dir}/${dockerfile_dir}"

        if [ -z "${IMAGE_TAG}" ]; then
            IMAGE_TAG="${GERRIT_BRANCH}"
        fi
        echo "IMAGE_TAG -> ${IMAGE_TAG}"

        FULL_IMAGE_NAME="${TEST_DOCKER_IMAGE}:${IMAGE_TAG}"

        echo $DOCKER_USER_PASSWORD | docker login $DOCKER_REGISTRY -u $DOCKER_USER_NAME --password-stdin
        docker build $DOCKERFILE_DIR --label image_version=$IMAGE_TAG --tag $FULL_IMAGE_NAME
        docker push $FULL_IMAGE_NAME
        docker logout $DOCKER_REGISTRY

        echo "Image: ${FULL_IMAGE_NAME} has been successfully created."
        ''')
    }
}
