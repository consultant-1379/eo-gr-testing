import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-clean-up-test-assets-and-dns"

pipelineJob(jobTitle) {

    description Defaults.description(
        "This pipeline performs:<br>- cleanup for test assets on VIM,<br>- cleanup CVNFM namespaces,<br>- removing DNS server and cleanup dns data cluster's configmap",
        "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )
    keepDependencies(false)
    logRotator(50, 50)

    parameters {
        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
        choiceParam("ACTIVE_SITE", Defaults.all_env_list, "Please choose the Active Site name")
        choiceParam("PASSIVE_SITE", Defaults.all_env_list_passive_site_default, "Please choose the Passive Site name")
        stringParam("SLAVE_LABEL", Defaults.DOCKER_SLAVE_LABEL_FEM_5, "Please provide slave to run job on. Or leave default one")
        choiceParam("VIM", Defaults.vim_list, "Select a vim to use. For selected option, a config file should be present in config/vims folder in the repo. Eg: vim_mycloud12A-test.yaml file is present for mycloud12A-test")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
        booleanParam("DELETE_ALL", false, "If checked then all assets (VIM and CNF) that start with 'gr-test' prefix will be removed.<br>Enable it for pre-installation sites phase, disable for post-testing phase.<br>DNS configurations will be removed regardless of the value of this parameter")
        stringParam("GR_STAGE_SHARED_NAME", "", "Provide shared name for search and delete Vim VMVNFM and CVNFM test assets.<br>WARNING: Ignored if DELETE_ALL is enabled.")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
        stringParam("GERRIT_BRANCH", Defaults.DEFAULT_BRANCH, "Please specify branch for execution")
        stringParam("GERRIT_REFSPEC", 'refs/heads/${GERRIT_BRANCH}', "Please use for running from eo-gr-testing repo commit, example 'refs/changes/43/7079843/1'")
    }
    definition {
            cps {
                script(readFileFromWorkspace(Defaults.PIPELINES_PATH + "eo_gr_clean_up_test_assets_and_dns.Jenkinsfile"))
                sandbox()
            }
        }
    logRotator(50, 50)
}
