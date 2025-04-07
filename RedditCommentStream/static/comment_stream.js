document.getElementById('spinner').style.visibility = 'hidden';
document.getElementById('refresh-btn').style.display = 'none';

const tz_offset = new Date().getTimezoneOffset();
updateAllDateTimeLocale()
// bool for when scrolled down past our header, this for tracking if we should refresh or not.
// Where scrolling down stops the comment refreshing. 
let scrolled_down = false;

// set up dropdown event
const setting_dropdown = document.getElementById('setting-dropdown');
setting_dropdown.addEventListener('click', function(event){
  event.stopPropagation();
  setting_dropdown.classList.toggle('is-active');
});

const icon_light = document.getElementById('icon-light');
const icon_dark = document.getElementById('icon-dark');
const icon_system = document.getElementById('icon-system');
// get localStorage saved theme if it exists, if not we'll just use the system value
const theme_val_storage = localStorage.getItem('theme-val');
theme_val_storage ? toggleTheme(theme_val_storage) : toggleTheme('system');
// get saved refresh rate if it exists
const refresh_rate_saved = localStorage.getItem('refresh-rate');
if(refresh_rate_saved){
  const refresh_rate_select = document.getElementById('refresh-rate-options');
  refresh_rate_select.value = refresh_rate_saved;
}


/* Method startRace - Creates three promises that will race each other.
  1. promise_refresh_rate - This promise is only resolved if refresh rate is not 'Don't Refresh' ( > 0).
                It is resolved after the amount of the time the refresh rate is defined for passes.
                Then we will call fetch to reload the comments in page.
  2. promise_refresh_changed - This promise is resolved whenever the refresh rate drop down has changed value.
                This means that if the refresh rate is changed while we are waiting for a new refresh, the current
                refresh wait time is reset.
  3. promise_refresh_btn - This promise is resolved when the refresh floating button is clicked, 
                and will immediately reload comments.

*/
async function startRace (){
  // get current refresh rate if refresh rate == -1 we don't refresh.
  const refresh_rate_select = document.getElementById('refresh-rate-options');
  const refresh_rate_val = refresh_rate_select.options[refresh_rate_select.selectedIndex].value;

  const promise_refresh_rate = new Promise(function(resolve) {
    // only resolve this promise if refresh rate is not set to don't refresh.
    // resolve after the amount of time defined in the refresh rate drop down.
      if(refresh_rate_val != -1 && !scrolled_down) {
        setTimeout(resolve, refresh_rate_val, 1);
      }
      else {
        // resolve after 2 seconds so we are not calling too often to check if we have scrolled back up to the top
        setTimeout(resolve, 2000, -2);;
      }
  });

  // second promise which is resolved whenever the refresh rate drop down is changed.
  const promise_refresh_changed = new Promise(function(resolve) {
      document.getElementById('refresh-rate-options').addEventListener('change', function(){
        const refresh_rate_select = document.getElementById('refresh-rate-options');
        const refresh_rate_val = refresh_rate_select.options[refresh_rate_select.selectedIndex].value;
        localStorage.setItem('refresh-rate', refresh_rate_val)
        resolve(-1);
      });
  });
  // third promise is the refresh button is clicked so refresh data right away.
  const promise_refresh_btn = new Promise(function(resolve) {
    document.getElementById('refresh-btn').addEventListener('click', () => {
      resolve(2);
    });
  });

 Promise.race([promise_refresh_rate, promise_refresh_changed, promise_refresh_btn]).then(async function(value) {
    // Make the fetch call to Django server if we have a != -1 refresh rate
    // and we have not scrolled to where the manual refresh button is showing.
    // But always refresh if we were called from the refresh button directly (resolve code 2)
    if((refresh_rate_val != -1 && value > 0 && !scrolled_down) || value == 2){
      // scroll to top of page when refresh button clicked
      if(value == 2){
        window.scrollTo({top: 0, behavior: 'smooth'});        
      }
      document.getElementById('spinner').style.visibility = 'visible';
      const url = window.location.pathname;
      const query = {time_zone_offset: tz_offset};
      const fetch_params = new URLSearchParams(query);

      try 
      {
        const data = await (await fetch(url + "?" + fetch_params, {
          method: 'GET'
        })).text();

        if(data){
          addNewComments(data);
        }
        else{
          document.getElementById('spinner').style.visibility = 'hidden';
          startRace();
        }
      } 
      catch(error)
      {
        console.log('Refreshing Comments Failed: ' + error);
        startRace();
      }
    }
    else{
        startRace();
    }});
}
// Entry point. This function is recalled often.
startRace();

/* Method addNewComments - hide spinner and populate data from GET response to entire page.
   @param data - GET response data, which will be our html template generated by views.py
 */
async function addNewComments(data){
 
  document.getElementById('spinner').style.visibility = 'hidden';
  // remove parent div from previous new comments if they exist
  let new_comments = document.getElementById('new-comments');
  if(new_comments){
    new_comments.replaceWith(...new_comments.childNodes);
  }
  // insert new comments and update time locale
  document.getElementById('inner-comment-list').insertAdjacentHTML('afterbegin', data);
  updateNewDateTimeLocale();
  // small delay to allow render time for fade-in property to be updated.
  await new Promise(r => setTimeout(r, 100));
  document.getElementById('new-comments').classList.add('fade-in');
  // call entry method again.
  startRace();
}

/* Method toggleTheme -  This method allows us the change the theme of the page.
   @param - themeStr - the theme we are changing to valid values are light, dark, or system
*/
function toggleTheme(themeStr){
  document.documentElement.removeAttribute('class');
  icon_light.classList.remove('fa-border');
  icon_dark.classList.remove('fa-border');
  icon_system.classList.remove('fa-border');

  if(themeStr === 'light'){
    document.documentElement.classList.add('theme-light');
    icon_light.classList.add('fa-border');
    localStorage.setItem('theme-val', 'light');
  }
  else if(themeStr === 'dark'){
    document.documentElement.classList.add('theme-dark');
    icon_dark.classList.add('fa-border');
    localStorage.setItem('theme-val', 'dark');
  }
  else if(themeStr === 'system'){
    icon_system.classList.add('fa-border');  
    localStorage.removeItem('theme-val');
  }
}

const comment_div = document.getElementById('comments');
// Listen for when the scrolled window is below the header, 
// this is when we will show our manual refresh button on the bottom right
function scrollListener(){
  if(window.scrollY > comment_div.offsetTop){
    scrolled_down = true;
    document.getElementById('refresh-btn').style.display = ''
  }
  else if(window.scrollY <= comment_div.offsetTop){
    scrolled_down = false;
    document.getElementById('refresh-btn').style.display = 'none';
  }
} 
window.addEventListener('scroll', scrollListener);

// Method updateAllDateTimeLocale - Update every comment's date time into the user's locale
function updateAllDateTimeLocale(){
  document.querySelectorAll('.comment-time').forEach((el) => {
    const comment_time = new Date(Date.parse(el.innerHTML));
    const comment_time_locale = comment_time.toLocaleString();
    el.replaceWith(comment_time_locale);
  });
 
}
// Method updateNewDateTimeLocale - Update only new comments date time into user's locale
function updateNewDateTimeLocale(){
  const new_comments = document.getElementById('new-comments');
  new_comments.querySelectorAll('.comment-time').forEach((el) => {
    const comment_time = new Date(Date.parse(el.innerHTML));
    const comment_time_locale = comment_time.toLocaleString();
    el.replaceWith(comment_time_locale);
  });
}



