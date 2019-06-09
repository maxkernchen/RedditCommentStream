import praw
from datetime import datetime
import praw.config
import praw.exceptions
import praw.models.reddit.more
"""
Method get_comments, this takes in a Reddit comment url string and passes it to the PRAW client.
Currently this returns only the parent comment, no child comments. 
Also it includes the time the comment was posted. These comments are order by newest submission.
para - comment_url - string of the full Reddit URL pointing to the comment page of a post.
"""

def get_comments(self, comment_url):
    reddit_obj = praw.Reddit(client_id = '',
                             client_secret = '',
                             user_agent = '')
    # get the submission from the link passed in
    try:
        submission = reddit_obj.submission(url=comment_url)
    except praw.exceptions.ClientException:
        # None is okay to return as views.py will handle this appropriately
        return None

    # for performance if there are more than 300 comments in a thread only use replace_more with a 100 limit.
    # replace_more will replace all comments that are actually a MoreComment object. However, this causes performance
    # hits with large Reddit threads
    if submission.num_comments > 1000:
        submission.comments.replace_more(limit=50)
    elif submission.num_comments > 300:
        submission.comments.replace_more(limit=100)
    else:
        submission.comments.replace_more(limit=None)

    # only get comments and then sort by newest comment
    i = 0
    comment_list = submission.comments

    comment_list = sorted(comment_list, key=lambda comment: comment.created_utc, reverse=True)
    comments_returned = []

    for comment in comment_list:
        i += 1

        comments_returned.append(str(datetime.fromtimestamp(comment.created_utc)) + " - " + comment.body)

    # return the comments only
    # print("number of comments: ", i)

    return comments_returned

