import unittest
from unittest.mock import patch
from io import StringIO


from squad_client.report import Report, ReportContext, ReportGenerator
from squad_client.exceptions import InvalidSquadObject


class ReportContextTest(unittest.TestCase):
    def test_basics(self):
        context = {
            'var1': {
                'type': 'Build',
                'filters': {
                    'param1': 'val1'
                }
            }
        }

        report_context = ReportContext(context)
        self.assertEqual(1, len(report_context.context))

        c = report_context.context[0]
        self.assertEqual('var1', c.name)
        self.assertEqual('Build', c.type)
        self.assertEqual({'param1': 'val1'}, c.filters)

    def test_invalid_object_type(self):
        context = {
            'var1': {
                'type': 'InvalidType',
            }
        }
        report_context = ReportContext(context)
        with self.assertRaises(InvalidSquadObject):
            report_context.fill()


class ReportTest(unittest.TestCase):

    def test_basic_report_generation(self):
        template = 'This is the most basic template'
        report = Report(template)
        generated = report.generate()
        self.assertEqual(template, generated)

    @patch('squad_client.core.models.Squad.fetch')
    def test_basic_report_generation_with_context(self, squad_fetch):
        squad_fetch.return_value = 'fetched string'
        template = 'Report: {{ dummy }}'
        context = ReportContext({
            'dummy': {
                'type': 'Test',
                'filters': {
                    'param1': 'val1'
                }
            }
        })
        report = Report(template, context=context)
        generated = report.generate()
        self.assertEqual('Report: fetched string', generated)


class ReportGeneratorTest(unittest.TestCase):

    @patch('squad_client.core.models.Squad.fetch')
    def test_basics(self, squad_fetch):
        squad_fetch.return_value = 'fetched string'
        template = 'Report: {{ dummy }}'
        output = StringIO()
        context = {
            'dummy': {
                'type': 'Test',
                'filters': {
                    'param1': 'val1'
                }
            }
        }
        generator = ReportGenerator('http://example.com')
        generator.add_report('dummy report', template, output=output, context=context)
        reports = generator.generate()

        self.assertEqual(1, len(reports))

        self.assertEqual('Report: fetched string', output.getvalue())
