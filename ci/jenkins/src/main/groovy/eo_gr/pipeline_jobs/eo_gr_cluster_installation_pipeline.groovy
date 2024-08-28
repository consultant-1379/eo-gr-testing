import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-cluster-capo-installation-pipeline"

pipelineJob(jobTitle) {

    description Defaults.description(
        "This job for installation K8s CAPO (Cluster API Provider OpenStack) cluster and performs post-installation steps",
        "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )
    keepDependencies(false)
    logRotator(50, 50)

    parameters {
        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
            choiceParam('ENV', Defaults.rv_env_list, 'Choose the environment you want to install')
            choiceParam('CONTROLLER_ENV', Defaults.controllersList, 'The server that is used to execute procedures')
            stringParam('ECCD_LINK', Defaults.ECCD_RELEASE_LINK, 'Provide link to download CAPO package.')
            stringParam('MASTER_DIMENSIONS', '3, 6, 8, 50', 'Provide info about master node.<br> Node Count, VCPUs per node, Memory per node (GB), Root Volume per node (GB).<br> Please contact REM engineer for the most up-to-date data.')
            stringParam('WORKER_DIMENSIONS', '4, 20, 32, 169', 'Provide info about worker (control plane) node.<br> Node Count, VCPUs per node, Memory per node (GB), Root Volume per node (GB).<br> Please contact REM engineer for the most up-to-date data.')
            stringParam("SLAVE_LABEL", Defaults.DOCKER_SLAVE_LABEL_FEM_5, "Please provide slave to run job on. Or leave default one")

            parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
            stringParam('GERRIT_BRANCH', Defaults.DEFAULT_BRANCH, 'eo-gr-testing repository branch')
            stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', 'refs to run from eo-gr-testing repository commit')
            stringParam('GERRIT_BRANCH_EO_INSTALL', Defaults.DEFAULT_BRANCH, 'eo-install repository branch')
            stringParam('GERRIT_REFSPEC_EO_INSTALL', '', 'refs to run from eo-install repository commit')
    }
    definition {
            cps {
                script(readFileFromWorkspace(Defaults.PIPELINES_PATH + "eo_gr_install_capo_cluster.Jenkinsfile"))
                sandbox()
            }
        }
}
