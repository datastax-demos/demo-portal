function create_advanced_datacenter_options() {
    for (var i = 1; i < 7; i++) {
        var thisDiv = $('.dc' + i + '-div');
        var input = $('<input>', {
            'id': 'dc' + i + '-name',
            'name': 'dc' + i + '-name',
            'value': 'DC' + i,
            'class': 'datacenter-input',
            'type': 'text'
        });
        thisDiv.append(input);

        var table = $('<table>', {
            'class': 'advanced-setup-table'
        });
        table.append($('<tr>').append(
            $('<th>', {
                'class': 'cassandra',
                'text': 'C*'
            }),
            $('<th>').html($('<img>', {
                'src': '/static/img/spark.png',
                'class': 'service-image'
            })),
            $('<th>').html($('<img>', {
                'src': '/static/img/solr.png',
                'class': 'service-image'
            })),
            $('<th>').html($('<img>', {
                'src': '/static/img/hadoop.png',
                'class': 'service-image'
            })),
            $('<th>', {
                'html': '&nbsp;'
            })
        ));

        for (var j = 0; j < 10; j++) {
            table.append($('<tr>').append(
                $('<td>').html($('<input>', {
                    'type': 'radio',
                    'id': 'dc' + i + '-node' + j,
                    'name': 'dc' + i + '-node' + j,
                    'value': 'cassandra'
                })),
                $('<td>').html($('<input>', {
                    'type': 'radio',
                    'id': 'dc' + i + '-node' + j,
                    'name': 'dc' + i + '-node' + j,
                    'value': 'spark'
                })),
                $('<td>').html($('<input>', {
                    'type': 'radio',
                    'id': 'dc' + i + '-node' + j,
                    'name': 'dc' + i + '-node' + j,
                    'value': 'search'
                })),
                $('<td>').html($('<input>', {
                    'type': 'radio',
                    'id': 'dc' + i + '-node' + j,
                    'name': 'dc' + i + '-node' + j,
                    'value': 'analytics'
                })),
                $('<td>').html($('<input>', {
                    'type': 'radio',
                    'id': 'dc' + i + '-node' + j,
                    'name': 'dc' + i + '-node' + j,
                    'value': 'null'
                }).prop('checked', true))
            ));
        }
        thisDiv.append(table);
    }
}

$(document).ready(function () {
    $('label').tooltip();
    $('.reveal').click(function (e) {
        var parent = $(this).parent().parent();
        var currentHeight = parent[0].offsetHeight + 'px';
        var minHeight = parent.css('min-height');
        var openHeight = parent[0].scrollHeight + 'px';

        if (minHeight == currentHeight) {
            parent.animate({"height": openHeight}, {duration: "slow"});
        } else {
            parent.animate({"height": minHeight}, {duration: "slow"});
        }
        e.preventDefault();
    });

    $('.advanced-datacenters').hide();
    var createdOnce = false;
    $('.configure-datacenters').click(function (e) {
        if (!createdOnce) {
            create_advanced_datacenter_options();
            createdOnce = true;
        }

        var advancedDatacenters = $('.advanced-datacenters');
        if (advancedDatacenters.is(':visible')) {
            advancedDatacenters.slideUp();
            $('.normal-datacenters').slideDown();
        } else {
            advancedDatacenters.slideDown();
            $('.normal-datacenters').slideUp();
        }
        e.preventDefault();
    });

    $('#submit-button').click(function (e) {
        e.preventDefault();
        $(this).attr('disabled', true);
        $(this).text('ctool calls are being made. Please wait...');
        $('#launch-form').submit();
    });

    $('#ec2-label').tooltip();
    $('.instance-type-help').tooltip();
    $('#gce').click(function (e) {
        $('#instance-type').attr('list', 'instance-type-list-gce').val('n1-standard-2');
    });
    $('#ec2').click(function (e) {
        $('#instance-type').attr('list', 'instance-type-list-ec2').val('m1.large');
    });
});
