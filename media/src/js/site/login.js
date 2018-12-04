
$(function() {
    function scroll_to_create_account() {
        var formTop = $('#create-account').offset().top;
        var pageStart = $('body').css('padding-top').replace('px', '');
        $('html, body').animate({scrollTop: formTop - pageStart - 20}, 300);
    }

    if(window.location.hash == '#create-account') {
        scroll_to_create_account();
    }

    $(document).ready( function() {
        if ($('.auto-scroll-target').length > 0) {
            scroll_to_create_account();
        }
    });
});

