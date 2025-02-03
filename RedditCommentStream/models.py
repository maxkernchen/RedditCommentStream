from django.db import models
__author__  = 'Max Kernchen'
__version__ = '1.0.'
__email__   = 'max.f.kernchen@gmail.com'

"""
models.py - only class defined here is ActiveSubmissions which we use to store 5 of the most active submissions 
currently on Reddit. The PK is permalink which will be unique for each submission
"""
class ActiveSubmissions(models.Model):
    submission_permalink = models.CharField(max_length=1000, primary_key=True)
    submission_title = models.CharField(max_length=1000)
    subreddit_name = models.CharField(max_length=1000)
    num_comments = models.IntegerField(default=0)
    one_comment_avg = models.FloatField(default=0)
    rank = models.IntegerField(default=0)
