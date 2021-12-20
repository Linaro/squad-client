# 0.24

This 0.23 release allows squad to fetch and push TestRun
metadata.

Complete list of changes going in:
* core/models: handle fetching testrun metadata if there is none
* core/models: fetch testrun metadata from squad

# 0.23.1

This 0.23.1 release fixes a long-running bug that was overwriting
kconfig and download_url metadata, causing lots of confusion when
people tried to cross down info regarding tuxbuilds.

Complete list of changes going in:
* commands: submit_tuxbuild: require download_url in schema
* commands: submit_tuxbuild: avoid extra slash
* submit_tuxbuild: add config file url to the metadata

# 0.23

This 0.23 release changes submit_tuxbuild command so
that it sends kconfig of builds along with other
metadata fields.

Complete list of changes going in:
* submit_tuxbuild: add kconfig as metadata
* dockerfile: remove wkhtmltopdf

# 0.22.1

This 0.22.1 release fixes a bug when adding download_url
into tuxbuild submission.

Complete list of changes going in:
* commands: submit_tuxbuild: use metadata from iterating builds

# 0.22

This 0.22 release makes Project.compare_builds use metrics comparison.

Complete list of changes going in:
* test_shortcuts: assert an error was logged
* shortcuts: make sure the shortcut args match
* all: fetch build comparisons based on metrics

# 0.21

This 0.21 release sends download_url to TuxBuild build
test results. It also fixed differences when dealing with
backend MetricThreshold objects.

A nice feature added in this release is an extra arg
in create-or-update-project command: --thresholds.
That allows users/CI to automatically create necessary
thresholds per project.

Complete list of changes going in:
* commands:
  * create_or_update_project: add --thresholds arg
  * submit_tuxbuild: add downlaod_url to ALLOWED_METADATA
  * submit_tuxbuild: splitup ALLOWED_METADATA
* core: models:
  * add metrics to build
  * add relation between project and metric thresholds
* tests:
  * fixtures: fix fixtures for new versions of squad
  * test_models: fix typo fixed in SQUAD

# 0.20

This 0.20 release used warnings_count of tuxbuild result
file to send as metric to SQUAD.

Complete list of changes going in:
* commands: submit_tuxbuild: send metrics

# 0.19

This 0.19 release adds a command that allow users to
send job requests to SQUAD.

Complete list of changes going in:
* commands: submit-job: submit job requests command

# 0.18.3

This 0.18.3 release fixes a bug submitting TuxBuild results
due to an upstream dependency (jsonschema) update.

Complete list of changes going in:
* submit_tuxbuild: set schema version

# 0.18.2

This 0.18.2 release fixes an issue in Docker that prevented
running containers by calling out /bin/bash

Complete list of changes going in:
* Dockerfile: remove entrypoint to allow /bin/bash to be called out

# 0.18.1

This 0.18.1 release is a quick release on the Docker
image to restore the original entry point to bash
(it was python's console after)

# 0.18

This 0.18 release makes TuxBuild submissions send
build metadata along with build results.

Complete list of changes going in:
* submit_tuxbuild: submit build metadata

# 0.17

This 0.17 release changes the base docker image to Alpine, thus
cutting the image size in half.

Complete list of changes going in:

* Dockerfile: refactor and switch to Alpine based image

# 0.16

This 0.16 release moves request cache activation to
inside SquadApi.configure() so other libs using squad-client
can toggle it on/off.

Complete list of changes going in:

* core: api: configure cache in SquadApi.configure()

# 0.15

This 0.15 release replaces the `version` command by a flag, which
is simpler. The release also improved logging.

Complete list of changes going in:

* commands: add version command
* core:
  * api: check for squad server version
  * api: remove nested endpoints
  * models: cache build tests depending on filters
* logging: centralize all logging config
* manage: remove version command, make it a flag
* misc: use module name for the logger name
* tests: fix tests that need output from manage.py

# 0.14

This 0.14 release makes sure to save project settings. 

SQUAD stopped displaying "project_settings" column because
it contained sensitive information. We removed this attribute
in project class and prevented that saving it as consequence.

# 0.13

This 0.13 release allows comparison on builds that are unfinished

# 0.12

This 0.12 release fixes a bug in submit_tuxbuild command.

Complete list of changes going in:

* tests: test_shortcuts: remove test against project_settings
* commands: submit_tuxbuild: fix key in case of builds with dotted version
* Add some printable representations for a few classes

# 0.11

This 0.11 release improves `build_report` in the example
folder and it should run much faster now.

The release also moves tuxbuild submissions to its own
subcommand.

Complete list of changes going in:

* commands: add a new command for submiting tuxbuild data to squad
* commands: validate a full tuxbuild file instead of just individual builds
* core: add "unit" to Metric attributes
* core: models: avoid loading testrun environment
* examples: build report: fix objects keys
* examples: build_report: improve load time
* shortcuts: improve 'retrieve_build_results' response time
* squad_service: define squad storage folder in /tmp
* utils: add getid utility

# 0.10.1

This 0.10.1 release is a bugfix of previous one, where environment
and build references were missing from Test model

Complete list of changes going in:

* core: models: add environment and build to Test

# 0.10

This 0.10 release adds an significant improvement when fetching
tests of a build. Now there's no need to go through Build's
testruns in order to get tests, it can be done directly just by
calling `build.tests()`. It's supposed to be much quicker than legacy
code.

Complete list of changes going in:

* core: models: add tests endpoint to build
* core: models: do not crash in str() if attribute is missing
* core: models: add missing url attribute
* rename redundant json: tuxbuild_json to tuxbuild only
* squad_client: commands: submit: metadata: allow more types
* squad_client: commands: submit: metadata: update error message

# 0.9.1

This 0.9.1 release fixes a small bug and changes tuxbuild submission
slightly.

Complete list of changes going in:

* Remove the arch from the test name when using tuxbuild json
* Gracefully handle some tuxbuild json config errors
* Do not show the hash for an empty kconfig

# 0.9

This 0.9 release adds support for TuxBuild input for submitting test results
to SQUAD.

Complete list of changes going in:

* Add an option to the submit command that allows the submission of tuxbuild json result files
* Fix a file extension check error message
* Allow the verbose flag to be used when running specific tests
* tests: fixtures: fix fixtures to work along with recent squad changes
* core: models: query tests in Suite class
* commands: fix submit command docs

# 0.8.1

This 0.8.1 release just turns the featured added in 0.8 into a command line.
It makes possible to create or update a project using command line arguments.

Complete list of changes going in:

* commands: add create_or_update_project command
* shortcuts: add create_or_update_project shortcut

# 0.8

This 0.8 release fixes the number of suites retrieved in build_report
and allow users to create projects using the client. A newer version
will come in quickly allowing all models to be created/deleted.

Complete list of changes going in:

core: models allow project creation
examples: fix suite retrieval in build_report.py

# 0.7

This 0.7 release adds a method in project to fetch its environments
among other minor bug fixes.

The release also changes the home of squad-client docker image to
squadproject/squad-client.

Complete list of changes below:

* add methods to fetch environments from a project
* change the attribute from complete to finished
* core: models: add nested endpoints to models
* examples: fix URL in build_report
* fix the example for filtering on finished builds
* manage: avoid configuring api when running tests
* release: change docker repo to squadproject


# 0.6

This 0.6 release adds basic caching for fetching data. It also adds
support for fetching metrics and a shortcut for comparing two builds
from the same project.

Complete list of changes below:

* core:
  * api: ignore netrc auth
  * models: add metrics
  * models: add suite do project model
  * models: fix metrics and testrun status endpoints
  * shortcuts: add shortcut to compare builds
* manage: add basic caching
* shortcuts: return exit code of submit operation
* tests: add test for submit_results return value

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
