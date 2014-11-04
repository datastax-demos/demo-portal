function load_server_information() {

    $.ajax('server-information')
        .done(function (reservations) {
            var $tr = $('<tr>').append(
                $('<th>').text('Launch Date'),
                $('<th>').text('Demo'),
                $('<th>').text('TTL'),
                $('<th>').text('Cluster Size'),
                $('<th>').text('State'),
                $('<th>').text('Demo Addresses'),
                $('<th>').text('OpsCenter'),
                $('<th>').text('IP Addresses'),
                $('<th>').text('')
            );
            $('#launch-table').html($tr);

            $.each(reservations, function (reservation, instances) {
                $.each(instances, function (j, instance) {
                    if (j == 0) {
                        app_address = instance.ip_address + ':' + instance.tags['app_port'];
                        opscenter_address = instance.ip_address + ':8888';
                        var $tr = $('<tr>').append(
//                            $('<td>').text(instance.tags['launch_time']),
                            $('<td>').text(instance.launch_time.replace('T', ' ')),
                            $('<td>').text(instance.tags['name']),
                            $('<td>').text(instance.tags['ttl']),
                            $('<td>').text(instance.reservation_size),
                            $('<td>').text(instance.state),
                            $('<td>').html($('<a>', {
                                href: 'http://' + app_address,
                                text: app_address,
                                target: '_blank'
                            })),
                            $('<td>').html($('<a>', {
                                href: 'http://' + opscenter_address,
                                text: opscenter_address,
                                target: '_blank'
                            })),
                            $('<td>').text(instance.ip_address),
                            $('<td>').html($('<a>', {
                                href: '/kill/' + reservation,
                                text: 'X'
                            }))
                        );
                        $tr.appendTo('#launch-table');
                    }
                });
            });
        })
        .fail(function (response) {
            // alert('error');
            console.log(response);
        });
}

$(document).ready(function () {
    $('#launch-form').bootstrapValidator({
        message: 'This value is not valid',
        feedbackIcons: {
            valid: 'glyphicon glyphicon-ok',
            invalid: 'glyphicon glyphicon-remove',
            validating: 'glyphicon glyphicon-refresh'
        }
    });
    load_server_information();
    setInterval( load_server_information, 10000 );
});
