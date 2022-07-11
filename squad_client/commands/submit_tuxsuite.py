import json
import requests

from squad_client import logging
from squad_client.shortcuts import watchjob
from squad_client.core.command import SquadClientCommand


logger = logging.getLogger(__name__)


class SubmitTuxSuiteCommand(SquadClientCommand):
    command = "submit-tuxsuite"
    help_text = "submit TuxSuite results to SQUAD"

    def register(self, subparser):
        parser = super(SubmitTuxSuiteCommand, self).register(subparser)
        parser.add_argument(
            "--group", help="SQUAD group where results are stored", required=True
        )
        parser.add_argument(
            "--project", help="SQUAD project where results are stored", required=True
        )
        parser.add_argument(
            "--build", help="SQUAD build where results are stored", required=False
        )
        parser.add_argument(
            "--backend", help="SQUAD backend to be used to process results", required=True
        )
        parser.add_argument(
            "--json", help="File with tuxsuite results to submit", required=True
        )

    def _load_results_file(self, path):
        try:
            with open(path) as f:
                results = json.load(f)
        except Exception as e:
            logger.error("Failed to load json: %s", e)
            return None

        # results file can be one of 3 types: build.json, test.json or plan.json
        # the plan.json contains both tests and build results formatted as: {"builds": {}, "tests": {}}
        # both test.json and build.json contains either tests or builds only, respectively, formatted as: [{}]
        if type(results) == dict:
            if "tests" in results and "builds" in results:
                return results
            # else it's a single test result file
            results = [results]

        # index results using uid
        indexed = {r['uid']: r for r in results}

        # now attempt to identify the results type
        if results[0].get('build_name') is not None:
            results = {'builds': indexed, 'tests': {}}
        else:
            results = {'tests': indexed, 'builds': {}}
        return results

    def _generate_job_id(self, result_type, result):
        """
            The job id for TuxSuite results is generated using 3 pieces of info:
            1. If it's either "BUILD" or "TEST" result;
            2. The TuxSuite project. Ex: "linaro/anders"
            3. The ksuid of the object. Ex: "1yPYGaOEPNwr2pfqBgONY43zORp"

            A couple examples for job_id are:
            - BUILD:linaro@anders#1yPYGaOEPNwr2pCqBgONY43zORq
            - TEST:arm@bob#1yPYGaOEPNwr2pCqBgONY43zORp

            Then it's up to SQUAD's TuxSuite backend to parse the job_id
            and fetch results properly.
        """
        _type = 'TEST' if result_type == 'tests' else 'BUILD'
        project = result['project'].replace('/', '@')
        uid = result['uid']
        return f'{_type}:{project}#{uid}'

    def run(self, args):
        """
            Submitting TuxSuite results to SQUAD basically consists of:
            1. Parsing the TuxSuite results file
            2. Triggering a watchjob on every build or test result that has result!=unknown in
               TuxSuite results file
            3. Once SQUAD receives the watchjob request, it'll be responsible for
               retrieving important data out of TuxSuite api endpoints
        """
        results = self._load_results_file(args.json)
        if results is None:
            return False

        # If build is not specified, then fetch the first build
        # to get git-describe out of status.json
        build = args.build
        if build is None:
            first_build = results['builds'][0]
            try:
                response = requests.get('%s/%s' % (first_build['download_url'], 'status.json'))
                build = response.json()['git-describe']
            except Exception as e:
                logger.error("Failed to retrieve tuxsuite build: %s" % e)
                return False

        env_key = lambda result_type: 'device' if result_type == 'tests' else 'target_arch'  # noqa
        for result_type in ['builds', 'tests']:
            num_watching_jobs = 0
            for result in results[result_type].values():
                job_id = self._generate_job_id(result_type, result)

                num_watching_jobs += 1
                watchjob(
                    group_project_slug='%s/%s' % (args.group, args.project),
                    build_version=build,
                    env_slug=result[env_key(result_type)],
                    backend_name=args.backend,
                    testjob_id=job_id,
                )

            logger.info(f"Triggered {num_watching_jobs} watch jobs for {result_type}")

        return True
