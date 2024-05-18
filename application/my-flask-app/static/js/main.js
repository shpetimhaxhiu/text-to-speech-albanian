// Handle form submission
document.getElementById('text-to-speech-form').addEventListener('submit', function(event) {
  event.preventDefault();

  // Get form values
  var text = document.getElementById('text-input').value;
  var lang = document.getElementById('lang-select').value;
  var gender = document.getElementById('gender-select').value;

  // Make request to /say endpoint
  fetch('/say?text=' + encodeURIComponent(text) + '&lang=' + encodeURIComponent(lang) + '&gender=' + encodeURIComponent(gender))
    .then(function(response) {
      return response.blob();
    })
    .then(function(blob) {
      // Create audio element and play the speech
      var audio = new Audio(URL.createObjectURL(blob));
      audio.play();
    })
    .catch(function(error) {
      console.error('Error:', error);
    });
});