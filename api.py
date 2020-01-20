import requests
import logging


logger = logging.getLogger('api')


class SquadApi:
    url = None
    token = None

    @staticmethod
    def configure(url=None, token=None):
        SquadApi.url = url if url[-1] is '/' else url + '/'
        SquadApi.token = token
        logger.debug('SquadApi: url = "%s" and token = "%s"' % (SquadApi.url, 'yes' if SquadApi.token else 'no'))

    @staticmethod
    def get(endpoint, params):
        url = '%s%s' % (SquadApi.url, endpoint)
        logger.debug('GET %s (%s)' % (url, params))
        return requests.get(url=url, params=params)

