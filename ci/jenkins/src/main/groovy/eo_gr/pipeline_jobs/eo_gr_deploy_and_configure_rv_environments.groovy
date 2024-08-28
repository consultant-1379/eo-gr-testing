import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-deploy-and-configure-rv-environments-job"

pipelineJob(jobTitle) {

    description Defaults.description(
        "This pipeline deploys RV environments and prepares environments for run RV tests. This is pre-setup stage for RV pipelines.",
        "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )
    keepDependencies(false)

    parameters {
        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
        choiceParam("ACTIVE_SITE", Defaults.rv_env_list, "Please choose the Active Site name")
        choiceParam("PASSIVE_SITE", Defaults.rv_env_list_passive_site_default, "Please choose the Passive Site name")
        stringParam("SLAVE_LABEL", Defaults.DOCKER_SLAVE_LABEL_FEM_5, "Please provide slave to run job on. Or leave default one")
        choiceParam("VIM", Defaults.vim_list, "Select a vim to use. For selected option, a config file should be present in config/vims folder in the repo. Eg: vim_mycloud12A-test.yaml file is present for mycloud12A-test")
        stringParam("EO_VERSION", "", "Provide with the version of packages should be installed (e.g. 2.7.0-310)")
        stringParam("DEPLOYMENT_MANAGER_VERSION", "", "Provide a version of the deployment manager, e.g. 1.42.0-451")
        stringParam("NAMESPACE", "eo-deploy", "The name of the EO namespace")
        booleanParam("ENABLE_VM_VNFM_HA", false, "Check to enable VM VNFM HA. Available starting from helmfile 2.22.x")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
        stringParam("GERRIT_BRANCH", Defaults.DEFAULT_BRANCH, "Please specify branch for execution")
        stringParam("GERRIT_REFSPEC", 'refs/heads/${GERRIT_BRANCH}', "Please use for running from eo-gr-testing repo commit, example 'refs/changes/43/7079843/1'")
        stringParam("GERRIT_BRANCH_EO_INSTALL", Defaults.DEFAULT_BRANCH, "eo-install repository branch")
        stringParam("GERRIT_REFSPEC_EO_INSTALL", '', "Please use for running from eo-install repo commit, example 'refs/changes/44/7079844/2'")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
        booleanParam("SKIP_CREATE_SUPERUSER_PASSWORD_STAGE", false, "true if need to skip creating superuser password stage else false")
        booleanParam("SKIP_COPY_KMS_KEYS_AFTER_SITES_INSTALLATION", false, "true if need to skip copying kms keys as post-install step")
        booleanParam("PRETTY_API_LOGS", false, "true if API logs needed to be output in pretty format else false")
        booleanParam("SKIP_SFTP_BANDWIDTH_MEASUREMENT", false, 'true if needed to skip bandwidth measurement between SFTP server and both clusters.')
        booleanParam("SKIP_CLEANUP_REGISTRY", false, 'true if needed to skip cleanup sites registries before installation.')
    }
    definition {
            cps {
                script(readFileFromWorkspace(Defaults.PIPELINES_PATH + "eo_gr_deploy_and_configure_rv_environments.Jenkinsfile"))
                sandbox()
            }
        }
    logRotator(50, 50)
}
