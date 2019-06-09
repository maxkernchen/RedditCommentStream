from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.contrib import messages
from .forms import RedditURL
from . import comment_stream


"""
Method for loading the index page. Defined in URLS.py
param: request - request object that expects a response
"""
def index(request):
    return render(request, 'index.html')

"""
Method for loading the index page for a new stream, this page does not use any faded in elements. Defined in URLS.py
param: request - request object that expects a response
"""


def index_new_stream(request):
    return render(request, 'index_no_fade_in.html')


"""
Method for loading the comments page, will be used for both POST (original form submission) and GET 
(ajax in-page refresh request) requests. Defined in URLS.py
param: request - request object that expects a response
"""


def process_reddit_url(request):
    # if this is a POST request we need to process the form data
    comments = ['No Results Found']

    if request.method == 'POST':
        form = RedditURL(request.POST)
        # create a form instance and populate it with data from the request:

        if form.is_valid():

            # print(form.cleaned_data['reddit_url'])
            comment_url = form.cleaned_data['reddit_url']
            # to persist the URL for future ajax calls for now cache it to text file.
            # TODO: replace cache file with different method to store URL between calls.
            comment_file_post = open('URL_CACHE.txt', 'w')
            comment_file_post.write(comment_url)

            comments = comment_stream.get_comments(comment_stream, form.cleaned_data['reddit_url'])
            # Comments is None if any exceptions occur on the PRAW side
            if comments is not None and len(comments) > 0:
                return render(request, 'comments.html', {'comments_template': comments})
            else:
                return render(request, 'index_no_fade_in.html', {'error': 'invalid url'})
        else:
            # form found to be not valid.
            return render(request, 'index_no_fade_in.html', {'error': 'invalid url'})
    # ajax call for refresh will be a GET request
    if request.method == 'GET':
        # open cache file
        # TODO: replace cache file with different method to store URL between calls.
        comment_file_get = open('URL_CACHE.txt', 'r')
        comment_url_get = comment_file_get.read()
        if comment_url_get:
            comments = comment_stream.get_comments(comment_stream, comment_url_get.strip())
            return render(request, 'comment_body.html', {'comments_template': comments})





