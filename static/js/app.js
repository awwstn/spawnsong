(function (spawnsong) {
  "use strict";
  
  ////
  // Orders
  ////

  function SnippetOrders(el) {
    this.orderEl = el;
    this.stripePublicKeys = window.STRIPE_PUBLIC_KEY; // set in base.html
    this.price = window.SONGSPAWN_SNIPPET_DETAILS.price;
    this.title = window.SONGSPAWN_SNIPPET_DETAILS.title;
    this.userEmail = window.LOGGED_IN_USER_EMAIL;
    this.snippetId = window.SONGSPAWN_SNIPPET_DETAILS.id;
  }

  SnippetOrders.prototype = {
    ready: function () {
      this.orderEl.click(_.bind(this.showCheckout, this));
    },
    showCheckout: function () {
      var _this = this;
      var handler = window.StripeCheckout.configure({
        key: this.stripePublicKeys,
        token: function(token, args) {
          _this.orderEl.attr('disabled', true);
          _this.orderEl.text("Processing...");
          $('#orderForm [name=email]').val(token.email);
          $('#orderForm [name=token]').val(token.id);
          $('#orderForm').submit();
          // Use the token to create the charge with a server-side script.
        }
      });

      handler.open({
        name: 'Songspawn',
        description: 'Pre Order "' + this.title + '"',
        email: this.userEmail,
        amount: this.price
      });
    }
  };

  ////
  // Player
  ////
  
  function SnippetPlayer(el) {
    this.beatLocations = window.SONGSPAWN_SNIPPET_DETAILS.beats;
    this.visualisation = window.SONGSPAWN_SNIPPET_DETAILS.visualisation_effect;
  }

  SnippetPlayer.prototype = {
    ready: function () {
      this.setupMediaElementPlayer();
    },
    setupMediaElementPlayer: function ( ) {
      var _this = this;
      $('audio').mediaelementplayer({
        videoHeight: 0,
        features: ['playpause','progress','current','duration', 'volume'],
        success: function (mediaElement, domObject) { 
          mediaElement.addEventListener('playing', function(e) {
            $('#playButtonOverlay').fadeOut();
            if (_this.visualisation === "pulsate") {
              _this.runVisualisation(mediaElement);
            }
          });

          $('#playerContainer').click(function () {
            if (mediaElement.paused || mediaElement.ended) {
              mediaElement.play();
            } else {
              mediaElement.pause();
            }
          });
        },
      });
    },

    runVisualisation: function (mediaElement) {
      var _this = this;
      var beats = _.clone(this.beatLocations);
      function update() {
        var beat;
        if (mediaElement.paused || mediaElement.ended) return;
        while(beats[0] < mediaElement.currentTime) {
          beat = beats.shift();
        }
        // 0.1 seconds before the beat we add the class, the
        // css transition time is set to 0.1 so it will reach its peak at
        // the same time as the beat.
        if (beats[0] && beats[0]-mediaElement.currentTime < 0.1) {
          $('#playerImage').addClass('beat');
        } else {
          $('#playerImage').removeClass('beat');
        }
        window.requestAnimationFrame(update);
      }
      // _.defer(update);
      window.requestAnimationFrame(update);
    }
  };

  ////
  // Comments
  ////
  
  function SnippetComments(el) {
  }

  SnippetComments.prototype = {
    ready: function () {
      $('#addcomment').click(_.bind(this.postComment, this));
    },

    /////
    // Comments
    ////
    
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
  };
    

  ////
  // CSS Fixes
  ////
  
  function SnippetViewCSS(el) {
  }

  SnippetViewCSS.prototype = {
    ready: function () {
      var _this = this;
      setInterval(function () {
        _this.setHeights();
      }, 500);
      this.setHeights();
    },
    // Fix up the heights of the page alements after page load
    setHeights: function () {
      var playerHeight = $('#playerContainer').height();
      $('#detailsContainer').css({height: playerHeight + 'px'});
      if ($('#comments ul').length) {
        $('#comments ul').css({height: playerHeight-$('#comments ul').position().top-50});
      }
    },

  };
  
  /////
  // Uploads (used for both snippet and full song upload)
  ////
  
  function UploadForm(el) {
  }

  UploadForm.prototype = {
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
          if (percentComplete > 99.99) {
            // Once we get to 100% upload it might still take a while
            // on the server, so add animated stripes to the progress
            // bar so that the user doesn't think it has stalled
            $('#uploadStatus .progress').addClass('progress-striped').addClass('active');
          }
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
    '#order': SnippetOrders,
    '#playerContainer': SnippetPlayer,
    '#comments': SnippetComments,
    '#snippetView': SnippetViewCSS,
    '#uploadForm': UploadForm
  };

  $(document).ready(function () {
    for (var selector in views) {
      var el = $(selector);
      if (el.length) {
        new views[selector](el).ready(el);
      }
    }
  });
  
})(window.spawnsong = {});

var a = 1;
