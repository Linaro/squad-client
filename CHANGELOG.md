# 0.5

This release includes many new additions and bug fixes to
work in sync with SQUAD.

The example build report template has been improved and anonymized
for genereric use.

A new command `./manage.py submit` has been added to allow
users to submit results to SQUAD backend by simply passing
results files. It still missing on attachments but will be
added in near future.
work in sync with SQUAD.

The example build report template has been improved and anonymized
for genereric use.

A new command `./manage.py submit` has been added to allow
users to submit results to SQUAD backend by simply passing
results files. It still missing on attachments but will be
added in near future.

Better testing has been implemeted. There's a squad instance
running on the fly, meaning tests are run against a real
squad instance, instead of basic mocking.

Complete list of changes below:

* commands:
  * add submit results
  * shell: add missing import
  * submit: fix bugs
  * test: return test result code
* core:
  * api: add helpful message on 500 errors
  * api: improve credentials handling
  * models: fix small bugs and add helpful messages
  * models: update metricthreshold to use env
  * models: use testrun status endpoint
* examples:
  * build_report: add free text form from params
  * rename schneider report
  * schneider_template: add links to tests
  * schneider_template: anonymize template
  * schneider_template: fix tabs and tr tags
* manage:
  * configure basic logging
  * exit with proper exit code
  * handle credentials before subcommands
  * make squad-host mandatory in environment
* tests:
  * add flake8 check
  * add tests for submit command
  * remove configurarion of the api before running tests
  * remove test_squad_service.py to speed up testing
  * start local squad server to support testing
  * test_api: add auth test
* misc:
  * fix the import paths for some docs and examples
  * reports: improve generic reports
  * setup.py: make squad-client program name shorter
  * shortcuts: add submit_results shortcut
  * travis: add travis file

# 0.4

This release improves basic report generation for Schneider project

# 0.3

This release make changes Dockerfile to make it better to
run squad-client in docker.

# 0.2

This release automates build of squad-client docker image
and pushes it to docker hub.

Complete list of changes below:
* release: build and push docker image as well

# 0.1

Initial Squad-Client release
