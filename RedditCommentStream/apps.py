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
        Only runs for main process by using --preload option for gunicorn
        """
      
        from . import active_submissions_thread
        import logging
        from logging.handlers import RotatingFileHandler
        logs_dir = "reddit_stream_logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        log_name = os.path.join(logs_dir, 'RedditStreamLog.txt')

        loggerCfg = logging.basicConfig(
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            level=logging.INFO,
                            handlers=[RotatingFileHandler(log_name, maxBytes=1000000, backupCount=10)])

        ActiveSubThread = active_submissions_thread.ActiveSubmissionsThread()
        ActiveSubThread.thread.start()