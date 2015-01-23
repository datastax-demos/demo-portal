$(document).ready(function () {
    $('[data-toggle="confirmation"]').confirmation({
        btnOkLabel: 'Destroy',
        placement: 'right',
        title: 'Remove Admin?',
        container: 'body'
    });
});
