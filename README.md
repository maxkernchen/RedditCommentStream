Live Reddit Comments 

  

Live Reddit Comments is a Django web application which will allow a user to stream the newest comments from any Reddit submission This application utilizes the Reddit Python API library named PRAW - https://praw.readthedocs.io/en/stable/index.html 


It is currently hosted below:


http://192.210.137.126:8000/reddit-comment-stream/

  

Features include: 

  * Dark,Light, or System Theme which is stored for every user session.

  * Option to change refresh rate of comments, also saved for every user session. 

  * Comments stop refreshing when scrolling down and allow for a manual refresh. 

  * Home page contains top 5 most active submissions currently (submissions with least amount of time between comments). 

    These submissions cards contain a link to start streaming them directly. 

     

Technical Talking Points: 

  *  Each browser session contains a session id which we can use to store data into the session table in Django's session database. 

     I have used this table to store the submission id (a 6-character value unique to each Reddit submission) and a list of similarly unique comment ids. 

     Storing these two values allow me to easily remember the Reddit submission that is being used between AJAX calls. 
     It also lets me nicely refresh the comments list, so instead of refreshing the whole comment body for each AJAX call, 
     I will only fade in the newest comments that have not been loaded yet. 
     I also send a HTTP 204 status back to the AJAX response which lets the JavaScript code know that while the request was successful,
     no new comments have been written since our last request. 

  *  I have heavily utilized Promises in the comment streaming JavaScript code. Promises were great for this use case as I had 3 conditions 
     that would allow for comments to be refreshed or for the timer to be reset. The first most obvious use case is when the time the user has 
     set to refresh comments has expired, this is done by resolving a promise after the completion of a simple setTimeout function call. 
     The second Promise is triggered when the refresh options drop down is changed, this is so if a user changes from 15 seconds to 30 seconds for instance,
     the timer gets reset instead of refreshing after 15 or less seconds. The third Promise is triggered whenever the user clicks the manual refresh button,
     which only shows up if they scroll down past the header of page. This promise will immediately refresh the comments. 
     These three Promises race each other so whichever one finishes first will then go into a final method.
    This method checks the resolution code and either sends an AJAX request to the Django server, or restarts the timers for another iteration. 

  *  A daemon thread has been created that finds active submissions on startup of the web server and runs indefinitely. 
     This thread will fetch submissions from Reddit that are considered “hot” with a limit of 5,000. 
     Then it will filter out based on if the submission has greater than 1,000 comments and if it contains any adult content or topics.
     Usually once this filtering has completed, there are around 50 submissions found.
     I then check the newest comments for each submission and compare the time between the current and next comment. This total difference is then averaged and sorted.  
     The top 5 submission with the least average time between each comment is then stored in a Django Model table, in this case called ActiveSubmissions. These records are fetched from the Django database each time the user browses to the index page. 

 
