/* Created by jankoatwarpspeed.com */
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

$(document).ready(function(){
    $("#SignupForm").formToWizard({ submitButton: 'SaveAccount' })
});


(function($) {
$.fn.formToWizard = function(options) {
options = $.extend({  
    submitButton: "" 
}, options); 

var element = this;

var steps = $(element).find("fieldset");
var count = steps.size();
var submmitButtonName = "#" + options.submitButton;
$(submmitButtonName).hide();

// 2
$(element).before("<ul id='steps'></ul>");

steps.each(function(i) {
    $(this).wrap("<div id='step" + i + "'></div>");
    $(this).append("<p id='step" + i + "commands'></p>");

    // 2
    var name = $(this).find("legend").html();
    $("#steps").append("<li id='stepDesc" + i + "'>Step " + (i + 1) + "<span>" + name + "</span></li>");

    if (i == 0) {
        createNextButton(i);
        selectStep(i);
    }
    else if (i == count - 1) {
        $("#step" + i).hide();
        createPrevButton(i);
    }
    else {
        $("#step" + i).hide();
        createPrevButton(i);
        createNextButton(i);
    }
});

function createPrevButton(i) {
    var stepName = "step" + i;
    $("#" + stepName + "commands").append("<a href='#' id='" + stepName + "Prev' class='prev'>< Back</a>");

    $("#" + stepName + "Prev").bind("click", function(e) {
        $("#" + stepName).hide();
        $("#step" + (i - 1)).show();
        $(submmitButtonName).hide();
        selectStep(i - 1);
    });
}

function createNextButton(i) {
    var stepName = "step" + i;
    $("#" + stepName + "commands").append("<a href='#' id='" + stepName + "Next' class='next'>Next ></a>");

    $("#" + stepName + "Next").bind("click", function(e) {
        $("#" + stepName).hide();
        $("#step" + (i + 1)).show();
        if (i + 2 == count)
            $(submmitButtonName).show();
        selectStep(i + 1);
    });
}

function selectStep(i) {
    $("#steps li").removeClass("current");
    $("#stepDesc" + i).addClass("current");
}

}
})(jQuery); 