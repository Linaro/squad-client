import yaml

from os import path, chdir

from squad_client import logging
from squad_client.core.command import SquadClientCommand
from squad_client.report import ReportGenerator


logger = logging.getLogger(__name__)


class ReportCommand(SquadClientCommand):
    command = 'report'
    help_text = 'generate reports from yaml descriptor file'

    def register(self, subparser):
        parser = super(ReportCommand, self).register(subparser)
        parser.add_argument('--report-config', help='yaml file configuring the report. Assume `report.yml` by default', default='report.yml', dest='report_config')

    def run(self, args):
        logger.info('Running report')
        if not path.isfile(args.report_config):
            logger.error('Report config file "%s" not found!' % args.report_config)
            return False

        if args.report_config != 'report.yml':
            report_path = path.abspath(args.report_config)
            chdir(path.dirname(report_path))
            args.report_config = path.basename(report_path)

        return self.__generate__(args.report_config)

    def __generate__(self, report_config):
        logger.info('generating based on %s' % report_config)
        config = self.__parse_config__(report_config)
        generator = ReportGenerator(config.get('squad_url'), config.get('token'))
        for r in config.get('reports'):
            generator.add_report(r.get('name'), r.get('template'), output=r.get('output'), context=r.get('context'))

        generated = generator.generate()
        return len(generated) > 0

    def __parse_config__(self, report_config):
        with open(report_config) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config
