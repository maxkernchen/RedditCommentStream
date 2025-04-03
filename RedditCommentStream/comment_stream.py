from datetime import datetime, timezone
import configparser
import praw
import praw.config
import praw.exceptions
import praw.models.reddit.more
import prawcore.exceptions
import re
from praw.models import MoreComments
from pathlib import Path
import os
__author__  = 'Max Kernchen'
__version__ = '1.0.'
__email__   = 'max.f.kernchen@gmail.com'

""" This module's main purpose is to retreive the latest comments from a submission, it is called often via fetch or the 
post request from our index form submission.
"""

def get_comments(submission_id, views_request, is_post, tz_offset):
    """ Method get_comments will take in a submission_id (6 character alphanumeric value) from views.py
        and find the submission/newest comments. These comments are then compared to already loaded comments
        stored in the session cookie. Any comments comments that different from the already loaded ones are returned to
        views.py in a formatted string.
        -----params-----
        @submission_id - the 6 char alphanumeric value that represents a submission
        @views_request - the request object from views.py, this is passed in to update the session cookie.
        @is_post       - the request is a POST so we will need additonal info returned in our dictionary

        @return a dictionary with comments sorted by newest, the title and permalink if this is a POST request
    """
    config = configparser.ConfigParser()
    config_dir = Path(os.getcwd() + '/RedditCommentStream/praw.ini')
    config.read(config_dir)

    reddit_obj = praw.Reddit(client_id=config['bot1']['client_id'],
                             client_secret=config['bot1']['client_secret'],
                             user_agent=config['bot1']['user_agent'])

    try:
        submission = reddit_obj.submission(id=submission_id)
        # only get the newest comments
        submission.comment_sort = 'new'
        comment_list = list(submission.comments)
    except (praw.exceptions.PRAWException, prawcore.PrawcoreException,
            praw.exceptions.RedditAPIException) as e:
        # None is okay to return as views.py will handle this appropriately
        return None

    i = 0
    comments_sorted = []
    comments_cookie = []
    # get session cookie which stored the previous list of loaded comments
    already_loaded_comments = views_request.session['loaded_comments_cookie']
    for comment in comment_list:
        if isinstance(comment, MoreComments):
            # for now we are only streaming top-level comments, no replies
            continue
        comments_sorted.append(comment)
        # store just the comment id hex value to only load new comments between ajax calls
        comments_cookie.append(comment.id)

    comments_arthur = []
    comments_time = []
    comments_body = []
    for comment in comments_sorted:
        i += 1
        # don't track deleted comments or comments which we've already loaded
        if(comment.author is not None and comment.id not in already_loaded_comments and not comment.stickied):
            comments_arthur.append(comment.author.name)
            comments_time.append('<div class=\"comment-time\">' + str(datetime.fromtimestamp(comment.created_utc - (int(tz_offset) * 60),
                                                                timezone.utc).replace(tzinfo=None)) + '</div>')
            comment_body = format_emotes(comment)
            comments_body.append(format_hyper_link(comment_body))

    #update session cookie with newly streamed comments
    views_request.session['loaded_comments_cookie'] = comments_cookie
    # store results in a dictionary, if this is a POST request on initial form submission
    # include the title and permalink
    submission_comments_dict = {}
    if(is_post):
        submission_comments_dict['title'] = submission.subreddit_name_prefixed + ' | ' + submission.title
        submission_comments_dict['permalink'] = 'https://www.reddit.com' + submission.permalink
    submission_comments_dict['comments_arthur'] = comments_arthur
    submission_comments_dict['comments_time'] = comments_time
    submission_comments_dict['comments_body'] = comments_body
    return submission_comments_dict

def get_submission_id_from_url(comment_url):
    """ Simple helper method which will parse the full url of the reddit page and find the submission_id only
    This is useful as it allows the user to enter only the partial url or just the submission_id in the form.
     -----params-----
    @comment_url - the url or submission id the user has passed into our form

    @return - just the parsed submission_id
    """
    index_start = comment_url.find('comments')
    # assume user has passed in just the submission id,
    # if it's incorrect it will be caught by try catch in get_comments
    if(index_start == -1):
        return comment_url
   
    # parse submission id which will start 9 characters after comments keyword in the url
    # and will be at least 5 chars, but can be more
    else:
        index_start += 9
        # find ending slash, this will then be our full submission id
        index_end = comment_url.find("/", index_start)
        # if the end slash is missing assume the last character is the full submission id
        if(index_end == -1):
            return comment_url[index_start:len(comment_url)]
        else:
            return comment_url[index_start:index_end]


def format_hyper_link(comment_text):
    """ Simple helper method which will parse each comment and find if it contains a hyperlink in the reddit format
       e.g. [URL NAME](www.url.com)
       -----params-----
      @comment_text - text of the comment to check

      @return - the comment as is or parsed into an anchor tag for a hyperlink
      """
    anchor_html = '<a href="{0}">{1}</a>'
    pattern_link = r'\[.+?\]\(https{0,1}:\/\/.+?\)'
    matches = re.finditer(pattern_link, comment_text)
    for match in matches:
        start = int(match.regs[0][0])
        end = int(match.regs[0][1])
        link_str = match.string[start:end]
        open_bracket_index = link_str.find('[')
        closing_bracket_index = link_str.find(']')
        opening_parentheses_index = link_str.find('(')
        closing_parentheses_index = link_str.find(')')
        # verify bracket and paranthese are in the right place then format the anchor html
        # with our link and link name
        if(open_bracket_index < closing_bracket_index and opening_parentheses_index < closing_parentheses_index and
        opening_parentheses_index > open_bracket_index and opening_parentheses_index > closing_bracket_index):
            anchor_html_filled = anchor_html.format(link_str[opening_parentheses_index + 1:closing_parentheses_index],
                                            link_str[open_bracket_index + 1:closing_bracket_index])
            comment_text = comment_text.replace(link_str, anchor_html_filled)


    return comment_text


def format_emotes(comment):
    """ Takes a comment object and finds all emotes usually in the form of ![img](emote|t5_2th52|1234)
        then replaces these with the actual image stored in the media_metadata dictionary
       -----params-----
      @comment - the comment object which represents the current comment

      @return - the comment text but with emotes correctly inserted or just the raw text if there are
                no emotes.
      """
    if hasattr(comment, 'media_metadata'):
        emote_html = '<img class="emote" alt="Comment Emote" src="{0}">'
        comment_text = comment.body
        pattern_whole = r'!\[img\]\(emote\|.+?\|[0-9].+?\)'
        pattern_key = r'emote\|.+?\|[0-9]+'
        matches = re.finditer(pattern_whole, comment_text)
        for match in matches:
            start = int(match.regs[0][0])
            end = int(match.regs[0][1])
            emote_str = match.string[start:end]
            emote_key_search = re.search(pattern_key, emote_str)
            emote_key = emote_key_search.group()
            # replace emote with img tag that has source defined from dictionary 
            if emote_key in comment.media_metadata:
                emote_html_with_src = emote_html.format(comment.media_metadata[emote_key]['s']['u'])
                comment_text = comment_text.replace(match.string[start:end], emote_html_with_src)
        
        return comment_text
    else:
        return comment.body


def parse_submission_id(processing_url):
    """ Simple helper method which will parse the submission id from our processing url.
     -----params-----
    @processing_url - processing url in format /process-url/123abc

    @return - just the parsed submission_id
    """
    # get the submission url it will be at least 5 characters
    submission_id = processing_url[13:len(processing_url)]
    # the url can either have the last slash or not
    if(submission_id[-1] == "/"):
        return submission_id[:-1]
    else:
        return submission_id
    
