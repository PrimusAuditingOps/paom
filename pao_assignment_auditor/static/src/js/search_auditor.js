/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { useBus } from "@web/core/utils/hooks";
import { parseDate, formatDate } from "@web/core/l10n/dates";

import { onWillStart, Component } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";


class SearchAuditors extends Component {
    static template = "pao_assignment_auditor.popup_assignment_auditor";
    static props = {
        ...standardWidgetProps,
    };

    setup() {
        super.setup(...arguments);

        this.rpc = useService("rpc");
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");

        onWillStart(async () => {
        	await this._GetLangDateFormat();
        });
    }

    async _GetLangDateFormat() {
        this.dateFormat = await this.orm.searchRead(
            "res.lang",
            [
            	["code","=",this.env.model.config.context.lang]
            ],
            ["date_format"]
        );
    }

	_formatDate(date) {
	    if (this.format == "%m/%d/%Y"){
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
	    else if (this.format == "%d/%m/%Y"){
	        return date.split("/").reverse().join("-");
	    }
	    else{
	        return date;
	    }
	}

	async onClickSearchAuditors(event) {
        event.preventDefault();
        event.stopPropagation();

		var warningAccoured = false;
        var startdatesArray = [];
        var datesArray = [];
		var languages = [];
        var productArray = [];
        var organizationArray = [];
        var saleorderid = null;
		
        var recordData = this.props.record.data
        var orderid = recordData.id;
        var cityid = recordData.audit_city_id[0];
		var stateid = recordData.audit_state_id[0];
		var orderCountry = recordData.country_code;
        var auditquantity = 0;
        var order_line = this.props.record.data.order_line;
		var d = this.props.record.data.language_ids;
		$(d._currentIds).toArray().forEach((l) => {
			languages.push(l);
		});


		//if (orderid){
	        if (recordData.sale_order_id){
	            saleorderid = recordData.sale_order_id[0];
	        }
	        if ($(order_line).toArray()[0].count > 0) {
		        $(order_line).toArray().forEach((line) => {
		        	var lineData = line.records[0].data;
		            var start_date = lineData.service_start_date;
		            var end_date = lineData.service_end_date;
		            var product_id = lineData.product_id[0];
		            var organization_id = lineData.organization_id;
					auditquantity += lineData.product_qty;
		            if (typeof start_date !== 'undefined' && start_date != false) {
		                var fsd = this._formatDate(start_date);
		                var fed = this._formatDate(end_date);
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
		            if (typeof product_id !== 'undefined' && product_id != false) {
		                if (!productArray.includes(product_id)){
		                    productArray.push(product_id);
		                }
		            }
		            if (typeof organization_id !== 'undefined' && organization_id != false) {
		                organization_id = organization_id[0];
		                if (!organizationArray.includes(organization_id)){
		                    organizationArray.push(organization_id);
		                }
		            }
		            
		        });
	        } else {
	        	warningAccoured = true;
	            this.dialog.add(WarningDialog, {
	                title: _t('Warning'),
	                message: _t('Please add some products to the order line.'),
	            });
	        }
	        if (datesArray.length > 0 && productArray.length > 0){
	        	let datas = await this.rpc('/auditor_assignment', {
		            'dates' : datesArray,
		            'startdates' : startdatesArray, 
		            'products' : productArray,
		            'organizations': organizationArray,
		            'saleorderid' : saleorderid,
		            'orderid' : orderid,
		            'cityid' : cityid,
					'stateid': stateid,
					'auditquantity': auditquantity,
					'languages':languages,
					'orderCountry': orderCountry,
	        	});
	            if ( datas.auditors.length > 0 ){
			        this.action.doAction({
	                    name: 'Assignment Auditor Qualification',
	                    views: [[false, 'list']],
	                    view_type: 'form',
	                    view_mode: 'tree,form',
	                    res_model: 'paoassignmentauditor.auditor.qualification',
	                    type: 'ir.actions.act_window',
	                    target: 'new',
	                    domain: [['ref_user_id', '=', datas.user_id]],
	                },
	                {


						onClose: async () => {
	                        const data = await this.orm.searchRead(
					            'paoassignmentauditor.auditor.qualification',
					            [
					            	["ref_user_id","=", datas.user_id],
					            	["assigned_auditor_id","<>",0]
					            ],
					            ["assigned_auditor_id","assigned_auditor_position","assigned_auditor_qualification"]    
	                        );
	                        for (var i=0; i < data.length; i++) {
	                            if (data[i].assigned_auditor_id > 0){
									this.props.record.update(
										{ 
											assigned_auditor_id: data[i].assigned_auditor_id,  
											assigned_auditor_position: data[i].assigned_auditor_position,
											assigned_auditor_qualification: data[i].assigned_auditor_qualification
										}
									);
								}
	                            break;
	                        }
						},
	                });
	            }
	            else{
	            	if (!warningAccoured) {
	            		warningAccoured = true;
		                this.dialog.add(WarningDialog, {
		                    title: _t('Warning'),
		                    message: _t('No available auditors found.'),
		                });
		            }
	            }
	
	        }
	        else{
	        	if (!warningAccoured) {
		            this.dialog.add(WarningDialog, {
		                title: _t('Warning'),
		                message: _t('Capture audit services or assign a date to services.'),
		            });
		        }
	        }
		//}
		//else {
        //    this.dialog.add(WarningDialog, {
        //        title: _t('Warning'),
        //        message: _t('You can not use this feature when creating the data, save it first.'),
        //    });
		//}
    }

}

export const resSearchAuditors = {
    component: SearchAuditors,
};

registry.category("view_widgets").add("popup_assignment_auditor", resSearchAuditors);
