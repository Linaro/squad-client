import requests
import logging
import urllib


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
        if endpoint.startswith('http'):
            parsed_url = urllib.parse.urlparse(endpoint)
            assert SquadApi.url == '%s://%s/' % (parsed_url.scheme, parsed_url.netloc), \
                   'Given url (%s) is does not match pre-configured one!'

            params.update(urllib.parse.parse_qs(parsed_url.query))
            endpoint = parsed_url.path

        url = '%s%s' % (SquadApi.url, endpoint if endpoint[0] is not '/' else endpoint[1:])
        logger.debug('GET %s (%s)' % (url, params))
        return requests.get(url=url, params=params)

