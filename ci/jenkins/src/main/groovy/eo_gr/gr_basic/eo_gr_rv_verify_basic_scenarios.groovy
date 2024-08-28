import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-rv-verify-basic-scenarios"

// def cronValue = "0 21 * * *"
def cronValue

// Assign false if cronValue is null
def cron = cronValue ?: false

pipelineJob(jobTitle) {

    description Defaults.description(
        """This pipeline allows to run selected RV basic scenarios one by one. It is triggered by cron: $cron""",
        "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )
    keepDependencies(false)

//  Disabling automatic job trigger
//     properties {
//         pipelineTriggers {
//             triggers {
//                 cron {
//                     spec(cronValue)
//                 }
//             }
//         }
//     }

    parameters {
        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
        choiceParam("ACTIVE_SITE", Defaults.rv_env_list, "Please choose the Active Site name")
        choiceParam("PASSIVE_SITE", Defaults.rv_env_list_passive_site_default, "Please choose the Passive Site name")
        stringParam("SLAVE_LABEL", Defaults.DOCKER_SLAVE_LABEL_FEM_5, "Please provide slave to run job on. Or leave default one")
        choiceParam("VIM", Defaults.vim_list, "Select a vim to use. For selected option, a config file should be present in config/vims folder in the repo. Eg: vim_mycloud12A-test.yaml file is present for mycloud12A-test")
        stringParam("EO_VERSION", "", "Provide with the version of packages should be installed (e.g. 2.7.0-310). Optional if SKIP_EO_DEPLOY_AND_CONFIGURE enabled")
        stringParam("DEPLOYMENT_MANAGER_VERSION", "", "Provide a version of the deployment manager, e.g. 1.42.0-451. Optional if SKIP_EO_DEPLOY_AND_CONFIGURE enabled")
        booleanParam("ENABLE_VM_VNFM_HA", true, "Check to enable VM VNFM HA. Available starting from helmfile 2.22.x. Optional if SKIP_EO_DEPLOY_AND_CONFIGURE enabled")
        stringParam("NAMESPACE", "eo-deploy", "The name of the EO namespace")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.TEST_PARAMETERS))
        booleanParam("POSITIVE_END_TO_END_SCENARIO", true, "true if need to run 'Positive End-to-end Scenario'")
        booleanParam("SWITCHOVER_WHEN_ACTIVE_SITE_NOT_AVAILABLE_SCENARIO", true, "true if need to run 'Switchover When Active Site Not Available Scenario'")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
        stringParam("GERRIT_BRANCH", Defaults.DEFAULT_BRANCH, "Please specify branch for execution")
        stringParam("GERRIT_REFSPEC", 'refs/heads/${GERRIT_BRANCH}', "Please use for running from eo-gr-testing repo commit, example 'refs/changes/43/7079843/1' ")
        stringParam("GERRIT_BRANCH_EO_INSTALL", Defaults.DEFAULT_BRANCH, "eo-install repository branch")
        stringParam("GERRIT_REFSPEC_EO_INSTALL", '', "Please use for running from eo-install repo commit, example 'refs/changes/44/7079844/2'")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
        booleanParam("SKIP_SFTP_BANDWIDTH_MEASUREMENT", false, 'Define if needed to skip bandwidth measurement between SFTP server and both clusters.')
        booleanParam("EO_VERSIONS_COLLECTION", true, "true if EO logs expected to be collected else false")
        booleanParam('EO_LOG_COLLECTION', true, 'true if needed to collect EO applications logs and attache it to current job from both sites')
        booleanParam("PRETTY_API_LOGS", false, "true if API logs needed to be output in pretty format else false")
        booleanParam('ENABLE_VMVNFM_DEBUG_LOG_LEVEL', false, 'true if needed to set debug log level for VMVNFM. By default INFO level is used. NOTE: changing of logging level may take some time, which may increase the total time of the job execution.')
        stringParam('OVERRIDE', '', '''Optional parameter. Overriding parameters specified in config folder.
            Basic rules for parameters override:
                - The parameters should be separated by # symbol:
                    Eg: OPENSTACK_CLIENT_HOST=0000.0000.0000.0000#OPENSTACK_CLIENT_USERNAME=test
                - The config/artifacts.yaml has nested structure and parameters path should be separated by | symbol::
                    Eg: artefacts|spider_app_multi_a|package_path=package.csar#artefacts|spider_app_multi_a|cnf_descriptor_id=CNF-124863124''')
        booleanParam("SKIP_EO_DEPLOY_AND_CONFIGURE", false, "true if EO pre-setup (GR installation) need to be skipped else false")
        booleanParam("SKIP_CLEANUP_REGISTRY", false, 'true if needed to skip cleanup sites registries before GR installation. Optional if SKIP_EO_DEPLOY_AND_CONFIGURE enabled')

    }

    definition {
            cps {
                script(readFileFromWorkspace(Defaults.GR_BASIC_PATH + "eo_gr_rv_verify_basic_scenarios.Jenkinsfile"))
                sandbox()
            }
        }

    logRotator(50, 50)
}