'use strict';

odoo.define('pao_fans_automation.cursojavascript', function (require) {
    require('web.dom_ready');
    var ajax = require('web.ajax');

    var button = $('#globalgapbutton');

    var _onButton = function (e) {
        ajax.jsonRpc('/get_globalgap_audit_products', 'call', {}).then(function (data) {
            console.log(data);
            var option = '';
            for (var i = 0; i < data.length; i++) {
                option += '<option value="' + data[i].id + '">' + data[i].name + '</option>';
            }
            $('#items').append(option);
        });
    }
    button.click(_onButton);

});