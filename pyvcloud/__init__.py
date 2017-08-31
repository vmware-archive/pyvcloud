import tempfile
import logging
import requests
try:
    import httplib
except ImportError:
    import http.client

_logger = None


def _get_logger():
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("pyvcloud")
    _logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler("%s/pyvcloud.log" % tempfile.gettempdir())
    formatter = logging.Formatter(
        "%(asctime)-23.23s | %(levelname)-5.5s | %(name)-15.15s | %(module)-15.15s | %(funcName)-12.12s | %(message)s")
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    requests_logger = logging.getLogger("requests.packages.urllib3")
    requests_logger.addHandler(handler)
    requests_logger.setLevel(logging.DEBUG)

    return _logger


class Log(object):

    @staticmethod
    def debug(logger, s):
        if logger is not None:
            logger.debug(s)

    @staticmethod
    def error(logger, s):
        if logger is not None:
            logger.error(s)

    @staticmethod
    def info(logger, s):
        if logger is not None:
            logger.info(s)


class Http(object):

    @staticmethod
    def _log_request(logger, data=None, headers=None, url=None):
        if logger is not None:
            logger.debug('url=%s' % url)
            if headers is not None:
                for header in headers:
                    logger.debug(
                        'request header: %s: %s',
                        header,
                        headers[header])
            if data is not None:
                logger.debug('request data:\n %s', data)

    @staticmethod
    def _log_response(logger, response):
        if logger is not None:
            for header in response.headers:
                logger.debug(
                    'response header: %s: %s',
                    header,
                    response.headers[header])
            logger.debug('[%d] %s', response.status_code, response.text)

    @staticmethod
    def get(url, data=None, logger=None, **kwargs):
        if logger is not None:
            Http._log_request(
                logger, data=data, headers=kwargs.get(
                    'headers', None), url=url)
        response = requests.get(url, data=data, **kwargs)
        Http._log_response(logger, response)
        return response

    @staticmethod
    def post(url, data=None, json=None, logger=None, **kwargs):
        if logger is not None:
            Http._log_request(
                logger, data=data, headers=kwargs.get(
                    'headers', None), url=url)
        response = requests.post(url, data=data, json=json, **kwargs)
        Http._log_response(logger, response)
        return response

    @staticmethod
    def put(url, data=None, logger=None, **kwargs):
        if logger is not None:
            Http._log_request(
                logger, data=data, headers=kwargs.get(
                    'headers', None), url=url)
        response = requests.put(url, data=data, **kwargs)
        Http._log_response(logger, response)
        return response

    @staticmethod
    def delete(url, data=None, logger=None, **kwargs):
        if logger is not None:
            Http._log_request(
                logger, data=data, headers=kwargs.get(
                    'headers', None), url=url)
        response = requests.delete(url, data=data, **kwargs)
        Http._log_response(logger, response)
        return response
