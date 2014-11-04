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

});
