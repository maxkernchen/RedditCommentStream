from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from .forms import RedditURL
from . import CommentStream
import praw

def index(request):
    # festival_list = ['Birthday','Holi','Diwali']
    festival_list = ["Birthday", 'Holi', 'Diwali']
    template = loader.get_template('index.html')
    return render(request, 'index.html', {'current_name': festival_list})


def reddit_url(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        comments = ['No Results found']
        # create a form instance and populate it with data from the request:
        form = RedditURL(request.POST)
        # check whether it's valid:

        if form.is_valid():
            print(form.cleaned_data['reddit_url'])
            comments = CommentStream.write_comments(form.cleaned_data['reddit_url'])

    # if a GET (or any other method) we'll create a blank form
    else:
        form = RedditURL()

    return render(request, 'comments.html', {'comments_template': comments})