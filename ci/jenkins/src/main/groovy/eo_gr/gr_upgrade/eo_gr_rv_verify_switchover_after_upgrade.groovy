import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-rv-verify-switchover-after-upgrade-scenario"

pipelineJob(jobTitle) {

    description Defaults.description(
        "This pipeline verifies EO GR switchover after the upgrade on RV (customer-like) environment",
        "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )
    keepDependencies(false)

    parameters {
        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
        choiceParam("ACTIVE_SITE", Defaults.rv_env_list, "Please choose the Active Site name")
        choiceParam("PASSIVE_SITE", Defaults.rv_env_list_passive_site_default, "Please choose the Passive Site name")
        stringParam("SLAVE_LABEL", Defaults.DOCKER_SLAVE_LABEL_FEM_5, "Please provide a specific slave name to run job on")
        choiceParam("VIM", Defaults.vim_list, "Select a vim to use. For selected option, a config file should be present in config/vims folder in the repo. Eg: vim_mycloud12A-test.yaml file is present for mycloud12A-test")
        stringParam("EO_VERSION", "", "Provide with the version of packages should be installed (e.g. 2.7.0-310)")
        stringParam("DEPLOYMENT_MANAGER_VERSION", "", "Provide a version of the deployment manager, e.g. 1.42.0-451")
        stringParam("EO_UPGRADE_VERSION", "", "Provide with the version of packages the site should be upgraded to (e.g. 2.8.0-40)")
        stringParam("DEPLOYMENT_MANAGER_UPGRADE_VERSION", "", "Provide a version of the deployment manager the site should be upgraded with, e.g. 1.43.0-45")
        booleanParam("ENABLE_VM_VNFM_HA", true, "Check to enable VM VNFM HA. Available starting from helmfile 2.22.x")
        stringParam("NAMESPACE", "eo-deploy", "The name of the EO namespace")
        stringParam("GR_STAGE_SHARED_NAME", "swtch-after-upgr", "Provide unique name for CVNFM tests assets")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
        stringParam("GERRIT_BRANCH", Defaults.DEFAULT_BRANCH, "Please specify branch for execution")
        stringParam("GERRIT_REFSPEC", 'refs/heads/${GERRIT_BRANCH}', "Please use for running from eo-gr-testing repo commit, example 'refs/changes/43/7079843/1' ")
        stringParam("GERRIT_BRANCH_EO_INSTALL", Defaults.DEFAULT_BRANCH, "eo-install repository branch")
        stringParam("GERRIT_REFSPEC_EO_INSTALL", '', "Please use for running from eo-install repo commit, example 'refs/changes/44/7079844/2'")
        stringParam("GERRIT_BRANCH_EO_INSTALL_UPGRADE", "master", "eo-install repository branch for upgrade EO version")
        stringParam("GERRIT_REFSPEC_EO_INSTALL_UPGRADE", '', "Please use for running from eo-install repo commit for upgrade EO version, example 'refs/changes/44/7079844/2'")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
        stringParam("OVERRIDE", "", "Override the default environment configurations")
        booleanParam("PRETTY_API_LOGS", false, "true if API logs needed to be output in pretty format else false")
        booleanParam("SKIP_EO_DEPLOY_AND_CONFIGURE", false, "true if EO pre-setup need to be skipped else false")
        booleanParam("SKIP_COPY_KMS_KEYS_AFTER_SITES_INSTALLATION", true, "true if need to skip copying kms keys as post-install step")
        booleanParam('EO_LOG_COLLECTION', true, 'true if needed to collect EO applications logs and attache it to current job from both sites')
    }

    definition {
            cps {
                script(readFileFromWorkspace(Defaults.GR_UPGRADE_PATH + "eo_gr_rv_verify_switchover_after_upgrade.Jenkinsfile"))
                sandbox()
            }
        }

    logRotator(50, 50)
}