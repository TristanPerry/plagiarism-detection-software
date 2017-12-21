var guid = (function() {
  function s4() {
    return Math.floor((1 + Math.random()) * 0x10000)
               .toString(16)
               .substring(1);
  }
  return function() {
    return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
           s4() + '-' + s4() + s4() + s4();
  };
})();

function trim(str) {
    return str.replace(/ /g, '');
}

function showLightbox(url) {
    $("#innerImage").html('Loading image...');
    $("#pageLightbox").show(300);

    $('<img src="'+ url +'">').load(function() {
        $("#innerImage").html('');
        $(this).appendTo('#innerImage');
    });
}

function hideLightbox() {
    $("#innerImage").html('');
    $("#pageLightbox").hide(300);
}

$(function() {
    $("#pageLightbox").click(function() {
        hideLightbox();
    });

    $("#show-menu").change(function() {
        if ($(this).is(':checked')) {
            $(".mainNav").show(250);
        } else {
            $(".mainNav").hide(250);
        }
    })

    $(document).keyup(function(e) {
      if (e.keyCode == 27) hideLightbox();
    });

    $(".lightboxImg").click(function() {
       showLightbox($(this).data('full-url'));
    });

    $('header nav ul li ul').hover(function() {
       $(this).prev('header nav ul li a').addClass("parentDropdownHover");
    }, function() {
        $(this).prev('header nav ul li a').removeClass("parentDropdownHover");
    });

    $('#loginlink').click(function() {
      $('#innerlogin').toggle(250);
    });

    if ($( window ).width() > 800) {
        var highestBox = $('#footer-initial #social-block').height() + 200;
        $('#footer-initial section').height(highestBox);
    }

    // Thanks http://osvaldas.info/elegant-css-and-jquery-tooltip-responsive-mobile-friendly
    var targets = $( '[rel~=tooltip]' ),
        target  = false,
        tooltip = false,
        title   = false;

    targets.bind( 'mouseenter', function() {
        target  = $( this );
        tip     = target.attr( 'title' );
        tooltip = $( '<div id="tooltip"></div>' );

        if( !tip || tip == '' )
            return false;

        target.removeAttr( 'title' );
        tooltip.css( 'opacity', 0 )
               .html( tip )
               .appendTo( 'body' );

        var init_tooltip = function() {
            if( $( window ).width() < tooltip.outerWidth() * 1.5 )
                tooltip.css( 'max-width', $( window ).width() / 2 );
            else
                tooltip.css( 'max-width', 340 );

            var pos_left = target.offset().left + ( target.outerWidth() / 2 ) - ( tooltip.outerWidth() / 2 ),
                pos_top  = target.offset().top - tooltip.outerHeight() - 20;

            if( pos_left < 0 ) {
                pos_left = target.offset().left + target.outerWidth() / 2 - 20;
                tooltip.addClass( 'left' );
            }
            else
                tooltip.removeClass( 'left' );

            if( pos_left + tooltip.outerWidth() > $( window ).width() ) {
                pos_left = target.offset().left - tooltip.outerWidth() + target.outerWidth() / 2 + 20;
                tooltip.addClass( 'right' );
            }
            else
                tooltip.removeClass( 'right' );

            if( pos_top < 0 ) {
                var pos_top  = target.offset().top + target.outerHeight();
                tooltip.addClass( 'top' );
            }
            else
                tooltip.removeClass( 'top' );

            tooltip.css( { left: pos_left, top: pos_top } )
                   .animate( { top: '+=10', opacity: 1 }, 50 );
        };

        init_tooltip();
        $( window ).resize( init_tooltip );

        var remove_tooltip = function() {
            tooltip.animate( { top: '-=10', opacity: 0 }, 50, function()
            {
                $( this ).remove();
            });

            target.attr( 'title', tip );
        };

        target.bind( 'mouseleave', remove_tooltip );
        tooltip.bind( 'click', remove_tooltip );
    });
});