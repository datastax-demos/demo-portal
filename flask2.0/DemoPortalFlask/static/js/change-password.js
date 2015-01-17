$(document).ready(function () {
    options = {
        common: {
            minChar: 6,
            onKeyUp: function (evt, data) {
                if (data.score > 0) {
                    $('#submit-button').prop('disabled', false);
                } else {
                    $('#submit-button').prop('disabled', true);
                }
            }
        },
        rules: {
            activated: {
                wordTwoCharacterClasses: true,
                wordRepetitions: true
            }
        },
        ui: {
            showVerdictsInsideProgressBar: true
        }
    };
    $('#new-password').pwstrength(options);
    $('#confirm-password').pwstrength(options);
});
