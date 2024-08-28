# Overview

This project contains the test automation framework with test cases and jobs for EO Geographical Redundancy testing by
EO-GR-FLOW-TEST pipeline, included in AppStaging and RV teams daily workflows.
The repository provides two options for installing the environment:
   1. For App Staging pipelines
   2. For RV or customer-like pipelines
Please refer to the dedicated Confluence space for more detailed information on each of the pipelines:
https://confluence-oss.seli.wh.rnd.internal.ericsson.com/display/PAO/Dawn+%7C+EO+GR?src=contextnavpagetreemode

## Requirements

* **Python >= 3.12.2**

## Project structure
```
Project structure consists of the following directories in the project root:

am-integration-charts - a folder to connect 'am-integration-chart' repository as Git submodule
apps                  - business logic layer to work with EO applications functionality
bob                   - a folder to connect 'adp-cicd/bob' repo as a submodule
ci                    - Jenkins jobs/pipelines/views related code; Spinnaker pipelines configuration backup
config                - test environments and test data configurations 
eo-install            - a folder to connect 'eo-install' repository as Git submodule
eo-integration-ci     - a folder to connect 'eo-integration-ci' repository as Git submodule
libs                  - framework utilities and helpers, e.g. constants, custom exceptions, logger, etc
oss-intgration-ci     - a folder to connect 'oss-integration-ci' repo as a submodule
resources             - different files, required for EO GR tests execution 
rulesets              - sets of bob tasks, involved in different test suites
tests                 - the automated EO GR test scenarios
util_scripts          - a package containing individual utility scripts that can function independently
```

## In-house repositories dependencies

This project dependent on the below in-house (internal teams owned) repositories:
1. 'core_test_libs' repository:
   1. context: set of libraries to interact with EO API
   2. link: https://gerrit.ericsson.se/#/admin/projects/OSS/com.ericsson.oss.orchestration.eo.testware/eo_gat_and_core_test_libs
   3. setup approach in the current repo: set as a dependency, stated in requirements.txt
   4. aim to use in the current repo: all the logic of EO API calls, triggered from EO GR tests, 
   are implemented in core_test_libs
2. 'bob' repository:
   1. context: utility to run commands in a shell or in a docker container; commands to run are implemented as tasks
   in a rulesets; for more information navigate to the bob repo README
   2. link: https://gerrit.ericsson.se/#/admin/projects/adp-cicd/bob
   3. setup approach in the current repo: added as a submodule via git submodule init
   4. aim to use in the current repo: bob rules, which used in ci/jenkins/src/main/groovy/eo_gr/pipelines, require bob
   repo access during their execution
3. oss-integration-ci repository:
   1. context: common service for CI of enormous OSS projects; 
   2. link: https://gerrit.ericsson.se/#/admin/projects/OSS/com.ericsson.oss.aeonic/oss-integration-ci	 	
   3. setup approach in the current repo: added as a submodule via git submodule init
   4. aim to use in the current repo:
      1. several EO-GR-FLOW-TEST pipeline stages code is implemented in oss-integration-ci/ci
      2. environment configs for those several stages are placed in oss-integration-ci/honeypots/pooling/environments
      3. environment certificates for those several stages are placed in oss-integration-ci/RV/ci/environment
4. 'am-integration-charts' repository:
   1. context: a repository that stores EVNFM chart and testing scripts
   2. link: https://gerrit.ericsson.se/#/admin/projects/OSS/com.ericsson.orchestration.mgmt/am-integration-charts
   3. setup approach in the current repo: added as a submodule via git submodule init
   4. it is used specifically for obtaining Scripts/eo-evnfm/certificate_management.py file that helps to install 
   certificates for the signed CNF packages
5. 'eo-install' repository:
   1. context: the project contains automation script for EVNFM, cCM, AAT, CAPO, and ECCD installation and upgrade
   2. link: https://gerrit.ericsson.se/#/admin/projects/rv/eo_automation/eo-install
   3. setup approach in the current repo: added as a submodule via git submodule init
   4. aims to use in the current repo:
      1. it is the place where stored EO certificates for RV (customer-like type of installation) environments
      2. provides functionality for RV environment installation
6. 'eo-integration-ci' repository:
   1. context: a repository that stores CI infrastructure, including Jenkins and Spinnaker files, site values,
   and certificates, across multiple environments
   2. link: https://gerrit.ericsson.se/#/admin/projects/OSS/com.ericsson.oss.orchestration.eo/eo-integration-ci
   3. setup approach in the current repo: added as a submodule via git submodule init
   4. it stores App Staging environment-specific cluster Intermediate certificates which are required for the signed CNF
   certificates installation

## Project Setup (Ubuntu)

1. Install Python (Version >= 3.12.2).
2. Install "python3-pip"
3. Clone this project either via ssh or via https with commit-msg hook 
4. Ensure that the linux package "libffi" is installed
    1. Verify whether package is installed with commands: `'sudo apt list | grep libffi-dev'` and `'whereis libffi'`
    2. if not installed, install with command: `'sudo apt-get install libffi-dev'`
5. From the project root directory run the setup script `python3 setup.py`
6. Add PYTHONPATH environment variable to your pytest run configurations in IDE. The value of the variable should be the
   project root
7. As the working directory apply the project root as well in your pytest run configurations in IDE


## Project Setup (Windows)

1. Install Python (Version >= 3.12.2) from https://www.python.org/downloads/.
2. Make sure to add location of the python.exe to the PATH in System variables.
3. Clone this project either via ssh or via https with commit-msg hook 
4. From the project root directory run the setup script `python setup.py`
5. Add PYTHONPATH environment variable to your pytest run configurations in IDE. The value of the variable should be the
   project root.
6. As the working directory apply the project root as well in your pytest run configurations in IDE.

## Environment Configuration

Before any script running from eo-gr-testing repository, environment configurations should be added. Please note that 
the repository contains multiple environment configurations types, all of them are stored in 'config' folder:
 - envs: configurations of EO deployments, required for EO GR, upgrade, EO functional (CVNFM, VMVNFM operations) testing
 - sftp_dns: configurations, required for SFTP or DNS server deploy
 - vims: configurations of existing VIM zones, required for VMVNFM operations testing
 - artefacts: configuration of used in testing test artefacts, e.g., CNF packages, VNF packages details
 - commom_config: configuration of used in testing other than packages artefacts: workflow, JFrog repository, etc

In order to add environment to the repository, add environment file here: config/envs/<team_name_directory>/env_<
environment_name>.yaml
Please note that the repository contains multiple environment configurations types. Here are their templates:
 - example_gr_template.yaml - the configuration that is customized specifically for EO GR environments
 - example_upgrade_template.yaml - the configuration that is customized specifically for upgrade test environments

In order to use the functionality of GR that required SFTP and DNS dependencies, please add shared config file
with SFTP and DNS configuration here: config/sftp_and_dns<environment_name>.yaml, example template: config/sftp_and_dns/templates/example_template.yaml




## Test Configuration

Expected parameters when executing GAT test cases via pytest:

| Name                            | Default value |  Mandatory  | Description                                                                                                                                             |
|---------------------------------|:-------------:|:-----------:|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| ACTIVE_SITE                     |     empty     |   &check;   | Name of the GR Active (Primary, Site A) Site the test is to be run on.                                                                                  |
| PASSIVE_SITE                    |     empty     | &check; / - | Name of the GR Passive (Secondary, Standby, Site B) Site. Mandatory for GR tests / Optional for Non GR tests and util scripts.                          |
| VIM                             |     empty     |      -      | Name of the VIM the system should use for executing the tests.                                                                                          |
| DNS_SERVER_IP                   |     empty     |      -      | DNS server ip, required for DNS switching befor a switchover                                                                                            |
| LOG_LEVEL                       |     DEBUG     |      -      | Variable that decides what logging level should be set.                                                                                                 |
| RANDOMIZE_VNFD                  |     False     |      -      | Variable that used only for internal usage. Use only for debugging.                                                                                     |
| OVERRIDE                        |     empty     |      -      | Overriding parameters specified in config folder.                                                                                                       |
| ADDITIONAL_PARAM_FOR_CHANGE_PKG |     False     |      -      | Flag that defines if additionalParams will used for 'change package' CNF package operation.                                                             |
| PRETTY_API_LOGS                 |     False     |      -      | Flag that defines if API logs to be output in pretty format.                                                                                            |
| RESOURCES_CLEAN_UP              |     False     |      -      | Variable that decides if resources should be cleaned up on the last stage                                                                               |
| GR_STAGE_SHARED_NAME            | default_name  |      -      | Variable represents the unique string that shared between the stages. Be sure that this string is same for each stage                                   |
| EO_VERSIONS_COLLECTION          |     True      |      -      | Flag that defines if need to collect EO applications versions from provided ENVIRONMENT and add them to pytest-report                                   |
| DEPLOYMENT_MANAGER_DOCKER_IMAGE |     empty     |      -      | Deployment Manager image that was used for sites installation. Please use this flag for non RV_SETUP only                                               |
| DEPLOYMENT_MANAGER_VERSION      |     empty     |      -      | Version of Deployment Manager that was used for sites installation. Please use this flag for RV_SETUP only                                              |
| RV_SETUP                        |     false     |      -      | Flag that defines if RV setup required. If it set to true all GR commands will run from working dir on EO RV Node else they will run from Jenkins slave |
| DM_LOG_LEVEL                    |     INFO      |      -      | Variable that decides what logging level should be set for Deployment Manager commands. Possible levels: CRITICAL, ERROR, WARNING, INFO, DEBUG          |
| DOCKER_CONFIG                   |     empty     |      -      | Path to the Docker config json file required for authentication on the artifactory                                                                      |                                                    |
| ENABLE_VMVNFM_DEBUG_LOG_LEVEL   |     False     |      -      | Flag that enables debug log level on VMVNFM side. By default info level is used.                                                                        |                                                    |

**Basic rules for parameters OVERRIDE operation:**<br/>

- The parameters should be separated by # symbol:
    - *Eg: COMMON_CONFIG_KEY=0000.0000#COMMON_CONFIG_ANOTHER_KEY=test*
- The config/artifacts.yaml or any other has nested structure and parameters path should be separated by | symbol:
    - *Eg: artefacts|package1_name|package_path=package.csar#artefacts|package1_name|id=CNF-12*

## Local Test Execution
Before launching tests please make sure you have successfully completed all steps described in the Project Setup section

For configuring Run/Debug pytest execution in your IDE please do the following:
1. Specify a path to the test package as a target
2. Set eo-gr-testing as a working directory
3. Add required environment variables, e.g. ACTIVE_SITE, PASSIVE_SITE, VIM, etc
4. Add content and source roots to PYTHONPATH
5. Specify a package path or a test mark of the desired test using '-m' option, e.g. '-m vmvnfm_phase_A'

Please note that tests and scripts that call docker locally are not compatible with Windows
Please note that DNS switching on Windows machines differs from DNS switching on Linux:
- on Windows machines DNS switching is emmulated by editing .\Windows\System32\drivers\etc\hosts
- on Linux machines execute tests inside a docker container, run with '--dns' option

## Test image creation

- All EO-GR Jenkins jobs require test docker image that includes appropriate Python version and other dependencies.
- 'armdocker.rnd.ericsson.se/proj-eo-gr-testing/eo-gr-test-image' image with 'master' tag that is built
  continuously from 'master' branch is used by default.
- Manual image build is required for an any branch.
- Use 'eo-gr-publish-test-image-job' Jenkins job to build the appropriate image for your branch.