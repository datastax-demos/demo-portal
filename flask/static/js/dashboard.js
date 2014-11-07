function load_server_information() {

    $.ajax('server-information')
        .done(function (reservations) {
            var $tr = $('<tr>').append(
                $('<th>').text(''),
                $('<th>').text('Launch Date'),
                $('<th>').text('Demo'),
                $('<th>').text('TTL'),
                $('<th>').text('Cluster Size'),
                $('<th>').text('State'),
                $('<th>').text('Demo Addresses'),
                $('<th>').text('OpsCenter'),
                $('<th>').text('IP Addresses'),
                $('<th>').text('Cost'),
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
                            $('<td>').text(instance.email),
                            $('<td>').text(instance.launch_time.replace('T', ' ')),
                            $('<td>').text(instance.tags['name']),
                            $('<td>').text(instance.tags['ttl']),
                            $('<td>').text(instance.reservation_size),
                            $('<td>').text(instance.state)
                        );
                        if (instance.ip_address) {
                            $tr.append(
                                $('<td>').html($('<a>', {
                                    href: 'http://' + app_address,
                                    text: app_address,
                                    target: '_blank'
                                })),
                                $('<td>').html($('<a>', {
                                    href: 'http://' + opscenter_address,
                                    text: opscenter_address,
                                    target: '_blank'
                                }))
                            );
                        } else {
                            $tr.append(
                                $('<td>'),
                                $('<td>')
                            );
                        }
                        $tr.append(
                            $('<td>').text(instance.ip_address),
                            $('<td>').text('$ ' + parseInt(instance.tags['ttl'])
                                * 0.840 * instance.reservation_size),
                            $('<td>').html($('<a>', {
                                id: 'confirmation_' + reservation,
                                'data-toggle': 'confirmation',
                                href: '/kill/' + reservation,
                                text: 'X'
                            }))
                        );
                        $tr.appendTo('#launch-table');
                        if (instance.ip_address) {
                            var $tr = $('<tr>').append(
                                $('<td>'),
                                $('<td>'),
                                $('<td colspan="9">').text('ssh -i ~/.ssh/demo-launcher.pem' +
                                    ' -o StrictHostKeyChecking=no' +
                                    ' ubuntu@' + instance.ip_address)
                            );
                            $tr.appendTo('#launch-table');
                        }

                        // display confirmation messages when attempting to destroy machines
                        $('#confirmation_' + reservation).confirmation({
                            btnOkLabel: 'Destroy',
                            placement: 'left',
                            href: '/kill/' + reservation,
                            title: 'Destroy cluster?'
                        });
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

    setInterval(load_server_information, 10000);
});
