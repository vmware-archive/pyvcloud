import tempfile
import logging
import requests

_logger = None

def _get_logger():
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("pyvcloud")
    _logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler("%s/pyvcloud.log" % tempfile.gettempdir())
    formatter = logging.Formatter("%(asctime)-23.23s | %(levelname)-5.5s | %(name)-15.15s | %(module)-15.15s | %(funcName)-12.12s | %(message)s")
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
    def _log_response(logger, response):
        if logger is not None:
            logger.debug('[%d] %s', response.status_code, response.text)

    @staticmethod
    def get(url, logger=None, **kwargs):
        response = requests.get(url, **kwargs)
        Http._log_response(logger, response)
        return response

    @staticmethod
    def post(url, data=None, json=None, logger=None, **kwargs):
        response = requests.post(url, data, json, **kwargs)
        Http._log_response(logger, response)
        return response

    @staticmethod
    def put(url, data=None, logger=None, **kwargs):
        response = requests.put(url, data, **kwargs)
        Http._log_response(logger, response)
        return response

    @staticmethod
    def delete(url, logger=None, **kwargs):
        response = requests.delete(url, **kwargs)
        Http._log_response(logger, response)
        return response
