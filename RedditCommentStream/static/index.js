document.getElementById('spinner').style.display = 'none';

// get all active submission cards
const active_submissions = document.getElementsByClassName('column');
const form_comment_url = document.getElementById('form-comment-url')
// set up dropdown event
const setting_dropdown = document.getElementById('setting-dropdown');
setting_dropdown.addEventListener('click', function(event){
  event.stopPropagation();
  setting_dropdown.classList.toggle('is-active');
});

const tz_offset = new Date().getTimezoneOffset();
const icon_light = document.getElementById('icon-light');
const icon_dark = document.getElementById('icon-dark');
const icon_system = document.getElementById('icon-system');
// get localStorage saved theme if it exists, if not we'll just use the system value
const theme_val_storage = localStorage.getItem('theme-val');
theme_val_storage ? toggleTheme(theme_val_storage) : toggleTheme('system');


// Loop through each card and add an event listener in its link element at the bottom.
// This event when triggered will fill in the form and submit it with the submission the card represents.
// It will also hide the input form and display a loading message/icon.
for(let i = 0; i < active_submissions.length; i++){
    const active_sub = active_submissions[i];
    const hidden_link = active_sub.getElementsByClassName('hidden')[0].innerHTML;
    const link = active_sub.getElementsByClassName('link')[0]

    link.addEventListener('click', function (event) {
      const form_input = document.getElementById('reddit_url');
      form_input.value = hidden_link;
      // this call triggers submit event listener too.
      form_comment_url.requestSubmit();
    });
}


form_comment_url.addEventListener('submit', function( event ) {
  event.preventDefault();
  // display spinner
  document.getElementById('all-input-container').style.display = 'none';
  document.getElementById('spinner').style.display='';

  const form_input = document.getElementById('reddit_url');
  form_comment_url.insertAdjacentHTML('beforeend', '<input type="hidden" name="time_zone_offset" value="' + tz_offset + '" >');
  // change url to include submission id
  form_comment_url.setAttribute('action', getSubmissionId(form_input.value));
  form_comment_url.submit();
});

// add the submission id to the processing url. This is so we have a unique url which allows the user to open
// multiple sessions for different streams of comments.
function getSubmissionId(reddit_url){
    let sub_id = "/process-url/";
    let index = reddit_url.toLowerCase().search("comments")
    if(index >= 0){
      const start = index + 9;
      const end = reddit_url.indexOf("/", start);
      // it's okay to be missing ending slash
      if(end == -1){
        sub_id += reddit_url.substring(start, reddit_url.length + 1);
      }
      else{
        sub_id += reddit_url.substring(start, end) + "/";
      }
    }
    // assume user has just passed in the submission id, if it's not valid views.py will handle it
    else{
        sub_id += reddit_url + "/";
    }
    return sub_id;
}

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



  