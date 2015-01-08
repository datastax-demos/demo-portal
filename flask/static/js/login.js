// borrowed from: http://stackoverflow.com/a/439578/2458243
function getQueryParams() {
    qs = document.location.search;
    qs = qs.split("+").join(" ");
    var params = {},
        tokens,
        re = /[?&]?([^=]+)=([^&]*)/g;

    while (tokens = re.exec(qs)) {
        params[decodeURIComponent(tokens[1])]
            = decodeURIComponent(tokens[2]);
    }

    return params;
}

$( document ).ready(function() {

    $('#login').click(function() {
        $("#login").addClass('active');
        $("#request-password").removeClass('active');
        $("#login-form").attr('action', 'login');
        $("#password-group").show();
    });

    $('#request-password').click(function() {
        $("#request-password").addClass('active');
        $("#login").removeClass('active');
        $("#login-form").attr('action', 'request-password');
        $("#password-group").hide();
    });

    $('#inputEmail').val(getQueryParams().email);

    if (getQueryParams().email) {
        $('#login').click();
    }

});
