## Stream Reddit Comments 

  
Stream Reddit Comments is a Django web application which allows a user to stream the newest comments from any Reddit submission. This application utilizes the Reddit Python API library named [PRAW](https://praw.readthedocs.io/en/stable/index.html) 


It is currently hosted below:

http://152.53.55.203:8000/reddit-comment-stream/
  

Features include: 

  * Dark, Light, or System Theme which is saved for every user session.

  * Option to change refresh rate of comments, also saved for every user session. 

  * Comments stop refreshing when scrolling down and allow for a manual refresh. 

  * Home page contains top 5 most active submissions currently (submissions with least amount of time between comments). 

    These submissions cards contain a link to start streaming them directly. 

  * Ability to stream multiple posts concurrently in separate browser tabs.



Technical Talking Points: 

 * This site uses vanilla JavaScript, a CSS framework called [Bulma](https://bulma.io/), and [FontAwesome](https://fontawesome.com/) for icons.

  *  Each browser session contains a session id which we can use to store data into the session table in Django's session database. 

     I have used this table to store the comments that have already been loaded for a certain user's browser session and Reddit submission they are streaming. This is required as the PRAW API always fetches the newest comments from a post, which may not have changed since the last refresh.

     This allows the site to only show new comments on automatic refresh, which is implemented using the JavaScript Fetch API. 

  *  I have  utilized Promises in the comment streaming JavaScript code. Promises were great for this use case as I had 3 conditions that would allow for comments to be refreshed or for the timer to be reset. 

        * The first most obvious use case is when the time the user has 
      set to refresh comments has expired, this is done by resolving a promise after the completion of a setTimeout function call.

        * The second Promise is triggered when the refresh options drop down is changed, this is so if a user changes from 15    seconds to 30 seconds for instance, the timer gets reset to start at 30 seconds.

        * The third Promise is triggered whenever the user clicks the manual refresh button,
      which only shows up if they scroll down past the header of page. This promise will immediately refresh the comments. 

        * These three Promises race each other, so whichever one finishes first will then go into a final method.
      This method checks the resolution code and either sends a Fetch request to the Django server, or restarts the timers for another iteration.

  *  A daemon thread has been created that finds active submissions on startup of the web server and runs indefinitely. 
     This thread will fetch submissions from Reddit that are considered “hot” with a limit of 5,000 total posts. We will also only consider posts that have at least 1,000 comments.  
     I then check the newest comments for each submission and compare the time between the current and next comment. This total difference is then averaged and sorted.  
     The top 5 submissions with the least average time between comments, are then stored in a Django Model table, in this case called ActiveSubmissions. These records are fetched from the Django database each time the user browses to the home page. 
     
     Because the site may query the database while a new row is being replaced, a mutex is used to prevent a situation where the user may see only 4 top submissions instead of 5.

  *   The application has been created into an image on docker hub which can be downloaded [here](https://hub.docker.com/repository/docker/maxkernchen/reddit-stream/general)

 
