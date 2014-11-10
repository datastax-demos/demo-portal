function add_to_table(row, table, complete, status) {
    if (complete) {
        row.addClass('success');
    } else if (status == 'Terminating.') {
        row.addClass('danger');
    } else {
        row.addClass('warning');
    }
    row.appendTo(table);
}

function load_server_information() {

    $.ajax('server-information')
        .done(function (reservations) {
            var $tr = $('<tr>').append(
                $('<th>').text(''),
                $('<th>').text('Launch Date'),
                $('<th>').text('Demo'),
                $('<th>').text('TTL'),
                $('<th>').text('Cluster Size'),
//                $('<th>').text('State'),
                $('<th>').text('Demo Addresses'),
                $('<th>').text('OpsCenter'),
                $('<th>').text('IP Addresses'),
                $('<th>').text('Max Cost'),
                $('<th>').text('')
            );
            $('#launch-table').html($tr);

            $.each(reservations, function (reservation, instances) {
                $.each(instances, function (j, instance) {
                    if (j == 0) {
                        complete = instance.tags['status'] == 'Complete.';
                        app_address = instance.ip_address + ':' + instance.tags['app_port'];
                        opscenter_address = instance.ip_address + ':8888';
                        var $tr = $('<tr>').append(
//                            $('<td>').text(instance.tags['launch_time']),
                            $('<td>').text(instance.email),
                            $('<td>').text(instance.launch_time.replace('T', ' ')),
                            $('<td>').text(instance.tags['name']),
                            $('<td>').html($('<span>', {
                                text: instance.tags['ttl'],
                                class: 'ttl',
                                'title': 'Update TTL',
                                'data-placement': 'top',
                                'data-toggle': 'popover',
                                'data-content': '<form action="ttl" method="post">' +
                                    '<input type="hidden" name="reservation-id"' +
                                    'value="' + reservation + '">' +
                                    '<input type="number" class="ttl-input" name="ttl"' +
                                           'value="' + instance.tags['ttl'] + '">' +
                                    '<button>Update</button></form>'
                            })),
                            $('<td>').text(instance.reservation_size)
//                            $('<td>').text(instance.state)
                        );
                        if (instance.ip_address && complete) {
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
                                * instance.reservation_size * 0.420),
                            $('<td>').html($('<a>', {
                                id: 'confirmation_' + reservation,
                                'data-toggle': 'confirmation',
                                href: '/kill/' + reservation,
                                text: 'X'
                            }))
                        );
                        add_to_table($tr, '#launch-table', complete, instance.tags['status']);

                        if (instance.ip_address) {
                            var $tr = $('<tr>').append(
                                $('<td>').addClass('info-row'),
                                $('<td colspan="2">').addClass('info-row').text(instance.tags['status']),
                                $('<td colspan="8">').addClass('info-row').text('ssh -i ~/.ssh/demo-launcher.pem' +
                                    ' -o StrictHostKeyChecking=no' +
                                    ' ubuntu@' + instance.ip_address)
                            );
                            add_to_table($tr, '#launch-table', complete, instance.tags['status']);
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

            $('.ttl').popover({
                html: true
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
