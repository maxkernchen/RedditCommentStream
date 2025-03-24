document.getElementById('spinner').style.display = 'none';
// get all bootstrap active submission cards displayed on the home page
const cards = document.getElementsByClassName('card');
let form_comment_url = document.getElementById('form_comment_url')

const offset = new Date().getTimezoneOffset();
// if device is mobile use active-card-mobile css to format active submissions for mobile
if(isMobile()){
  for(let i = 0; i < cards.length; i++){
    cards[i].classList.remove('active-card');
    cards[i].classList.add('active-card-mobile');
  }
  const inputForm = document.getElementById('input-form');
  inputForm.classList.remove('input-fields');
  inputForm.classList.add('input-fields-mobile');
}

// Loop through each card and add an event listener in its link element at the bottom.
// This event when triggered will fill in the form and submit it with the submission the card represents.
// It will also hide the input form and display a loading message/icon.
for(let i = 0; i < cards.length; i++){
    const cardTemp = cards[i];
    const hiddenLink = cardTemp.getElementsByClassName('hidden')[0].innerHTML;
    const link = cardTemp.getElementsByClassName('link')[0]
    link.addEventListener('click', function (event) {
      document.getElementById('all_input_container').style.display = 'none';

      document.getElementById('spinner').style.display='';
  
      const formInput = document.getElementById('reddit_url');
      formInput.value = hiddenLink;
      // this call triggers submit event listener too.
      form_comment_url.requestSubmit();
      
    });
}



form_comment_url.addEventListener('submit', function( event ) {
  event.preventDefault();
  const formInput = document.getElementById('reddit_url');
    
  form_comment_url.insertAdjacentHTML('beforeend', '<input type="hidden" name="time_zone_offset" value="' + offset + '" >');
  // change url to include submission id
  form_comment_url.setAttribute('action', getSubmissionId(formInput.value));
  form_comment_url.submit();
});

// add the submission id to the processing url. This is so we have a unique url which allows the user to open
// multiple sessions for different streams of comments.
function getSubmissionId(redditUrl){
    let subId = "/process-url/";
    let index = redditUrl.toLowerCase().search("comments")
    if(index >= 0){
      const start = index + 9;
      const end = redditUrl.indexOf("/", start);
      // it's okay to be missing ending slash
      if(end == -1){
        subId += redditUrl.substring(start, redditUrl.length + 1);
      }
      else{
        subId += redditUrl.substring(start, end) + "/";
      }
    }
    // assume user has just passed in the submission id, if it's not valid views.py will handle it
    else{
        subId += redditUrl + "/";
    }
    return subId;
}
// check if device is mobile via user agent
function isMobile() {
  return /Android|webOS|iPhone|iPad|iPod|IEMobile|BlackBerry|Opera Mini/i.test(navigator.userAgent);
}



  