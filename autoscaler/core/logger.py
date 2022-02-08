import logging

from colorlog import ColoredFormatter


def logger_config():
    """
        Setup the logging environment
    """

    clogger = logging.getLogger()
    format_str = '%(log_color)s%(levelname)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    colors = {'DEBUG': 'cyan',
              'INFO': 'blue',
              'WARNING': 'bold_yellow',
              'ERROR': 'bold_red',
              'CRITICAL': 'bold_purple'}
    formatter = ColoredFormatter(format_str, date_format, log_colors=colors)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    clogger.addHandler(stream_handler)
    clogger.setLevel(logging.INFO)
    return clogger


logger = logger_config()


class GroupNamePrefixAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return '[%s] %s' % (self.extra['name'], msg), kwargs
