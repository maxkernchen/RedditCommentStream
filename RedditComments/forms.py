from django import forms

class RedditURL(forms.Form):
    reddit_url = forms.CharField(label='reddit_url', max_length=300)




