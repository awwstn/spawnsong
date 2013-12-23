(function (spawnsong) {
  "use strict";
  
  spawnsong.snippet = {
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

  $(document).ready(function () {
    spawnsong.snippet.setHeights();
    setTimeout(function () {
      spawnsong.snippet.setHeights();
    }, 500);

    $('audio').mediaelementplayer({
      videoHeight: 0,
      features: ['playpause','progress','current','duration', 'volume']
    });
  });
})(window.spawnsong = {});
