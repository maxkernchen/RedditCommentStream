import configparser
import praw
import praw.config
import praw.exceptions
import praw.models.reddit.more
import prawcore.exceptions
import requests
from django.db import transaction
from RedditCommentStream.models import ActiveSubmissions
from praw.models import MoreComments
from better_profanity import profanity
from pathlib import Path
import wordninja
import logging
import os
import threading
logger = logging.getLogger(__name__)
__author__  = 'Max Kernchen'
__version__ = '1.1.'
__email__   = 'max.f.kernchen@gmail.com'


""" Module whoses main purpose is to fetch the top 5 active submissions currently on reddit, these 5 submissions
are then stored in the index page. This module will be called by a seperte daemon thread. 
"""

# for locking the changes to active submissions.
active_sub_mutex = threading.Lock()

def get_active_submissions():
    """ Fetches 5k of the most hot posts, then filters them down by eliminating posts with < 1000 comments
    and profantity in the title or subreddit name. Then each submission left is sorted by new comments and the time
    between comments is averaged. This will then give us a dictionary of indexes for our list of posts as the key
    and the average time per new comment as our value.
    We then take the top 5 of these sorted by least average time per comment and consider them the top 5 most active
    submissions. These are stored as our ActiveSubmission model and replaces existing rows in the database.

    WARNING - this method is long running, it takes an average of 5 mintues to complete due to the built in Reddit API
    calling limitations.
    
    -----returns-----
    @return - None if any exceptions are found, this is method is called every 5 minutes from a thread which does not
    expect any return values

    """
    # read the reddit config and login using our OAuth2 credentials
    config_dir = Path(os.getcwd() + '/RedditCommentStream/praw.ini')
    config = configparser.ConfigParser()
    config.read(config_dir)

    try:
        reddit_obj = praw.Reddit(client_id=config['bot1']['client_id'],
                                 client_secret=config['bot1']['client_secret'],
                                 user_agent=config['bot1']['user_agent'])

        logger.info('Starting new iteration of active submissions')
        all_submissions = list(reddit_obj.subreddit('all').hot(limit=5000))
    except (praw.exceptions.PRAWException, prawcore.PrawcoreException, praw.exceptions.RedditAPIException) as e:
        logger.error('PRAW Error on active submission: ' + e)
        # None is okay as the thread will just wait for next 5 minute interval
        return None
    # add any subreddits which are not in r/all and then filter profanity/posts with < 1000 comments
    add_excluded_subreddits(all_submissions, reddit_obj)
    filtered_posts = filter_posts(all_submissions)

    # find the avg time between comments for all filtered posts and stored them in avg_time_dict
    avg_time_dict = {}
    for i in range(len(filtered_posts)):
        try:
            filtered_posts[i].comment_sort = 'new'
            post = filtered_posts[i]
            comment_list_post = list(post.comments)
        except(praw.exceptions.PRAWException, prawcore.PrawcoreException, praw.exceptions.RedditAPIException) as e:
            logger.error('PRAW Error on active submission: ' + e)
              # None is okay as the thread will just wait for next 5 minute interval
            return None
        time_between_comments = 0
        num_comments = 0
        # compare 25 comments to get an average time between each comment.
        for j in range(25):
            if j == len(comment_list_post) - 1:
                break
            curr_comment = comment_list_post[j]
            next_comment = comment_list_post[j + 1]
            # skip any comments which are stickied, deleted, or are a MoreComments object.
            # this is to prevent any issues with how the avg time between comments is calcuated, i.e. it should
            # never result in a negative value
            if isinstance(curr_comment, MoreComments) or curr_comment.stickied or \
                    curr_comment.author is None or isinstance(next_comment, MoreComments) \
                    or next_comment.stickied or next_comment.author is None:
                continue
            difference = curr_comment.created_utc - next_comment.created_utc
            if(difference > 0):
                time_between_comments += (curr_comment.created_utc - next_comment.created_utc)
                num_comments += 1
        # store the avg time where the key is the index of the list of posts and the value is the average time
        if(num_comments > 0):
            avg_time_dict[i] = time_between_comments / num_comments

    i = 1
    # iterate through the dictionary ordered by the value, this results in top 5 most active posts with least time
    # between each new comment
    for k in sorted(avg_time_dict, key=avg_time_dict.get):
        logger.info(str(i) + 'th most active post with: ' + str(avg_time_dict[k]) + ' comments per sec')
        store_post_data(filtered_posts[k], i, avg_time_dict[k])
        # only check top 5 values
        if(i == 5):
            break
        i+=1
    logger.info('Finished iteration of active submissions')

def store_post_data(post, rank, avg_comment_time):
    """ Store the ActiveSubmissions model and delete any existing entries with same rank value.
        A global mutex is locked to ensure the results are not queried when one entry is replaced.
        Otherwise we might return only 4 top submissions. 
    -----params-----
    @post - the Reddit Submission object to be saved
    @rank - the rank int of this submission
    @avg_comment_time - the float value of averge comments per second
    """
    active_sub_mutex.acquire()
    ActiveSubmissions.objects.filter(rank=rank).delete()
    act_sub = ActiveSubmissions(submission_title=post.title,
                                num_comments=post.num_comments,
                                subreddit_name=post.subreddit_name_prefixed,
                                submission_permalink='https://reddit.com' + post.permalink,
                                one_comment_avg= round(avg_comment_time, 2),
                                rank=rank)
    act_sub.save()
    active_sub_mutex.release()

def query_active_submissions():
    """ Query to ActiveSubmissions model to return all rows from the database.
        Lock the mutex to make sure the database is not being updated while we query.

    @return - list of all ActiveSubmissions rows sorted by rank
    """
    active_sub_mutex.acquire()
    all_act_subs = []
    if (ActiveSubmissions.objects.all().exists()):
        all_act_subs = ActiveSubmissions.objects.all().order_by('rank')
    active_sub_mutex.release()
    return all_act_subs

def add_excluded_subreddits(all_list, reddit_obj):
    """ Certain subreddits which are popular have decicded to be excluded from r/all,
    This method will add the top 10 posts from these subreddits to our list all_list
    This method will open a text file in our root directory to add excluded subreddits to our
    -----params-----
    @all_list - list of all submissions from get_active_submissions method
    @reddit_obj - used to call Reddit API

    """
    excluded_subreddits = []
    excluded_subreddits_dir = Path(os.getcwd() + '/RedditCommentStream/excluded_subreddits_add.txt')
    with open(excluded_subreddits_dir) as file:
        excluded_subreddits = file.read().splitlines()
    for subreddit in excluded_subreddits:
        all_list += list(reddit_obj.subreddit(subreddit.strip()).hot(limit=10))

def filter_posts(all_posts_list):
    """ This method will filter posts to reduce number of submissions that we will fetch comments for.
    The main critera is that the number of comments in the submission is >= 1000 and that the title or subreddit name
    does not contain profanity.
    -----params-----
    @all_posts_list - the list of all submissions that we will filter down.
    -----returns-----
    @returns all_posts_list with filtered critera
    """
    profanity.load_censor_words()
    # A file will be opened to read some custom profanity keywords which show up on more inappropriate subreddits
    custom_badwords = []
    custom_badwords_dir = Path(os.getcwd() + '/RedditCommentStream/custom_profanity_keywords.txt')
    with open(custom_badwords_dir) as file:
        custom_badwords = file.read().splitlines()
    profanity.add_censor_words(custom_badwords)
    all_posts_list = list(filter(lambda post: post.num_comments >= 1000 and not post.over_18, all_posts_list))
    all_posts_list = list(filter(lambda post: not profanity.contains_profanity(post.title) and
                            not is_profanity_split(post.subreddit_name_prefixed[2:].lower())
                            # check both word splits and whole subreddit as a word
                            and not profanity.contains_profanity(post.subreddit_name_prefixed[2:].lower()), all_posts_list))
    return all_posts_list

def is_profanity_split(input_str):
    """ Because the subreddit name is combined without spaces e.g. r/ThisIsASubreddit
    I am using wordninja package to parse the words seperately and check if they contain profanity.
    -----returns-----
    @return - boolean value True for the subreddit name contains profanity else False
    """
    word_list = wordninja.split(input_str)
    for word in word_list:
        if(profanity.contains_profanity(word)):
            return True

    return False





