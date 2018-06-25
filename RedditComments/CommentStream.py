import praw
from praw.models import MoreComments;
import praw.config
def write_comments(comment_url):
    reddit = praw.Reddit(client_id='missingforprivacy',
    client_secret='missingforprivacy',
    user_agent='missingforprivacy')
    # get the submission from the link passed in
    submission = reddit.submission(url=comment_url)

    # get all posts
    submission.comments.replace_more(limit=0)
    #only get comments and then sort by new
    comment_list = submission.comments
    comment_list = sorted(comment_list, key=lambda comment: comment.created_utc,reverse=True)
    comment_body = []
    i = 0

    for comment in comment_list:
        i += 1
    # print(comment.body)
     #   print(comment.created_utc)

        comment_body.append(comment.body)
    # return the comments only
    print("number of comments: ", i)

    return comment_body

if __name__ == "__main__":
    write_comments()
