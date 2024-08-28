import eo_gr.defaults.Defaults

def jobTitle = Defaults.DEFAULT_PREFIX + "-rv-verify-upgrade-scenarios"

// def cronValue = "0 22 * * *"
def cronValue

// Assign false if cronValue is null
def cron = cronValue ?: false

pipelineJob(jobTitle) {

    description Defaults.description(
        """This pipeline allows to run selected upgrade RV scenarios one by one. It is triggered by cron: $cron""",
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
        choiceParam("ACTIVE_SITE", Defaults.rv_upgrade_env_list, "Please choose the Active Site name")
        choiceParam("PASSIVE_SITE", Defaults.rv_upgrade_env_list_passive_site_default, "Please choose the Passive Site name")
        stringParam("SLAVE_LABEL", Defaults.DOCKER_SLAVE_LABEL_FEM_5, "Please provide slave to run job on. Or leave default one")
        choiceParam("VIM", Defaults.vim_list, "Select a vim to use. For selected option, a config file should be present in config/vims folder in the repo. Eg: vim_mycloud12A-test.yaml file is present for mycloud12A-test")
        booleanParam("SKIP_EO_DEPLOY_AND_CONFIGURE", false, "true if EO pre-setup need to be skipped else false")
        stringParam("EO_VERSION", "", "Provide with the version of packages should be installed (e.g. 2.7.0-310)")
        stringParam("DEPLOYMENT_MANAGER_VERSION", "", "Provide a version of the deployment manager, e.g. 1.42.0-451")
        stringParam("EO_UPGRADE_VERSION", "", "Provide with the version of packages the site should be upgraded to (e.g. 2.8.0-40)")
        stringParam("DEPLOYMENT_MANAGER_UPGRADE_VERSION", "", "Provide a version of the deployment manager the site should be upgraded with, e.g. 1.43.0-45")
        booleanParam("ENABLE_VM_VNFM_HA", true, "Check to enable VM VNFM HA. Available starting from helmfile 2.22.x")
        stringParam("NAMESPACE", "eo-deploy", "The name of the EO namespace")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.TEST_PARAMETERS))
        booleanParam("SWITCHOVER_BEFORE_EO_UPGRADE", true, "true if need to run 'Switchover Before EO Upgrade Scenario'")
        booleanParam("SWITCHOVER_AFTER_EO_UPGRADE", true, "true if need to run 'Switchover After EO Upgrade Scenario'")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
        stringParam("GERRIT_BRANCH", Defaults.DEFAULT_BRANCH, "Please specify branch for execution")
        stringParam("GERRIT_REFSPEC", 'refs/heads/${GERRIT_BRANCH}', "Please use for running from eo-gr-testing repo commit, example 'refs/changes/43/7079843/1' ")
        stringParam("GERRIT_BRANCH_EO_INSTALL", Defaults.DEFAULT_BRANCH, "eo-install repository branch")
        stringParam("GERRIT_REFSPEC_EO_INSTALL", '', "Please use for running from eo-install repo commit, example 'refs/changes/44/7079844/2'")
        stringParam("GERRIT_BRANCH_EO_INSTALL_UPGRADE", "master", "eo-install repository branch for upgrade EO version")
        stringParam("GERRIT_REFSPEC_EO_INSTALL_UPGRADE", '', "Please use for running from eo-install repo commit for upgrade EO version, example 'refs/changes/44/7079844/2'")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
        booleanParam("EO_VERSIONS_COLLECTION", true, "true if EO logs expected to be collected else false")
        booleanParam('EO_LOG_COLLECTION', true, 'true if needed to collect EO applications logs and attache it to current job from both sites')
        booleanParam("PRETTY_API_LOGS", false, "true if API logs needed to be output in pretty format else false")
        stringParam('OVERRIDE', '', '''Optional parameter. Overriding parameters specified in config folder.
            Basic rules for parameters override:
                - The parameters should be separated by # symbol:
                    Eg: OPENSTACK_CLIENT_HOST=0000.0000.0000.0000#OPENSTACK_CLIENT_USERNAME=test
                - The config/artifacts.yaml has nested structure and parameters path should be separated by | symbol::
                    Eg: artefacts|spider_app_multi_a|package_path=package.csar#artefacts|spider_app_multi_a|cnf_descriptor_id=CNF-124863124''')

    }

    definition {
            cps {
                script(readFileFromWorkspace(Defaults.GR_UPGRADE_PATH + "eo_gr_rv_verify_upgrade_scenarios.Jenkinsfile"))
                sandbox()
            }
        }

    logRotator(50, 50)
}