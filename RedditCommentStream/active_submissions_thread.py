import time
from threading import Thread
from . import active_submissions
__author__  = 'Max Kernchen'
__version__ = '1.0.'
__email__   = 'max.f.kernchen@gmail.com'

""" Simple class whoses only purpose is to call get_active_submissions indefinitely every 5 minutes by default
This class is called by app.py on run of the Django server
"""

class ActiveSubmissionsThread(Thread):

    def __init__(self, interval=5*60):
        """ Constructor which sets the interval and defines the thread
        ----params-----
        @interval - the number of seconds between each call to get_active_submissions(), default value is 5 minutes
        """
        self.interval = interval
        self.thread = Thread(target=self.run)
        self.thread.daemon = True

    def run(self):
        """ run method whichw will start the thread and wait for the interval defined to call
        get_active_submissions()
        """
        while True:
            active_submissions.get_active_submissions()
            time.sleep(self.interval)