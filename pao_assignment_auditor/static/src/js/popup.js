odoo.define('pao_assignment_auditor.popup_assignment_auditor', function (require) {
    'use strict';
    
    const widgetRegistry = require('web.widget_registry');
    const Widget = require('web.Widget');
    var core = require('web.core');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var Dialog = require('web.Dialog');
    var FieldManagerMixin = require('web.FieldManagerMixin');
    var session = require('web.session');
    var _t = core._t;

    const ToasterButton = Widget.extend({FieldManagerMixin,
        template: 'pao_assignment_auditor.popup_assignment_auditor',
        xmlDependencies: ['/pao_assignment_auditor/static/src/xml/popup_assignment_auditor.xml'],
        events: Object.assign({}, Widget.prototype.events, {
            'click .fa-search': '_onClickButton',
        }),

        init: function (parent, data, node) {
            this._super(...arguments);
            FieldManagerMixin.init.call(this);
            this.button_name = node.attrs.button_name;
            this.title = node.attrs.title;
            this.id = data.res_id;
            this.model = data.model;
            this.virtual = data.ref;
            
            
        },
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
        _onClickButton: function (ev) {
            self = this;
            ev.preventDefault();
            ev.stopPropagation();
            
            var startdatesArray = [];
            var datesArray = [];
            var productArray = [];
            var organizationArray = [];
            var saleorderid = null;
            var orderid = this.res_id ? this.res_id : -1;
            var cityid = this.getParent().state.data.audit_city_id.res_id;

            var order_line = this.getParent().state.data.order_line.data;
            if (this.getParent().state.data.sale_order_id){
                saleorderid = this.getParent().state.data.sale_order_id.res_id;
            }
            for (let id in order_line){
                var start_date = order_line[id].data.service_start_date._i;
                var formatstartdate = order_line[id].data.service_start_date._f;
                var end_date = order_line[id].data.service_end_date._i;
                var formatenddate = order_line[id].data.service_end_date._f;
                var product_id = order_line[id].data.product_id.res_id;
                var organization_id = order_line[id].data.organization_id.res_id;

                if (typeof product_id !== 'undefined') {
                    
                    if (!productArray.includes(product_id)){
                        productArray.push(product_id);
                    }
                }

                if (typeof start_date !== 'undefined') {
                    var fsd = this._formatDate(start_date, formatstartdate);
                    var fed = this._formatDate(end_date, formatenddate);

                    var objDates = new Object();
                    objDates.start_date = fsd;
                    objDates.end_date = fed;
                    var existsDates = false;

                    if (datesArray.some(e => e.start_date === objDates.start_date && e.end_date === objDates.end_date)) {
                        existsDates = true;
                    }
                    if (!existsDates){
                        datesArray.push(objDates);
                    }

                    if (!startdatesArray.includes(fsd)){
                        startdatesArray.push(fsd);
                    }
                }
                if (typeof product_id !== 'undefined') {

                    if (!productArray.includes(product_id)){
                        productArray.push(product_id);
                    }
                }
                if (typeof organization_id !== 'undefined') {
                    
                    if (!organizationArray.includes(organization_id)){
                        organizationArray.push(organization_id);
                    }
                }
                
            }
            if (datesArray.length > 0 && productArray.length > 0){
                ajax.jsonRpc('/auditor_assignment', 'call', 
                {
                'dates' : datesArray,
                'startdates' : startdatesArray, 
                'products' : productArray,
                'organizations': organizationArray,
                'saleorderid' : saleorderid,
                'orderid' : orderid,
                'cityid' : cityid,
                }).then(function (data) {
                    if ( data.auditors.length > 0 ){
                        self.do_action({
                            name: 'Assignment Auditor Qualification',
                            views: [[false, 'list']],
                            view_type: 'form',
                            view_mode: 'tree,form',
                            res_model: 'paoassignmentauditor.auditor.qualification',
                            type: 'ir.actions.act_window',
                            target: 'new',
                            domain: [['ref_user_id', '=', data.user_id]],
                        },
                        {
                            on_close: function(result)
                            {   
                                var context = session.user_context;
                                var model = 'paoassignmentauditor.auditor.qualification';
                                // Use an empty array to search for all the records
                                var domain = [["ref_user_id","=",context.uid],["assigned_auditor_id","<>",0]];
                                // Use an empty array to read all the fields of the records
                                var fields = ["assigned_auditor_id","assigned_auditor_position","assigned_auditor_qualification"];
                                rpc.query({
                                    model: model,
                                    method: 'search_read',
                                    args: [domain, fields],
                                }).then(function (data) {
                                    for (var i=0; i < data.length; i++) {
                                        if (data[i].assigned_auditor_id > 0){
                                            $('[name="assigned_auditor_id"]').val(data[i].assigned_auditor_id).change();
                                            $('[name="assigned_auditor_position"]').val(data[i].assigned_auditor_position).change();
                                            $('[name="assigned_auditor_qualification"]').val(data[i].assigned_auditor_qualification).change();
                                        }
                                        break;
                                    }
                                });
                            }
                        });
                    }
                    else{
                        Dialog.alert(self, _t('No available auditors found.'));
                    }
                    
                });
            }
            else{
                Dialog.alert(this, _t('Capture audit services or assign a date to services.'));
            }
        },
        _formatDate: function(date,format) {
            
            if (format == "MM/DD/YYYY"){
                var d = new Date(date);
                var month = '' + (d.getMonth() + 1),
                    day = '' + d.getDate(),
                    year = d.getFullYear();
            
                if (month.length < 2) 
                    month = '0' + month;
                if (day.length < 2) 
                    day = '0' + day;
            
                return [year, month, day].join('-');

            }
            else if (format == "DD/MM/YYYY"){
                var newdate = date.split("/").reverse().join("-");
                return newdate;
            }
            else{
                return date;
                
            }
            
        }
    });

    widgetRegistry.add('popup_assignment_auditor', ToasterButton);



});


