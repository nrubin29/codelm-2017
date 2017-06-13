$(document).ready(function() {
    var script = $('#platform-script');
    var timestamp = parseFloat(script.attr('data-ending-time'));

    $('.tab-content').hide();

    countdown(
        function(ts) {
            if (ts.value <= 0 && script.attr('data-countdown') == 'True') {
                location.reload();
            }

            else {
                $('#timer').html(ts.toHTML());
            }
        },
        new Date(timestamp * 1000)
        // countdown.HOURS | countdown.MINUTES | countdown.SECONDS
    );

    $('.tab').click(function() {
        var ths = $(this);

        ths.parent().children().each(function() {
            $(this).removeClass('active');
        });

        ths.addClass('active');

        ths.closest('.tab-group').find('.tab-content.active').removeClass('active').slideUp('400', function() {
            $(ths.attr('href')).addClass('active').slideDown('400', function() {
                if (ths.hasClass('code-tab')) {
                    $(ths.attr('href')).find('textarea').data('codeMirror').refresh();
                }
            });
        });
    });

    $('.tabs').each(function() {
        var first = $(this).children('.active');

        if (first.length == 0) {
            first = $(this).children().first();
            first.addClass('active');
        }

        $(first.attr('href')).addClass('active').show();
    });
});