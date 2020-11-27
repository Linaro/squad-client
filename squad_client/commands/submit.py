import hashlib
import json
import logging
import os
import yaml
from squad_client.shortcuts import submit_results
from squad_client.core.command import SquadClientCommand


logger = logging.getLogger()


class SubmitCommand(SquadClientCommand):
    """
        The `squad-client submit` command is flexible enought to allow 3 types of result
        submission:

        1. The simplest one is by submitting single results. Ex (log, metadata and attachments are optional):

            $ squad-client submit \
                  --group mygroup \
                  --project myproject \
                  --build mybuild
                  --environment myenv
                  --result-name mysuite/mytest \
                  --result-value pass \
                  --logs name-of-test-log-file.log \
                  --metadata name-of-test-metadata-file.json \
                  --attachments attachment1.json attachment2.png attachment3.xml

        2. The example above might be very limited if the use case requires sending many tests at once,
           in this case, the second way might be better (log, metadata and attachments are optional):

            $ squad-client submit \
                  --group mygroup \
                  --project myproject \
                  --build mybuild
                  --environment myenv
                  --results results-file.json \
                  --logs name-of-test-log-file.log \
                  --metadata name-of-test-metadata-file.log \
                  --attachments attachment1.log attachment2.png attachment3.xml

        3. Finally, there's a third alternative which used TuxBuild's (https://gitlab.com/Linaro/tuxbuild)
           format (log, metadata and attachments are optional):

            $ squad-client submit
                  --group mygroup \
                  --project myproject \
                  --results tuxbuild-results-file.json \
                  --results-layout tuxbuild
                  --logs name-of-test-log-file.log \
                  --metadata name-of-test-metadata-file.log \
                  --attachments attachment1.log attachment2.png attachment3.xml

        Note that using `--results-layout tuxbuild` makes `--environment` and `--build` optional
    """
    command = "submit"
    help_text = "submit results to SQUAD"

    def register(self, subparser):
        parser = super(SubmitCommand, self).register(subparser)

        # Group and project are always mandatory
        parser.add_argument(
            "--group", help="SQUAD group where results are stored", required=True
        )
        parser.add_argument(
            "--project", help="SQUAD project where results are stored", required=True
        )

        # metrics, metadata, logs and attachments are always optional
        parser.add_argument(
            "--metrics",
            help="File with metrics(benchmarsk) to submit. Max 5MB. JSON and YAML formats are supported",
        )
        parser.add_argument(
            "--metadata",
            help="File with metadata to submit. Max 5MB. JSON and YAML formats are supported",
        )
        parser.add_argument(
            "--attachments",
            nargs="+",
            help="Job attachments. Multiple files are allowed",
            default=[],
        )
        parser.add_argument(
            "--logs",
            help="Test log file path"
        )

        # Results might be submitted using a result file one-by-one or using a file
        result_group = parser.add_mutually_exclusive_group()

        # Results file
        result_group.add_argument(
            "--results",
            help="File with test results to submit. Max 5MB. JSON and YAML formats are supported",
        )

        # Individual results can use name, value, metrics file, metadata file and multiple attachment files
        result_group.add_argument(
            "--result-name",
            help="Single result name. Please use suite_name/test_name as value for this parameter"
        )
        parser.add_argument(
            "--result-value",
            help="Single result output (pass/fail/skip)",
            choices=["pass", "fail", "skip"],
        )
        parser.add_argument(
            "--results-layout",
            help="Layout of the results file, if any",
            choices=["tuxbuild"],
        )

        parser.add_argument(
            "--build",
            help="Build version where results are stored"
        )
        parser.add_argument(
            "--environment",
            help="Build environent where results are stored",
        )

    def __check_file(self, file_path):
        if not os.path.exists(file_path):
            logger.error("Requested file %s doesn't exist" % file_path)
            return False
        # check file size and quit if the file is too big
        if os.stat(file_path).st_size > 5242881:
            logger.error("%s - file too big" % file_path)
            return False
        return True

    def __read_input_file(self, file_path):
        if not self.__check_file(file_path):
            return None

        _, ext = os.path.splitext(file_path)
        if ext not in ['.json', '.yml', '.yaml']:
            logger.error('File "%s" does not have a JSON or YAML file extension' % file_path)
            return None

        parser = json.load if ext == '.json' else yaml.safe_load
        parser_exception = json.JSONDecodeError if ext == '.json' else yaml.YAMLError
        output_dict = None
        with open(file_path, "r") as results_file:
            try:
                output_dict = parser(results_file)
            except parser_exception as e:
                logger.error('Failed parsing file "%s": %s' % (file_path, e))

        return output_dict

    def _load_tuxbuild(self, path):
        if not self.__check_file(path):
            return None

        data = None
        try:
            with open(path) as f:
                tb = {}
                # TODO: extra build version (git-describe) and environment (arch)
                # and build results_dict with builds and environments according to the documentation above
                builds = json.load(f)

                for b in builds:
                    name = self._get_tuxbuild_test_name(b)
                    tb[name] = b["build_status"]

                data = tb

        except IndexError as ie:
            logger.error("Failed to load tuxbuild json due to a missing kconfig value: %s", ie)

        except KeyError as ke:
            logger.error("Failed to load tuxbuild json due to a missing variable: %s", ke)

        except json.JSONDecodeError as jde:
            logger.error("Failed to load json: %s", jde)

        except OSError as ose:
            logger.error("Failed to open file: %s", ose)

        return data

    def _get_tuxbuild_test_name(self, build):
        suite = "build"

        if len(build["kconfig"][1:]):
            kconfig = "%s-%s" % (build["kconfig"][0], hashlib.sha1(json.dumps(build["kconfig"][1:]).encode()).hexdigest()[0:8])
        else:
            kconfig = build["kconfig"][0]

        return "%s/%s-%s" % (
            suite, build["toolchain"], kconfig,
        )

    def run(self, args):
        """
            results_dict = {
                'buildA': {
                    'envA': [{'suiteA/testA': 'pass'}, {'suiteA/testB': 'fail'}],
                    'envB': [{'suiteA/testA': 'pass'}, {'suiteA/testB': 'fail'}]
                },
                'buildB': {...}
            }
        """
        results_dict = {}
        metrics_dict = {}
        metadata_dict = None
        logs_file = None

        if args.result_name:
            if not args.result_value:
                logger.error("Test result value is required")
                return False
            results_dict = {args.result_name: args.result_value}

        if args.results:
            if args.results_layout == 'tuxbuild':
                if args.environment:
                    logger.warning('Deprecation notice: --environment is being ignored when using --results-layout=tuxbuild. Future releases will cause it to break')
                if args.build:
                    logger.warning('Deprecation notice: --build is being ignored when using --results-layout=tuxbuild. Future releases will cause it to break')

                results_dict = self._load_tuxbuild(args.results)
            else:
                if args.environment is None or args.build is None:
                    logger.error('--environment and --build arguments are mandatory')
                    return False

                results_dict = {
                    args.build: {
                        args.environment: self.__read_input_file(args.results)
                    }
                }

            if results_dict is None:
                return False

        if args.metrics:
            metrics_dict = self.__read_input_file(args.metrics)
            if metrics_dict is None:
                return False

        if args.result_name is None and args.results is None and args.metrics is None:
            logger.error(
                "At least one of --result-name, --results, --metrics is required"
            )
            return False

        if args.metadata:
            metadata_dict = self.__read_input_file(args.metadata)
            if metadata_dict is None:
                return False

        if args.logs:
            if not self.__check_file(args.logs):
                return False
            with open(args.logs, "r") as logs_file_source:
                logs_file = logs_file_source.read()

        for filename in args.attachments:
            if not self.__check_file(filename):
                return False

        if results_dict:
            # check dictionary correctness
            for key, value in iter(results_dict.items()):
                if type(key) is not str:
                    logger.error("Non-string key detected")
                    return False
                if type(value) not in [str, dict]:
                    logger.error("Incompatible results detected")
                    return False

        if metrics_dict:
            # check dictionary correctness
            for key, value in iter(metrics_dict.items()):
                if type(key) is not str:
                    logger.error("Non-string key detected")
                    return False
                if type(value) not in [float, int, list]:
                    logger.error("Incompatible metrics detected")
                    return False

        if metadata_dict:
            # check dictionary correctness
            for key, value in iter(metadata_dict.items()):
                if type(key) is not str:
                    logger.error("Non-string key detected")
                    return False
                if type(value) not in [str, dict, int, list]:
                    logger.error("Incompatible metadata detected")
                    return False

        for build in results_dict.keys():
            for environment in results_dict[build].keys():
                results = results_dict[build][environment]

                submit_results(
                    group_project_slug="%s/%s" % (args.group, args.project),
                    build_version=build,
                    env_slug=environment,
                    tests=results,
                    metrics=metrics_dict,
                    log=logs_file,
                    metadata=metadata_dict,
                )

        return True
