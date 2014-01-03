(function (spawnsong) {
  "use strict";

  function SnippetView(el) {
    this.beatLocations = window.SONGSPAWN_BEAT_LOCATIONS;
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
  
  function UploadView(el) {
  }

  UploadView.prototype = {
    ready: function () {
      if (!(new XMLHttpRequest().upload)) {
        // Browser doesn't support XHR2, fall back to standard HTML form
        return;
      }
      $('#uploadForm').ajaxForm({
        dataType: 'json',
        data: {xhr: true},
        beforeSubmit: function (arr, $form, option) {
          $('#uploadStatus').fadeIn();
          $('#uploadForm button').attr('disabled', true);
          // Disabling the inputs here breaks jquery.form, so disable
          // them in a ms
          setTimeout(function () {
            $('#uploadForm :input').attr('disabled', true);
          }, 1);
          // TOOD: Check file type
        },
        uploadProgress: function (evt, position, total, percentComplete) {
          $('#uploadStatus .progress-bar')
            .attr('aria-valuenow',percentComplete)
            .css({width: percentComplete + '%'})
            .find('.sr-only').text(percentComplete + '% complete');
        },
        error: function () {
          alert("Upload failed!");
        },
        success: function (response) {
          if (response.redirectTo) {
            document.location.href = response.redirectTo;
          } else {
            $('#uploadForm').html($('#uploadForm', response.html).html());
          }
        }
      });
    }
  };

  var views = {
    '#snippetView': SnippetView,
    '#uploadView': UploadView
  };

  $(document).ready(function () {
    for (var selector in views) {
      var el = $(selector);
      if (el.length) {
        new views[selector](el).ready();
      }
    }
  });
  
})(window.spawnsong = {});
