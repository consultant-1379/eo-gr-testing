import eo_gr.defaults.Defaults


for ( def jobType : ['', '-debug']) {
    def jobName = Defaults.DEFAULT_PREFIX + "-switchover-pipeline${jobType}-job"

    pipelineJob(jobName) {

    description Defaults.description(
        "This pipeline prepares workdir with all necessary file for making deployment manager geo redundancy switchover operations",
        "$IS_JOB_BUILDED_FROM_REFSPEC", "$GERRIT_REFSPEC", "$GERRIT_BRANCH"
    )
    keepDependencies(false)

  parameters {
        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.ENVIRONMENT_PARAMETERS))
        choiceParam('ACTIVE_SITE', Defaults.all_env_list, "Please specify the Active Site name")
        choiceParam('PASSIVE_SITE', Defaults.all_env_list_passive_site_default, "Please specify the Passive Site name")
        stringParam('SLAVE_LABEL', 'evo_docker_engine_gic', 'Specify the slave label that you want the job to run on')
        choiceParam('SWITCHOVER_RULE', Defaults.switchover_test_rule_list, "Please specify the rule for switchover run")
        stringParam('CLEAN_UP_WORKDIR', 'true', 'Set to true if the working directory should be cleaned up after the pipeline ends')
        stringParam('FLOW_AREA', 'default', 'Refers to product deployment area. Eg:- eiapaas, release, productstaging, etc...')
        stringParam('PLATFORM_TYPE', 'default', 'The platform type of the environment. Eg:-Azure, AWS, GCP, CCD, EWS, openshift etc..')
        stringParam('INT_CHART_VERSION', 'The version of base platform to install')
        stringParam('INT_CHART_NAME', 'eric-eo-helmfile', 'Integration Chart Name')
        stringParam('INT_CHART_REPO', 'https://arm.seli.gic.ericsson.se/artifactory/proj-eo-drop-helm', 'Integration Chart Repo')
        stringParam('DEPLOYMENT_MANAGER_DOCKER_IMAGE', 'armdocker.rnd.ericsson.se/proj-eric-oss-drop/eric-oss-deployment-manager:default',
         'The full image url and tag for the deployment manager to use for the deployment. If the tag is set to default the deployment manager details will be fetched from the dm_version.yaml file from within the helmfile tar file under test')
        stringParam('ARMDOCKER_USER_SECRET', 'cloudman-docker-auth-config', 'ARM Docker secret')
        stringParam('HELM_TIMEOUT', '1800', 'Time in seconds for the Deployment Manager to wait for the deployment to execute, default 1800')
        stringParam('DOCKER_TIMEOUT', '60', 'Time in seconds for the Deployment Manager to wait for the pulling of docker images to be used for deployment')
        stringParam('TAGS', 'eoEvnfm eoVmvnfm', 'List of tags for applications that have to be deployed (e.g: so adc pf). Enter "None" into this field to leave all tags as false')
        stringParam('LA_HOSTNAME', 'default', 'Hostname for Log Aggregator')
        stringParam('KAFKA_BOOTSTRAP_HOSTNAME', 'default', 'Hostname for Kafka Bootstrap')
        stringParam('IAM_HOSTNAME', 'default', 'Hostname for IAM')
        stringParam('SO_HOSTNAME', 'default', 'Hostname for SO')
        stringParam('UDS_HOSTNAME', 'default', 'Hostname for UDS')
        stringParam('PF_HOSTNAME', 'default', 'Hostname for PF')
        stringParam('GAS_HOSTNAME', 'default', 'Hostname for GAS')
        stringParam('ADC_HOSTNAME', 'default', 'Hostname for ADC')
        stringParam('APPMGR_HOSTNAME', 'default', 'Hostname for Application Manager')
        stringParam('TA_HOSTNAME', 'default', 'Hostname for Task Automation')
        stringParam('EAS_HOSTNAME', 'default', 'Hostname for Ericsson Adaptation Support')
        stringParam('CH_HOSTNAME', 'default', 'Hostname for Configuration Handling')
        stringParam('TH_HOSTNAME', 'default', 'Hostname for Topology Handling')
        stringParam('OS_HOSTNAME', 'default', 'Hostname for Oran Support')
        stringParam('VNFM_HOSTNAME', 'default', 'Hostname for EO EVNFM')
        stringParam('VNFM_REGISTRY_HOSTNAME', 'default', 'Registry Hostname for EO EVNFM')
        stringParam('GR_HOSTNAME', 'default', 'Hostname for EO GR')
        stringParam('ML_HOSTNAME', 'default', 'Hostname for Machine Learning(ML) Application')
        stringParam('BDR_HOSTNAME', 'default', 'Hostname for Bulk Data Repository (BDR) Application')
        stringParam('AVIZ_HOSTNAME', 'default', 'Hostname for Assurance Visualization Application')
        stringParam('EO_CM_HOSTNAME', 'default', 'EO_CM_HOSTNAME')
        stringParam('HELM_REGISTRY_HOSTNAME', 'default', 'Hostname for EO HELM Registry')
        stringParam('VNFLCM_SERVICE_DEPLOY', 'false', 'EO VM VNFM Deploy, set \"true\" or \"false\"')
        stringParam('HELM_REGISTRY_DEPLOY', 'false', 'EO HELM Registry Deploy, set \"true\" or \"false\"')
        stringParam('IDUN_USER_SECRET', 'idun_credentials', 'Jenkins secret ID for default IDUN user password')
        stringParam('FULL_PATH_TO_SITE_VALUES_FILE', 'Full path within the Repo to the site_values.yaml file')
        stringParam('PATH_TO_SITE_VALUES_OVERRIDE_FILE', 'NONE', 'Path within the Repo to the location of the site values override file(s). Content will override the content for the site values set in the FULL_PATH_TO_SITE_VALUES_FILE paramater.  Use CSV format for more than 1 override file')
        stringParam('PATH_TO_CERTIFICATES_FILES', 'Path within the Repo to the location of the certificates directory')
        stringParam('NAMESPACE', 'Namespace to install the Chart')
        stringParam('KUBECONFIG_FILE', 'Kubernetes configuration file to specify which environment to install on')
        stringParam('FUNCTIONAL_USER_SECRET', 'cloudman-user-creds', 'Jenkins secret ID for ARM Registry Credentials')
        stringParam('FUNCTIONAL_USER_TOKEN', 'NONE', 'Jenkins identity token for ARM Registry access')
        stringParam('WHAT_CHANGED', 'None', 'Variable to store what chart contains the change')
        stringParam('DOCKER_REGISTRY', 'armdocker.rnd.ericsson.se', 'Set this to the docker registry to execute the deployment from. Used when deploying from Officially Released CSARs')
        stringParam('DOCKER_REGISTRY_CREDENTIALS', 'None', 'Jenkins secret ID for the Docker Registry. Not needed if deploying from armdocker.rnd.ericsson.se')
        stringParam('CI_DOCKER_IMAGE', 'armdocker.rnd.ericsson.se/proj-eric-oss-drop/eric-oss-ci-scripts:default', 'CI Docker image to use. Mainly used in CI Testing flows')
        stringParam('CRD_NAMESPACE', 'crd-namespace', 'Namespace which was used to deploy the CRD')
        stringParam('IPV6_ENABLE', 'false', 'Used to enable IPV6 within the site values file when set to true')
        stringParam('INGRESS_IP', 'default', 'INGRESS IP')
        stringParam('INGRESS_CLASS', 'default', 'ICCR ingress class name')
        stringParam('VNFLCM_SERVICE_IP', '0.0.0.0', 'LB IP for the VNF LCM service')
        stringParam('EO_CM_IP', 'default', 'EO CM IP')
        stringParam('EO_CM_ESA_IP', 'default', 'EO CM ESA IP')
        stringParam('FH_SNMP_ALARM_IP', 'default', 'LB IP for FH SNMP Alarm Provider')
        stringParam('ENV_CONFIG_FILE', 'default', 'Can be used to specify the environment configuration file which has specific details only for the environment under test')

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.REPOSITORY_PARAMETERS))
        stringParam('GERRIT_BRANCH', Defaults.DEFAULT_BRANCH, 'Please specify branch for execution.')
        stringParam('GERRIT_REFSPEC', 'refs/heads/${GERRIT_BRANCH}', "Please use for running from commit, example 'refs/changes/43/7079843/1' ")

        parameterSeparatorDefinition(Defaults.getSeparatorParams(Defaults.OPTIONS))
        stringParam('DOWNLOAD_CSARS', 'false', 'When set to true the script will try to download the officially Released CSARs relation to the version of the applications within the helmfile being deployed.')
        stringParam('USE_DM_PREPARE', 'true', 'Set to true to use the Deployment Manager function \"prepare\" to generate the site values file')
        stringParam('USE_SKIP_IMAGE_PUSH', 'false', 'Set to true to use the Deployment Manager parameter "--skip-image-check-push" in case an image push is done in advance. If false will deploy without the "--skip-image-check-push" parameter')
        stringParam('USE_SKIP_UPGRADE_FOR_UNCHANGED_RELEASES', 'false', 'Set to true to use the Deployment Manager parameter "--skip-upgrade-for-unchanged-releases" to skip helm upgrades for helm releases whose versions and values have not changed. If false will deploy without the "--skip-upgrade-for-unchanged-releases" parameter')
        stringParam('COLLECT_LOGS', 'true', 'If set to "true" (by default) - logs will be collected. If false - will not collect logs.')
        stringParam('COLLECT_LOGS_WITH_DM', 'false', 'If set to "false" (by default) - logs will be collected by ADP logs collection script. If true - with deployment-manager tool.')
        stringParam('DDP_AUTO_UPLOAD', 'false', 'Set it to true when enabling the DDP auto upload and also need to add the DDP instance details into ENV_CONFIG_FILE and SITE_VALUES_OVERRIDE_FILE')
        stringParam('VERBOSITY', '3', 'Verbosity can be from 0 to 4. Default is 3. Set to 4 if debug needed')
        choiceParam('DM_LOG_LEVEL', Defaults.dm_log_levels, 'Provide log level for deployment manager logger. By default INFO level will used')
  }

        definition {
                cps {
                    script(readFileFromWorkspace(Defaults.GR_SWITCHOVER_PATH + 'eo_gr_switchover.Jenkinsfile'))
                    sandbox()
                }
            }

        logRotator(50, 50)
    }
}