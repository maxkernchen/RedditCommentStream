document.getElementById('spinner').style.display = 'none';
document.getElementById('refresh-btn').style.display = 'none';

const tz_offset = new Date().getTimezoneOffset();
// bool for when scrolled down past our header, this for tracking if we should refresh or not.
// Similar to youtube or twitch comments where scrolling stops the refreshing. 
let scrolledDown = false;

//global boolean for our theme, light == true, dark == false
let lightTheme = true;

loadOrCreateCookie();
toggleTheme(true);
updateAllDateTimeLocale();

/* Create three promises that will race each other.
1. promise1 - This promise is only resolved if refresh rate is not 'Don't Refresh' ( > 0).
              It is resolved after the amount of the time the refresh rate is defined for passes.
              Then we will call fetch to reload the comments in page.
2. promise2 - This promise is resolved whenever the refresh rate drop down has changed value.
              This means that if the refresh rate is changed while we are waiting for a new refresh, the current
              refresh wait time is reset.
3. promise3 - This promise is resolved when the refresh floating button is clicked, and will immediately reload comments.
              It will only resolve if the refresh button is visible which is the user scrolls down on the comment 
              list past the refresh options.

*/

async function startRace (){
  // get current refresh rate if refresh rate < 0 we don't refresh.
  const refreshRateSelect = document.getElementById('refresh-rate-options');
  const refreshRateInt = refreshRateSelect.options[refreshRateSelect.selectedIndex].value;

  const promiseRefreshRate = new Promise(function(resolve) {
    // only resolve this promise if refresh rate is not set to don't refresh.'
    // resolve after the amount of time defined in the refresh rate drop down.
      if(refreshRateInt > 0 && !scrolledDown) {
        setTimeout(resolve, refreshRateInt, '1');
      }
      else {
        // resolve after 2 seconds so we are not calling too often to check if we have scrolled back up to the top
        setTimeout(resolve, 2000, '-3');;
      }
    
  });

  // second promise which is resolved whenever the refresh rate drop is changed.
  const promiseRefreshChanged = new Promise(function(resolve) {
      document.getElementById('refresh-rate-options').addEventListener('change', function(){
          const refreshRateSelect = document.getElementById('refresh-rate-options');
          const refreshRateInt = refreshRateSelect.options[refreshRateSelect.selectedIndex].value;
          updateRefreshRateCookie(refreshRateInt)
          resolve('-2');
      });
  });
  // third promise is the refresh button is clicked so refresh data right away.
  const promiseRefreshClicked = new Promise(function(resolve) {
    document.getElementById('refresh-btn').addEventListener('click', () => {
      resolve(2);
    });
  });

  Promise.race([promiseRefreshRate, promiseRefreshChanged, promiseRefreshClicked]).then(async function(value) {

  // Make the fetch call to Django server if we have a > 0 refresh rate
  // and we have not scrolled to where the manual refresh button is showing.
  // But always refresh if we were called from the refresh button directly (resolve code 2)
  if((refreshRateInt > 0 && value > 0 && !scrolledDown) || value == 2){
    // scroll to top of page when refresh button clicked
        if(value == 2){
          window.scrollTo({top: 0, behavior: 'smooth'});        
        }

        document.getElementById('spinner').style.display='';
        toggleTheme(true);

        const url = window.location.pathname;
        const query = {time_zone_offset: tz_offset};
        const fetchParams = new URLSearchParams(query);
        
        try{
          const data = await (await fetch(url + "?" + fetchParams, {
            method: 'GET'
          })).text();

          if(data){
            reloadComments(data);
          }
          else{
            document.getElementById('spinner').style.display='none';
            startRace();
          }
        } catch(error){
          console.log('Refreshing Comments Failed: ' + error);
          startRace();
        }
          

  }
  else{
      startRace();
    }
  });

}
// Entry point. This function is recalled often.
startRace();


// hide spinner and populate data from GET response to entire page.
// @param Data - GET response data, which will be our html template generated by views.py
async function reloadComments(data){
 
  document.getElementById('spinner').style.display='none';
  // remove parent div from previous new comments if they exist
  let newComments = document.getElementById('new-comments');
  if(newComments){
    newComments.replaceWith(...newComments.childNodes);
  }

  document.getElementById('inner-comment-list').insertAdjacentHTML('afterbegin', data);
  // make sure theme persists between fetch calls.
  toggleTheme(true);
  //document.getElementById('new-comments').style.display='none';
  //document.getElementById('new-comments').classList.replace('show', 'hide');
  updateNewDateTimeLocale();
  // small delay to allow render time for fade-in property to be updated.
  await new Promise(r => setTimeout(r, 100));
  document.getElementById('new-comments').classList.add('fade-in');

  // call entry method again.
  startRace();
}





/* Method toggleTheme. This method allows us the change the theme of the page from dark to light.
@param - keepSame - This means we just reload the current theme again, this is needed after the fetch call.
*/
function toggleTheme(keepSame) {

  const themeBtn      = document.getElementById('theme-btn');
  const icon          = document.getElementById('theme-btn-icon');
  const container     = document.getElementById('container');
  const comments      = document.getElementsByClassName('list-group-item');
  let tempThemeBool = false;
  // if currently set to light set to dark and vice versa.
  if(lightTheme && !keepSame){
    icon.classList.remove('fa-sun');
    icon.classList.add('fa-moon');
    themeBtn.classList.remove('btn-light');
    themeBtn.classList.add('btn-dark');
    container.classList.add('dark');
    document.body.classList.add('dark');
    tempThemeBool = false;
  }
  else if(!keepSame){
    icon.classList.remove('fa-moon');
    icon.classList.add('fa-sun');
    themeBtn.classList.remove('btn-dark');
    themeBtn.classList.add('btn-light');
    container.classList.remove('dark');
    document.body.classList.remove('dark');
    tempThemeBool = true;   
  }
    
  // set theme for comment bodys
  for(let i = 0; i < comments.length; i++){
      if(keepSame){
        if(lightTheme){
          comments[i].classList.remove('dark');
        }
        else{
          comments[i].classList.add('dark');
        }
      }
      else{
        if(lightTheme){
          comments[i].classList.add('dark');
        }
        else{
          comments[i].classList.remove('dark');
        }
      }   
  }
 
  //add body styles so it shows correctly during refresh
  if(keepSame){
    if(lightTheme){
      document.body.classList.remove('dark');
      icon.classList.remove('fa-moon');
      icon.classList.add('fa-sun');
      themeBtn.classList.remove('btn-dark');
      themeBtn.classList.add('btn-light');
    }
    else{
      document.body.classList.add('dark');
      icon.classList.remove('fa-sun');
      icon.classList.add('fa-moon');
      themeBtn.classList.remove('btn-light');
      themeBtn.classList.add('btn-dark');
    }
  }

  //update cookie after changes have been completed
  if(!keepSame){
    updateThemeCookie(tempThemeBool);
  }

}
/*Apply drop down styles when clicked
  Doing it this way rather than changing on refresh/theme button, 
  because the elements that need styles applied are only found when the drop down is at least clicked once.
  That means if a user were to change to dark theme 
  and then click the drop down for the first time, it would still be in light theme.
*/
function applyDropDownStyle(){

  const dropdownItems = document.getElementsByClassName('dropdown-item');
  const dropdownMenu  = document.getElementsByClassName('dropdown-menu')[0];
  
  if(lightTheme){
     dropdownMenu.classList.remove('dark'); 
     for(let i = 0; i < dropdownItems.length; i++){
          dropdownItems[i].classList.remove('dark');
     } 
  }
  else{
    dropdownMenu.classList.add('dark');
    for(let i = 0; i < dropdownItems.length; i++){
        dropdownItems[i].classList.add('dark');
    } 
  }
}

// use bootstrap select built-in event to trigger themes for drop down menus
//$('#refresh-rate-options').on('show.bs.select', applyDropDownStyle);
const refreshRateOptions = document.getElementById('refresh-rate-options');

refreshRateOptions.addEventListener('show.bs.select', applyDropDownStyle);



const commentDiv = document.getElementById('comments');
// Listen for when the scrolled window is below the header, 
// this is when we will show our manual refresh button on the bottom right
function scrollListener(){
  if(window.scrollY > commentDiv.offsetTop){
    scrolledDown = true;
    document.getElementById('refresh-btn').style.display = ''
  }
  else if(window.scrollY <= commentDiv.offsetTop){
    scrolledDown = false;
    document.getElementById('refresh-btn').style.display = 'none';
  }
} 

window.addEventListener('scroll', scrollListener);

/* create a theme cookie which lasts for 1 week, this allows the user to exit
and then still have the same theme when returing later
@param lightBool - boolean value for if this should be light or dark theme (light == true, dark == false)
*/
function updateThemeCookie(lightBool) {
  const date = new Date();
  date.setTime(date.getTime() + (7 * 24 * 60 * 60 * 1000));
  document.cookie = 'theme_cookie=' + lightBool + '; ' + 'expires=' + date.toUTCString() + ";path=/";
  lightTheme = lightBool;
}
/* create a refresh rate cookie which lasts for 1 week, this allows the user to exit
and then still have the same refresh rate when returing later
@param refreshRate - int value for how often the comments should refresh
*/
function updateRefreshRateCookie(refreshRate) {
  const date = new Date();
  date.setTime(date.getTime() + (7 * 24 * 60 * 60 * 1000));
  document.cookie = 'refresh_rate_cookie=' + refreshRate + '; ' + 'expires=' + date.toUTCString() + ";path=/";
  setRefreshRate(refreshRate);
}
// helper method which will check if the theme cookie exists or not.
// If it does exist apply existing theme else create new cookie and default to light theme.
function loadOrCreateCookie(){
  if(document.cookie.indexOf('theme_cookie=') >= 0){
     const boolStr = document.cookie
     .split('; ')
     .find(row => row.startsWith('theme_cookie='))
     .split('=')[1];
     lightTheme = (boolStr === 'true');
  }
  else{
      updateThemeCookie(true);
  }
  
  if(document.cookie.indexOf('refresh_rate_cookie=') >= 0){
    let refreshRateStr = document.cookie
    .split('; ')
    .find(row => row.startsWith('refresh_rate_cookie='))
    .split('=')[1];;
    setRefreshRate(refreshRateStr);
 }
 else{
    updateRefreshRateCookie("30000");
 }
}
/*
  Update every comment's date time into the  user's locale
*/
function updateAllDateTimeLocale(){
  $('.comment-time').each(function() {
    const commentTime = new Date(Date.parse($(this).html()));
    const commentTimeToLocale = commentTime.toLocaleString();
    $(this).replaceWith(commentTimeToLocale);
   });
}

/*
  Update new comment's date time into the  user's locale
*/
function updateNewDateTimeLocale(){
  $('#new-comments').children().each(function() {
    const commentTime = new Date(Date.parse($(this).children().html()));
    const commentTimeToLocale = commentTime.toLocaleString();
    $(this).children().replaceWith(commentTimeToLocale);
   });
}

/*
  set refresh rate if it is stored in a cookie
*/
function setRefreshRate(refreshRate){
  $('#refresh-rate-options').val(refreshRate);
}

