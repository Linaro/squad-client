import jinja2
import uuid

from os import path
from io import StringIO

from squad_client import logging
from squad_client.core.api import SquadApi
from squad_client.core.models import SquadObject, Squad
from squad_client.exceptions import InvalidReportOutput, InvalidReportTemplate


logger = logging.getLogger(__name__)


class Report:
    def __init__(self, template, name=None, output=None, context=None):
        self.name = name if name else str(uuid.uuid1())
        self.template = template
        self.output = output
        self.context = context

    def generate(self):
        logger.info('Generating report "%s"' % self.name)
        values = self.context.fill() if self.context else {}
        template = self.get_template()
        return template.render(**values)

    def get_template(self):
        if self.template.endswith('.jinja2'):
            if path.isfile(self.template):
                abspath = path.abspath(self.template)
                loader = jinja2.FileSystemLoader(searchpath=path.dirname(abspath))
                environment = jinja2.Environment(loader=loader)
                template = environment.get_template(self.template)
            else:
                raise InvalidReportTemplate('Template file "%s" not found!' % self.template)
        else:
            template = jinja2.Template(self.template)
        return template


class ReportContext:
    class Context:
        pass

    def __init__(self, context={}):
        """
            Context dictionary should be in the format
            context = {
                'var1': {
                    'type': 'Build', # or any other available subclass of SquadObject
                    'filters': {
                        'param1': 'val1',
                        ...
                    }
                },
                ...
            }
        """
        self.context = []
        for name in context.keys():
            c = ReportContext.Context()
            if not name.isidentifier():
                name = name.replace(' ', '_')
            c.name = name
            c.type = context[name]['type']
            c.filters = context[name].get('filters') or {}
            self.context.append(c)

    def fill(self):
        logger.debug('Building report context')
        self.values = {}
        squad = Squad()
        for c in self.context:
            _type = SquadObject.get_type(c.type)
            self.values[c.name] = squad.fetch(_type, **c.filters)
        return self.values


class ReportGenerator:
    def __init__(self, squad_url, token=None):
        self.squad_url = squad_url
        self.token = token
        self.reports = []

    def add_report(self, name, template, output=None, context={}):
        report = Report(template, name, output, ReportContext(context))
        self.reports.append(report)
        return report

    def generate(self):
        for report in self.reports:
            SquadApi.configure(self.squad_url, self.token)
            output = report.generate()
            if report.output is None:
                # print to stdout
                print(output)
            elif type(report.output) is StringIO:
                report.output.write(output)
            elif type(report.output) is str and path.isfile(report.output):
                with open(report.output, 'w') as f:
                    f.write(output)
            else:
                raise InvalidReportOutput('Report "%s" output configuration is neither None, a file or StringIO object' % report.name)
        return self.reports
