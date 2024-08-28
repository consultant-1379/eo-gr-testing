package eo_gr.defaults

class Defaults {
    static DEFAULT_PREFIX = 'eo-gr'
    static PROJECT_NAME = 'eo-gr-testing'

    static final String TEST_FRAMEWORK_GIT_REPO = '${GERRIT_CENTRAL_HTTP}/OSS/EO-Parent/com.ericsson.oss.orchestration.eo.testware/eo-gr-testing'
    static final String AM_INTEGRATION_CHARTS_REPO = '${GERRIT_CENTRAL_HTTP}/OSS/com.ericsson.orchestration.mgmt/am-integration-charts'
    static final String EO_INTEGRATION_CI_REPO = '${GERRIT_CENTRAL_HTTP}/OSS/com.ericsson.oss.orchestration.eo/eo-integration-ci'
    static final String EO_GR_REPO_GERRIT_GITILES_LINK = '${GERRIT_CENTRAL_HTTP}/plugins/gitiles/OSS/EO-Parent/com.ericsson.oss.orchestration.eo.testware/eo-gr-testing/+/master'
    static final String TEST_FRAMEWORK_GIT_PROJECT_NAME = 'OSS/EO-Parent/com.ericsson.oss.orchestration.eo.testware/eo-gr-testing'
    static final String JENKINS_URL = 'https://fem1s11-eiffel052.eiffel.gic.ericsson.se:8443'

    static final String EO_INSTALL = 'eo-install'
    static final String DEFAULT_BRANCH = 'master'
    static final String ANY_BRANCH_REG = '^.*$'
    static final String ENV_PROPERTIES_FILE = '/proj/eiffel052_config_fem1s11/dawn/env.properties'
    static PYTHON_PATH = '/usr/local/bin/python3.10'
    static final String DEFAULT_RV_PASSIVE_SITE = 'ci480'
    static final String DEFAULT_APPSTAGING_PASSIVE_SITE = 'flexi28723'
    static final String DEFAULT_UPGRADE_PASSIVE_SITE = 'c16c022'

    static rv_env_list = ['ci476', 'ci480', 'c16a033', 'c16c022', 'nfvi-2', 'nfvi-3', 'c16a026', 'c11a1', 'c16c1']
    static rv_env_list_passive_site_default = Defaults.get_env_list_with_passive_site_default(rv_env_list, Defaults.DEFAULT_RV_PASSIVE_SITE)
    static rv_upgrade_env_list = ['c16a033', 'c16c022', 'ci476', 'ci480', 'nfvi-2', 'nfvi-3', 'c16a026', 'c11a1', 'c16c1']
    static rv_upgrade_env_list_passive_site_default = Defaults.get_env_list_with_passive_site_default(rv_env_list, Defaults.DEFAULT_UPGRADE_PASSIVE_SITE)
    static app_staging_env_list = ['flexi28594', 'flexi28723', 'flexi35650_gr1', 'flexi35660_gr1', 'flexi35650_gr2', 'flexi35660_gr2', 'flexi35650_gr3', 'flexi35660_gr3', 'c16c027', 'c16c029', 'c16b027']
    static app_staging_env_list_passive_site_default = Defaults.get_env_list_with_passive_site_default(app_staging_env_list, Defaults.DEFAULT_APPSTAGING_PASSIVE_SITE)
    static all_env_list = Defaults.rv_env_list + Defaults.app_staging_env_list
    static all_env_list_passive_site_default = Defaults.get_env_list_with_passive_site_default(all_env_list, Defaults.DEFAULT_RV_PASSIVE_SITE)
    static all_env_list_empty_default = Defaults.get_env_list_with_empty_elm(Defaults.all_env_list)

    static cluster_roles = ['PRIMARY', 'SECONDARY']
    static switchover_test_rule_list = ['run-switchover', 'run-switchover-while-active-site-unavailable', 'run-switchover-after-active-site-become-available']
    static vim_list = ['rdo08', 'rdo14', 'c7b23', 'c14avim2']
    static log_levels = ['debug', 'info']
    static dm_log_levels = ['INFO', 'DEBUG', 'CRITICAL', 'ERROR', 'WARNING']

    static final String SLAVE_1 = 'dawn_slave_1_new'
    static final String DOCKER_SLAVE_1 = 'dawn_docker_slave_1_new'
    static final String DOCKER_SLAVE_LABEL_FEM_5 = 'evo_docker_engine_gic'

    static final String TEST_REPORT_DIR = 'pytest_reports'
    static final String PIPELINES = 'pipelines/'
    static final String TEST_REPORT_NAME = 'report.html'
    static final String TEST_REPORT_TEMPLATE = 'tests/reporter_templates/report_template.html'
    static final String EO_GR_PATH = 'ci/jenkins/src/main/groovy/eo_gr/'
    static final String PIPELINES_PATH = Defaults.EO_GR_PATH + Defaults.PIPELINES
    static final String GR_BASIC_PATH = Defaults.EO_GR_PATH + 'gr_basic/' + Defaults.PIPELINES
    static final String GR_ROBUSTNESS_PATH = Defaults.EO_GR_PATH + 'gr_robustness/' + Defaults.PIPELINES
    static final String GR_UPGRADE_PATH = Defaults.EO_GR_PATH + 'gr_upgrade/' + Defaults.PIPELINES
    static final String GR_SWITCHOVER_PATH = Defaults.EO_GR_PATH + 'gr_switchover/' + Defaults.PIPELINES
    static final String DOCKER_SECRET_AUTH_CONFIG = 'cloudman-docker-auth-config'
    static final String DOCKER_AUTH_CREDS = 'cloudman-user-creds'
    static final String TEST_DOCKER_IMAGE = 'armdocker.rnd.ericsson.se/proj-eo-gr-testing/eo-gr-test-image'
    static final String CODE_CHECK_SCRIPT = 'ci/scripts/pylint_pycodestyle_black_check.sh'
    static final String DOCKERFILE_PATH = 'resources/eo-gr-test-image/Dockerfile'
    static final String ENV_PROPERTY_FILE = 'env.properties'

    static final String SECTION_HEADER_STYLE_CSS = 'color: white; font-weight: bold; background: #39505f; font-family: Roboto, sans-serif !important; padding: 5px; text-align: center; width: 25%;'
    static final String SEPARATOR_STYLE_CSS = 'border: 0; background: #999;'
    static final String ENVIRONMENT_PARAMETERS = 'ENVIRONMENT PARAMETERS'
    static final String REPOSITORY_PARAMETERS = 'REPOSITORY PARAMETERS'
    static final String OPTIONS = 'OPTIONS'
    static final String TEST_PARAMETERS = 'TEST_PARAMETERS'
    static final String JOB_TIMEOUT = '180'
    // eo-install:
    static controllersList = ["eo_node_ie", "eo_node_se", "ieatflo13a-15", "atvts3430", "atvts3491"]
    static final String ECCD_RELEASE_LINK = "https://arm.sero.gic.ericsson.se/artifactory/proj-erikube-generic-local/erikube/releases/2.26.0/CXP9043015/CXP9043015R2B.tgz"

    // parameters descriptions
    static final String TEST_TAG_DESCRIPTION_WITH_PYTEST_INI_LINK = """Please provide test mark. Existing markers can be found <a href="${Defaults.EO_GR_REPO_GERRIT_GITILES_LINK}/pytest.ini#markers:text:~:text=markers">HERE</a>"""


// utils regions

    static def getSeparatorParams(String separatorName) {
        // used for parameterSeparatorDefinition plugin
        return {
            name(separatorName)
            separatorStyle(Defaults.SEPARATOR_STYLE_CSS)
            sectionHeader(separatorName)
            sectionHeaderStyle(Defaults.SECTION_HEADER_STYLE_CSS)
        }
    }

    /**
    String msg - job descritption message
    Seed job parameters:
        String isFromRefSpec - flag that defines if job was created from custom
        String refSpec - refspecs from witch job was created
        String branch - branch from witch job was created
    */
    static def description(String msg, String isFromRefSpec=null, String refSpec=null, String branch=null) {
        String seedJobMsg;
        if (isFromRefSpec == "true") {
            seedJobMsg = "Job builded from custom refspec: <span style='color: #1417D3;'>${refSpec}</span> on branch <span style='color: #1417D3;'>${branch}</span>"
        } else if (isFromRefSpec == "false") {
            seedJobMsg = "Job builded from <span style='color: #1417D3;'>${branch}</span> branch"
        } else {
            seedJobMsg = "No information about seed job. Expected fields are not provided."
        }
		return """
        <h4><font color="red">WARNING: Manual modifications will be overwritten by seed job</h4>
        <div>
            The source code for this job can be found:
            <a href="${Defaults.EO_GR_REPO_GERRIT_GITILES_LINK}/ci/jenkins/src/main/groovy/eo_gr">here</a>
        </div>
        <br>
        <h2>${msg}</h2>
        <br>
        <div>
            <h3>${seedJobMsg}</h3>
            The last build of Seed job located:
            <a href="https://fem5s11-eiffel052.eiffel.gic.ericsson.se:8443/jenkins/view/EO-GR/view/Utils/job/eo-gr-dsl-jobs-generator/lastBuild">here</a>
        </div>
		"""
    }

    static def get_env_list_with_empty_elm(List<String> list_of_envs) {
        def env_list = list_of_envs.clone()
        env_list.add(0, "");
        return env_list
    }

    static def get_env_list_with_passive_site_default(List<String> list_of_envs, String passive_env) {
        def env_list = list_of_envs.clone() - passive_env
        env_list.add(0, passive_env)
        return env_list
    }

    static def is_rv_setup() {
        String RV_SETUP_LIST = Defaults.rv_env_list.join(' ')
        return """
        RV_ENV=\$(echo ${RV_SETUP_LIST} | grep -wo \$ACTIVE_SITE) || true

        if [ -z \$RV_ENV ]; then
            RV_SETUP=false
        else
            RV_SETUP=true
        fi
        """
    }


    static def check_required_params(String params){
        return """
        set +x
        echo "\n----- Check Required Parameters -----\n"
        echo "List parameters to check ${params}"

        empty_params=""

        while read -d, -r pair; do
          IFS='=' read -r key val <<<"\$pair"
          if [ -z \$val ]; then
              echo "ERROR: Required parameter \$key are not specified"
              empty_params+="\$key,"
          fi
        done <<<"${params},"

        if [ \$empty_params != "" ]; then
            exit 1
        fi
        """
    }

// python and git region

    static final String pullFromCommitShellCommand = '''
    if [ "$GERRIT_REFSPEC" != "refs/heads/$GERRIT_BRANCH" ]; then
        echo -e "\n -------- Installing git changes from provided refspec -------- \n"
        git fetch $GIT_REPO $GERRIT_REFSPEC && git checkout FETCH_HEAD
    fi
    '''

//  docker region

    static def pythonVirtualEnvAndInstallDependenciesSetUpInDocker(
        String dockerImage, String venvDir=".", String requirementsFile="requirements.txt"
            ) {
        return """
        set +x
        echo -e "\n -------- Setup venv and install Python dependencies from ${requirementsFile} via docker container -------- \n"

        docker run --init --rm -v \$(pwd):/workdir --workdir /workdir/ -v /var/run/docker.sock:/var/run/docker.sock \
                ${dockerImage} \
                /bin/bash -c \
                    "python -V && \
                    pip -V && \
                    docker -v && \
                    cd ${venvDir}
                    python -m venv venv && \
                    source venv/bin/activate && \
                    pip install -r${requirementsFile} --use-pep517"
        """
    }

    static def defineDnsIpAndDnsFlagEnvVars(String dockerImage, String envName) {
    return """
        set +x
        echo "USE_LOCAL_DNS: \${USE_LOCAL_DNS}"

        if [ "\${USE_LOCAL_DNS}" == true ]; then
                echo "Job will run with Local DNS Server settings"
                echo "Defining DNS Server IP for ${envName}..."

                docker run --init --rm -v \$(pwd):/workdir --workdir /workdir/ -v /var/run/docker.sock:/var/run/docker.sock \
                    --env ACTIVE_SITE=${envName} \
                    --env DOCKER_CONFIG=\${DOCKER_CONFIG_JSON} \
                    --env PYTHONPATH=/workdir \
                    ${dockerImage} \
                        /bin/bash -c "source venv/bin/activate && \
                        python util_scripts/gr/create_env_properties_file.py"

                echo "Content of ${Defaults.ENV_PROPERTY_FILE}:" && cat ${Defaults.ENV_PROPERTY_FILE}
        else
            echo "Job will run with Global DNS settings..."
            echo "DNS_FLAG=" > ${Defaults.ENV_PROPERTY_FILE}
        fi
    """
    }

    static final String DOCKER_CONFIG_DIR = '$WORKSPACE/.docker'
    static final String DOCKER_CONFIG_JSON = Defaults.DOCKER_CONFIG_DIR + '/config.json'

    static def install_docker_config_json() {
        return "install -m 600 -D \${DOCKER_AUTH_CONFIG} \${DOCKER_CONFIG_JSON}"
    }

    static def clean_up_dm_logs_from_eo_node(String dockerImage) {
        return """
        echo -e "\n-------- Cleaning up Deployment Manager logs from the EO Node --------\n"

        docker run --init --rm -v \$(pwd):/workdir --workdir /workdir/ -v /var/run/docker.sock:/var/run/docker.sock \
            --env ACTIVE_SITE=\${ENV} \
            --env DOCKER_CONFIG=\${DOCKER_CONFIG_JSON} \
            --env PYTHONPATH=/workdir \
                ${dockerImage} \
                    /bin/bash -c "source venv/bin/activate && \
                    python util_scripts/logging_scripts/collect_all_workdir_logs_script.py --clean-up"
        echo -e "\n-------- Cleaning up DM logs is completed successfully  --------\n"
       """
    }

    static def collect_dm_logs_from_eo_node(String dockerImage) {
        return """
        echo -e "\n-------- Download Deployment Manager logs from EO Node --------\n"

        docker run --init --rm -v \$(pwd):/workdir --workdir /workdir/ -v /var/run/docker.sock:/var/run/docker.sock \
            --env ACTIVE_SITE=\${ENV} \
            --env DOCKER_CONFIG=\${DOCKER_CONFIG_JSON} \
            --env PYTHONPATH=/workdir \
                ${dockerImage} \
                    /bin/bash -c "source venv/bin/activate && \
                    python util_scripts/logging_scripts/collect_all_workdir_logs_script.py"

        echo "--------------- Logs should be available in Build Artifacts ---------------"
        """
    }

    static def set_bur_orchestrator_log_level(String dockerImage) {
        return """
        echo -e "\n-------- Set debug log level for eric-gr-bur-orchestrator deployment --------\n"

        docker run --init --rm -v \$(pwd):/workdir --workdir /workdir/ -v /var/run/docker.sock:/var/run/docker.sock \
            --env ACTIVE_SITE=\${ENV} \
            --env DOCKER_CONFIG=\${DOCKER_CONFIG_JSON} \
            --env PYTHONPATH=/workdir \
                ${dockerImage} \
                    /bin/bash -c "source venv/bin/activate && \
                    python util_scripts/logging_scripts/set_bur_orchestrator_log_level_script.py"
        """
    }

    static def set_up_eo_install_submodule(String branchName, String refSpec) {
        String EO_INSTALL = Defaults.EO_INSTALL
        return """
        echo -e "\n ------ Getting ${EO_INSTALL} submodule ------- \n"
        git submodule update --init --remote --recursive ${EO_INSTALL}
        if [ ${branchName} != "master" ]; then
            cd ./${EO_INSTALL} && git checkout ${branchName}
            cd ..
        fi

        if [ -n "${refSpec}" ]; then
            echo "Installing git changes from provided gerrit refspec for ${EO_INSTALL} repo"
            cd ./${EO_INSTALL} && \
            git fetch origin ${refSpec} && git checkout FETCH_HEAD
        fi
        """
    }

    static def remove_stuck_volumes(String rmStuckVolumesFlag, String envName){
        return """
        if [ ${rmStuckVolumesFlag} == true ]; then
            echo "REMOVE_STUCK_VOLUMES parameter is ENABLED"
            echo "Removing all stuck cluster volumes"
            echo -e "\n-------- Cleaning up all remaining and stuck VIM zone volumes --------\n"
            docker run --init --rm -v \$(pwd):/workdir --workdir /workdir/ -v /var/run/docker.sock:/var/run/docker.sock \
                --env ACTIVE_SITE=${envName}\
                --env PYTHONPATH=/workdir \
                \${TEST_DOCKER_IMAGE} \
                /bin/bash -c "source venv/bin/activate && python util_scripts/common/persistent_volume_cleaner.py"
        fi
        """
    }

    static def set_global_registry_env_var(String dockerImage, String envName){
        return """
        echo -e "\n-------- Setting up GLOBAL_REGISTRY environment variable --------\n"

        docker run --init --rm -v \$(pwd):/workdir --workdir /workdir/ -v /var/run/docker.sock:/var/run/docker.sock \
            --env ACTIVE_SITE=${envName} \
            --env PYTHONPATH=/workdir \
            ${dockerImage} \
                /bin/bash -c "source venv/bin/activate && \
                python util_scripts/gr/create_env_properties_file.py --registry"

        echo "Content of ${Defaults.ENV_PROPERTY_FILE}:" && cat ${Defaults.ENV_PROPERTY_FILE}
        """
    }
}
