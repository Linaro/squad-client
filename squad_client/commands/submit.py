import json
import logging
import os
import yaml
from squad_client.shortcuts import submit_results
from squad_client.core.command import SquadClientCommand


logger = logging.getLogger()


class SubmitCommand(SquadClientCommand):
    command = "submit"
    help_text = "submit results to SQUAD"

    def register(self, subparser):
        parser = super(SubmitCommand, self).register(subparser)
        result_group = parser.add_mutually_exclusive_group()
        result_group.add_argument(
            "--results",
            help="File with test results to submit. Max 5MB. JSON and YAML formats are supported",
        )
        result_group.add_argument("--result-name", help="Single result name")
        parser.add_argument(
            "--result-value",
            help="Single result output (pass/fail)",
            choices=["pass", "fail"],
        )
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
        parser.add_argument("--logs", help="Test log file path")
        parser.add_argument(
            "--group", help="SQUAD group where results are stored", required=True
        )
        parser.add_argument(
            "--project", help="SQUAD project where results are stored", required=True
        )
        parser.add_argument(
            "--build", help="Build version where results are stored", required=True
        )
        parser.add_argument(
            "--environment",
            help="Build environent where results are stored",
            required=True,
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
        output_dict = None
        with open(file_path, "r") as results_file:
            try:
                output_dict = json.load(results_file)
            except json.JSONDecodeError:
                logger.warning("JSON parsing failed")
                results_file.seek(0)
                try:
                    output_dict = yaml.safe_load(results_file)
                except yaml.YAMLError as exc:
                    logger.warning("YAML parsing failed")

        return output_dict

    def run(self, args):
        results_dict = None
        metrics_dict = None
        metadata_dict = None
        logs_file = None
        if args.result_name:
            if not args.result_value:
                logger.error("Test result value is required")
                return False
            results_dict = {args.result_name: args.result_value}
        elif args.results:
            if not self.__check_file(args.results):
                return False
            results_dict = self.__read_input_file(args.results)
        elif args.metrics:
            if not self.__check_file(args.metrics):
                return False
            metrics_dict = self.__read_input_file(args.metrics)
        else:
            logger.error(
                "At last one of --result-name, --results, --metrics is required"
            )
            return False

        if args.metadata:
            if not self.__check_file(args.metadata):
                return False
            metadata_dict = self.__read_input_file(args.metadata)
        if args.logs:
            if not self.__check_file(args.logs):
                return False
            with open(args_logs, "r") as logs_file_souce:
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
                if type(value) not in [str, dict]:
                    logger.error("Incompatible results detected")
                    return False

        submit_results(
            group_project_slug="%s/%s" % (args.group, args.project),
            build_version=args.build,
            env_slug=args.environment,
            tests=results_dict,
            metrics=metrics_dict,
            log=logs_file,
            metadata=metadata_dict,
        )

        return True
