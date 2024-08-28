nestedView('EO-GR') {
    views {
        sectionedView('Utils') {
            sections {
                listView() {
                    name('Seed Job')
                    description('View for project EO-GR-TESTING. All jobs related to eo-gr-testing')
                    jobs {
                        name('eo-gr-dsl-jobs-generator')
                    }
                    columns {
                        status()
                        weather()
                        name()
                        lastSuccess()
                        lastFailure()
                        lastDuration()
                        buildButton()
                    }
                }
                listView() {
                    name('EO GR Common RV Stages')
                    description('Pipelines with common environment and test activities related to RV setup')
                    jobs {
                        name('eo-gr-clean-up-test-assets-and-dns')
                        name('eo-gr-deploy-and-configure-rv-environments-job')
                    }
                    columns {
                        status()
                        weather()
                        name()
                        lastSuccess()
                        lastDuration()
                        buildButton()
                    }
                }
                listView() {
                    name('Code Quality Check Jobs')
                    description('Jobs for running code quality checks on code.')
                    jobs {
                        name('eo-gr-code-quality-check-pycodestyle-pylint-job')
                    }
                    columns {
                        status()
                        weather()
                        name()
                        lastSuccess()
                        lastFailure()
                        lastDuration()
                        buildButton()
                    }
                }
                listView() {
                    name('Utility Jobs')
                    description('Jobs that automate routine tasks and makes life easier')
                    jobs {
                        name('eo-gr-clean-up-registry-job')
                        name('eo-gr-clean-up-vim-job')
                        name('eo-gr-copy-kms-key-job')
                        name('eo-gr-collecting-logs-job')
                        name('eo-gr-create-alarm-secret-job')
                        name('eo-gr-create-new-evnfm-user-job')
                        name('eo-gr-delete-cnf-namespaces-job')
                        name('eo-gr-delete-namespace-and-pv-cleanup-job')
                        name('eo-gr-deploy-bur-sftp-server-job')
                        name('eo-gr-deploy-dns-server-job')
                        name('eo-gr-install-cvnfm-certificates-job')
                        name('eo-gr-install-site-job')
                        name('eo-gr-upgrade-site-job')
                        name('eo-gr-publish-test-image-job')
                        name('eo-gr-remove-dns-server-job')
                        name('eo-gr-update-superuser-password-job')
                    }
                    columns {
                        status()
                        weather()
                        name()
                        lastSuccess()
                        lastFailure()
                        lastDuration()
                        buildButton()
                    }
                }
                listView() {
                    name('Cluster Jobs')
                    description('Jobs that automate cluster installation and post-installation activities')
                    jobs {
                        regex('eo-gr-.*cluster.*')
                    }
                    columns {
                        status()
                        weather()
                        name()
                        lastSuccess()
                        lastFailure()
                        lastDuration()
                        buildButton()
                    }
                }
            }
        }
        sectionedView('Tests') {
            sections {
                listView() {
                    name('Geographical Redundancy Test Jobs')
                    description('Jobs for running GR tests.')
                    jobs {
                        regex('eo-gr-tests.*')
                    }
                    columns {
                        status()
                        weather()
                        name()
                        lastSuccess()
                        lastDuration()
                        buildButton()
                    }
                }
                listView() {
                    name('AppStaging Switchover Pipelines')
                    description('Pipelines related to GR testing')
                    jobs {
                        regex('eo-gr-switchover-pipeline.*')
                    }
                    columns {
                        status()
                        weather()
                        name()
                        lastSuccess()
                        lastDuration()
                        buildButton()
                    }
                }
                listView() {
                    name('EO GR Basic Scenarios')
                    description('Pipelines related to the RV EO GR Basic scenarios')
                    jobs {
                        regex('eo-gr-rv-verify-.*basic-scenario.*')
                    }
                    columns {
                        status()
                        weather()
                        name()
                        lastSuccess()
                        lastDuration()
                        buildButton()
                    }
                }
                listView() {
                    name('EO GR Upgrade Scenarios')
                    description('Pipelines related to the RV EO GR Upgrade scenarios')
                    jobs {
                        regex('eo-gr-rv-verify-.*upgrade-scenario.*')
                    }
                    columns {
                        status()
                        weather()
                        name()
                        lastSuccess()
                        lastDuration()
                        buildButton()
                    }
                }
                listView() {
                    name('EO GR Robustness Scenarios')
                    description('Pipelines related to the RV EO GR Robustness scenarios')
                    jobs {
                        regex('eo-gr-rv-verify-.*robustness-scenario.*')
                    }
                    columns {
                        status()
                        weather()
                        name()
                        lastSuccess()
                        lastDuration()
                        buildButton()
                    }
                }
            }
        }
    }
}
