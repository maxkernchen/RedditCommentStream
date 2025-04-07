from django.apps import AppConfig
import os
__author__  = 'Max Kernchen'
__version__ = '1.1.'
__email__   = 'max.f.kernchen@gmail.com'

"""
RedditCommentsConfig which allows us to use a custom AppConfig and override the ready method
This is so we can spawn a background thread and setup our global logger
"""
class RedditCommentsConfig(AppConfig):
    name = 'RedditCommentStream'

    def ready(self):
        """ Overridden ready method which will require us to import inline modules
        This will setup out logger and spawn our background thread for ActiveSubmissions.
        Only runs for main process.
        """
        if os.environ.get('RUN_MAIN'):
            from . import active_submissions_thread
            import logging
            from logging.handlers import RotatingFileHandler
            loggerCfg = logging.basicConfig(
                                format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S',
                                level=logging.INFO,
                                handlers=[RotatingFileHandler('RedditCommentsLog.txt', maxBytes=1000000, backupCount=10)])

            ActiveSubThread = active_submissions_thread.ActiveSubmissionsThread()
            ActiveSubThread.thread.start()