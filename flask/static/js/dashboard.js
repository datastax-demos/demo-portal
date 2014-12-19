function add_to_table(row, table, complete, status) {
    if (complete) {
        //row.addClass('success');
    } else if (status == 'Terminating.') {
        row.addClass('danger');
    } else {
        //row.addClass('warning');
    }
    row.appendTo(table);
}

function load_server_information() {

    $.ajax('server-information')
        .done(function (clusters) {
            var $tr = $('<tr>').append(
                $('<th>').text(''),
                $('<th>').text('Launch Date'),
                $('<th>').text('Cluster Name'),
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

            $.each(clusters, function (cluster_name, cluster) {
                var ip_addresses = [];
                var reservation_ids = [];
                var app_address = '';
                var opscenter_address = '';

                $.each(cluster, function (j, instance) {
                    if (instance.tags.product == 'demo') {
                        app_address = instance.ip_address + ':' + instance.tags['app_port'];
                    } else if (instance.tags.product == 'opscenter') {
                        opscenter_address = instance.ip_address + ':8888';
                    } else if ('automaton-opscenter' in instance.tags) {
                        opscenter_address = instance.ip_address + ':8888';
                        ip_addresses.push(instance.ip_address);
                    } else {
                        ip_addresses.push(instance.ip_address);
                    }
                    reservation_ids.push(instance.reservation_id);
                });

                var instance = cluster[0];
                var complete = instance.tags['status'] == 'Complete.';
                var failure = instance.tags['status'].toLowerCase().indexOf('fail') > -1;
                var $tr = $('<tr>').append(
                    $('<td>').text(instance.email),
                    $('<td>').text(instance.launch_time.replace('T', ' ')),
                    $('<td>').text(function(){
                        if ('ctool_name' in instance.tags)
                            return instance.tags['ctool_name'];
                        return instance.tags['Name'];
                    }),
                    $('<td>').html($('<span>', {
                        text: instance.tags['ttl'],
                        class: 'ttl',
                        'title': 'Update TTL',
                        'data-placement': 'top',
                        'data-toggle': 'popover',
                        'data-content': '<form action="ttl" method="post">' +
                            '<input type="hidden" name="reservation-ids"' +
                            'value="' + reservation_ids.join(',') + '">' +
                            '<input type="number" class="ttl-input" name="ttl"' +
                                   'value="' + instance.tags['ttl'] + '">' +
                            '<button>Update</button></form>'
                    })),
                    $('<td>').text(cluster.length)
                );
                if (instance.tags['app_port'] && instance.ip_address && complete) {
                    $tr.append(
                        $('<td>').html($('<a>', {
                            href: 'http://' + app_address,
                            text: app_address,
                            target: '_blank'
                        }))
                    );
                } else {
                    $tr.append(
                        $('<td>')
                    );
                }
                if (instance.ip_address && complete) {
                    if ('ctool_name' in instance.tags) {
                        $tr.append(
                            $('<td>').html($('<a>', {
                                'class': 'tooltip-gen',
                                'href': 'http://' + opscenter_address,
                                'text': opscenter_address,
                                'title': 'Affected by DEMO-31. Manual cluster entry required.',
                                'data-toggle': 'tooltip',
                                'data-placement': 'top',
                                'target': '_blank'
                            }))
                        );
                    } else {
                        $tr.append(
                            $('<td>').html($('<a>', {
                                href: 'http://' + opscenter_address,
                                text: opscenter_address,
                                target: '_blank'
                            }))
                        );
                    }
                } else {
                    $tr.append(
                        $('<td>')
                    );
                }

                if (instance.ip_address) {
                    $tr.append($('<td>').html(ip_addresses.join('<br/>')));
                } else {
                    $tr.append($('<td>'));
                }

                $tr.append(
                    $('<td>').html($('<span>', {
                        'text': '$ ' + parseInt(instance.tags['ttl'])
                                * instance.reservation_size * 0.420,
                        'class': 'max-cost',
                        'title': 'The cost of running this cluster for '
                                 + instance.tags['ttl'] + ' hours',
                        'data-toggle': 'tooltip',
                        'data-placement': 'top'
                    })),
                    $('<td>').html($('<a>', {
                        id: 'confirmation_' + cluster_name,
                        'data-toggle': 'confirmation',
                        href: '/kill/' + reservation_ids.join(','),
                        text: 'X'
                    }))
                );
                add_to_table($tr, '#launch-table', complete, instance.tags['status']);

                if (instance.ip_address) {
                    var $tr = $('<tr>').addClass('info-row').append(
                        $('<td>').addClass('info-row'));
                    var $td = $('<td colspan="2">').addClass('info-row').html('<b>Status:</b> ' + instance.tags['status']);
                    if (complete) {
                        $td.addClass('success');
                    } else if (failure) {
                        $td.addClass('danger');
                    } else {
                        $td.addClass('warning');
                    }
                    $tr.append($td);
                    if ('ctool_name' in instance.tags){
                        $tr.append($('<td colspan="8">').addClass('info-row').html(
                                '<b>Direct Download:</b> <a href="/pemfile?cloud-option=ec2&cluster-id=' + instance.tags['Name'] + '">' +
                                    instance.tags['Name'] + '.pem</a><br>' +
                                '<b><a href="/static/bin/demo-pem">demo-pem</a> Command:</b> ' +
                                '<input class="command1" value="demo-pem ec2 ' +
                                    instance.tags['Name'] + '" /><br>' +
                                '<b>Connect:</b> <input class="command2" value="ssh ' +
                                '-i ~/.datastax/demos/ctool/' + instance.tags['Name'] + '.pem' +
                                ' -o StrictHostKeyChecking=no' +
                                ' automaton@' + instance.ip_address + '">')
                        );
                    } else {
                        $tr.append($('<td colspan="8">').addClass('info-row').html('<b>Connect:</b> ' +
                            '<input class="command2" value="ssh ' +
                                '-i ~/.datastax/demos/demo-launcher.pem' +
                                ' -o StrictHostKeyChecking=no' +
                                ' ubuntu@' + instance.ip_address + '">')
                        );
                    }
                    add_to_table($tr, '#launch-table', complete, instance.tags['status']);
                }

                // display confirmation messages when attempting to destroy machines
                $('#confirmation_' + cluster_name).confirmation({
                    btnOkLabel: 'Destroy',
                    placement: 'left',
                    href: '/kill/' + reservation_ids.join(','),
                    title: 'Destroy cluster?'
                });
            });

            $('.command1').click(function() {
                $(this).select();
            });

            $('.command2').click(function() {
                $(this).select();
            });

            $('.ttl').popover({
                html: true
            });
            $('.max-cost').tooltip();
            $('.tooltip-gen').tooltip();
        })
        .fail(function (response) {
            // alert('error');
            console.log(response);
            console.log('Ensure you\'ve run `source set_credentials.sh`.');
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
