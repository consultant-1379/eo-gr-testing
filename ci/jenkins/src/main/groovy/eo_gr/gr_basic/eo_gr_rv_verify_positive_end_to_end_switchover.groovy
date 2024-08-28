import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-rv-verify-positive-end-to-end-basic-scenario"

pipelineJob(jobTitle) {

    description Defaults.description(
        "This pipeline verifies EO GR positive test cases on RV (customer-like) environment",
        "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )
    keepDependencies(false)

    parameters {
        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
        choiceParam("ACTIVE_SITE", Defaults.rv_env_list, "Please choose the Active Site name")
        choiceParam("PASSIVE_SITE", Defaults.rv_env_list_passive_site_default, "Please choose the Passive Site name")
        stringParam("SLAVE_LABEL", Defaults.DOCKER_SLAVE_LABEL_FEM_5, "Please provide a specific slave name to run job on")
        choiceParam("VIM", Defaults.vim_list, "Select a vim to use. For selected option, a config file should be present in config/vims folder in the repo. Eg: vim_mycloud12A-test.yaml file is present for mycloud12A-test")
        stringParam("EO_VERSION", "", "Provide with the version of packages should be installed (e.g. 2.7.0-310). Optional if SKIP_EO_DEPLOY_AND_CONFIGURE enabled")
        stringParam("DEPLOYMENT_MANAGER_VERSION", "", "Provide a version of the deployment manager, e.g. 1.42.0-451. Optional if SKIP_EO_DEPLOY_AND_CONFIGURE enabled")
        booleanParam("ENABLE_VM_VNFM_HA", false, "Check to enable VM VNFM HA. Available starting from helmfile 2.22.x. Optional if SKIP_EO_DEPLOY_AND_CONFIGURE enabled")
        stringParam("NAMESPACE", "eo-deploy", "The name of the EO namespace")
        stringParam("GR_STAGE_SHARED_NAME", "positive-e2e", "Provide unique name for CVNFM tests assets")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
        stringParam("GERRIT_BRANCH", Defaults.DEFAULT_BRANCH, "Please specify branch for execution")
        stringParam("GERRIT_REFSPEC", 'refs/heads/${GERRIT_BRANCH}', "Please use for running from eo-gr-testing repo commit, example 'refs/changes/43/7079843/1' ")
        stringParam("GERRIT_BRANCH_EO_INSTALL", Defaults.DEFAULT_BRANCH, "eo-install repository branch")
        stringParam("GERRIT_REFSPEC_EO_INSTALL", '', "Please use for running from eo-install repo commit, example 'refs/changes/44/7079844/2'")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
        booleanParam("SKIP_SFTP_BANDWIDTH_MEASUREMENT", false, 'Define if needed to skip bandwidth measurement between SFTP server and both clusters.')
        stringParam("OVERRIDE", "", "Override the default environment configurations")
        booleanParam("PRETTY_API_LOGS", false, "true if API logs needed to be output in pretty format else false")
        booleanParam("SKIP_EO_DEPLOY_AND_CONFIGURE", false, "true if EO pre-setup (GR installation) need to be skipped else false")
        booleanParam("SKIP_CLEANUP_REGISTRY", false, 'true if needed to skip cleanup sites registries before GR installation. Optional if SKIP_EO_DEPLOY_AND_CONFIGURE enabled')
        booleanParam('EO_LOG_COLLECTION', true, 'true if needed to collect EO applications logs and attache it to current job from both sites')
        booleanParam('ENABLE_VMVNFM_DEBUG_LOG_LEVEL', false, 'true if needed to set debug log level for VMVNFM. By default INFO level is used. NOTE: changing of logging level may take some time, which may increase the total time of the job execution.')
    }

    definition {
            cps {
                script(readFileFromWorkspace(Defaults.GR_BASIC_PATH + "eo_gr_rv_verify_positive_end_to_end_switchover.Jenkinsfile"))
                sandbox()
            }
        }

    logRotator(50, 50)
}