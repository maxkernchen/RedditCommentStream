from django import forms
__author__  = 'Max Kernchen'
__version__ = '1.0.'
__email__   = 'max.f.kernchen@gmail.com'

""" forms.py - repesents form submission from index page, contains full url 
             
"""
class RedditURL(forms.Form):
    reddit_url = forms.CharField(label='reddit_url', max_length=300)





