(function (spawnsong) {
  "use strict";

  function SnippetView(el) {
    this.beatLocations = window.SONGSPAWN_BEAT_LOCATIONS;
    this.ready();
  }

  SnippetView.prototype = {
    ready: function () {
      var _this = this;
      this.setHeights();
      setTimeout(function () {
        _this.setHeights();
      }, 500);
      this.setupMediaElementPlayer();
    },
    setupMediaElementPlayer: function ( ) {
      var _this = this;
      $('audio').mediaelementplayer({
        videoHeight: 0,
        features: ['playpause','progress','current','duration', 'volume'],
        success: function (mediaElement, domObject) { 
          
          // add event listener
          mediaElement.addEventListener('timeupdate', function(e) {
            
            console.log(mediaElement.currentTime);
            $('#playerImage').show();
            _this.beatLocations.forEach(function (location) {
              if (Math.abs(mediaElement.currentTime-location) < 0.15) {
                console.log('BEAT', Math.abs(mediaElement.currentTime-location));
                $('#playerImage').hide();
              }
            });
            // document.getElementById('current-time').innerHTML = mediaElement.currentTime;
            
          }, false);
          
          
        },
      });
    },
    // AJAXify the comment posting (progressively enhanced)
    postComment: function () {
      var text = $('#commentText').val().trim();
      if (text === '') return;
      var csrf = $('input[name=csrfmiddlewaretoken]').val();
      $('#addcomment').attr('disabled','disabled');
      $.ajax(document.location.href, {
        data: {comment: text, badger: ''},
        type: 'POST',
        headers: {'X-CSRFToken': csrf},
        success: function (data) {
          $('#comments').replaceWith($('#comments', data));
        }
      });
    },
    
    // Fix up the heights of the page alements after page load
    setHeights: function () {
      var playerHeight = $('#playerContainer').height();
      $('#detailsContainer').css({height: playerHeight + 'px'});
      $('#comments ul').css({height: playerHeight-$('#comments ul').position().top-50});
    },

  };

  var views = {
    '#snippetView': SnippetView
  };

  $(document).ready(function () {
    for (var selector in views) {
      var el = $(selector);
      if (el.length) {
        new views[selector](el);
      }
    }
  });
  
})(window.spawnsong = {});
