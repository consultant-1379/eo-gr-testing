// ###
// Common configuration file for all Jenkins-pipeline scripts
// ###

TEST_FRAMEWORK_GIT_REPO = '${GERRIT_CENTRAL_HTTP}/OSS/EO-Parent/com.ericsson.oss.orchestration.eo.testware/eo-gr-testing'
DEFAULT_BRANCH = 'master'
ENVS = ['ci476', 'ci480', 'c16a033', 'c16c022']
DEFAULT_PREFIX = 'eo-gr'
SLAVE_1 = 'dawn_slave_1_new'
DOCKER_SLAVE_1 = 'dawn_docker_slave_1_new'
EO_GR_LABEL = 'eo_gr'

return this;
