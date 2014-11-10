$(document).ready(function () {
    $('label').tooltip();
    $('.reveal').click(function (e) {
        var parent = $(this).parent().parent();
        var currentHeight = parent[0].offsetHeight + 'px';
        var minHeight = parent.css('min-height');
        var openHeight = parent[0].scrollHeight + 'px';

        if (minHeight == currentHeight) {
            parent.animate({"height": openHeight}, {duration: "slow" });
        } else {
            parent.animate({"height": minHeight}, {duration: "slow" });
        }
        e.preventDefault();
    });
});
