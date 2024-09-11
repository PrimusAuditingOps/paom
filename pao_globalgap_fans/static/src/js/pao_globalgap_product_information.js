/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";


publicWidget.registry.globalgapproductinformation = publicWidget.Widget.extend({

    selector: '.o_website_product_information_registration',
    events: {
        'click .btn_send_product_information': '_onClickSendProduct',
        'blur .o_website_product_information_registration_form input[name^="name"]': '_onName',
        
    },

    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);
        this.rpc = this.bindService("rpc");    
        this.grid_selector = new gridjs.Grid({
            columns: [
                {
                    id: "product_id",
                    name: "Product ID",
                    hidden: true,
                },
                {
                    id: "product_name",
                    name: "Producto",
                },
                {
                    id: "uncovered_production_area",
                    name: "Área en producción total (ha)",
                },
                {
                    id: "covered_production_area",
                    name: "Producción cubierta (Invernadero, Macrotúnel con cobertura plástica)",
                },
                {
                    id: "applicable_harvest",
                    name: "Cosecha aplicable (Si/No)",
                },
                {
                    id: "harvest_type",
                    name: "Primera Cosecha/Cosecha Posterior",
                },
                {
                    id: "product_handling",
                    name: "Manipulación de Producto",
                },
                {
                    id: "outsourced_activities",
                    name: "Actividades Subcontratadas",
                },
                {
                    id: "ggn_gln_outsourced",
                    name: "Si se subcontrata el empaque, indicar GGN o GLN (Obligatorio si tiene)",
                },
                {
                    id: "product_manipulated_not_certificate",
                    name: "¿El producto a auditar es manipulado con producto no certificado GLOBALG.A.P.?",
                },
                {
                    id: "organization_buys_product",
                    name: "¿La organización compra el mismo producto certificado y/o no certificado?",
                },
                {
                    id: "fsma",
                    name: "FSMA",
                },
                {
                    id: "estimated_yield_in_tons",
                    name: "Rendimiento Estimado en Tons (voluntario)",
                },
                {
                    id: "start_date_harvest_estimated",
                    name: "Fecha inicio de cosecha estimada (Obligatorio)",
                },
                    {
                    id: "end_date_harvest_estimated",
                    name: "Fecha fin de cosecha estimada (Obligatorio)",
                },
                {
                    id: "countries_of_products",
                    name: "Países de Destino",
                },
            ],
            data: [],
            width: 1200,
            style: {
                table: {
                    border: '3px solid #ccc',
                    'table-layout': 'auto',
                },
                th: {
                    'background-color': 'rgba(0, 0, 0, 0.1)',
                    'color': '#000',
                    'border-bottom': '3px solid #ccc',
                    'text-align': 'center',
                    'height': '50px',
                },
                td: {
                'text-align': 'center'
                }
            }
        }).render(document.getElementById("gridProductInformation"));    
    },
    /**
     * @override
     * @param {Object} parent
     */
    
    start: async function (parent) {
        
        var d = [];
        var x = this.grid_selector;
        await this.rpc('/pao/fan/product_information',
        {
            'fan_id': $("#fr_id").val().trim(), 
            'fan_token': $("#fr_token").val().trim(), 
        }).then(function (data) {
            data.data.forEach(function(objdata) {
                 
                console.log(data.fsma);
                console.log(objdata.fsma);
                var applicable_harvest = `<select optional="false" name="applicable_harvest" id="applicable_harvest`+objdata.product_id+`">`;
                for (let i = 0; i < data.applicable_harvest.length; i++) {
                    if (data.applicable_harvest[i][0] == objdata.applicable_harvest[i]){
                        applicable_harvest += `<option selected value="`+data.applicable_harvest[i][0]+`">`+data.applicable_harvest[i][1]+`</option>`;
                    }
                    else{
                        applicable_harvest += `<option value="`+data.applicable_harvest[i][0]+`">`+data.applicable_harvest[i][1]+`</option>`;
                    }                        
                }
                applicable_harvest += `</select>`;
                var fsma = "";
                if (data.show_fsma == true)
                {
                    fsma = `<select optional="false" name="fma" id="fsma`+objdata.product_id+`">`;
                    for (let i = 0; i < data.fsma.length; i++) {
                        if (data.fsma[i][0] == objdata.fsma){
                            fsma += `<option selected value="`+data.fsma[i][0]+`">`+data.fsma[i][1]+`</option>`;
                        }
                        else{
                            fsma += `<option value="`+data.fsma[i][0]+`">`+data.fsma[i][1]+`</option>`;
                        }                        
                    }
                    fsma += `</select>`;
                }
                

                var harvest_type = `<select optional="false" name="harvest_type" id="harvest_type`+objdata.product_id+`">`;
                for (let i = 0; i < data.harvest_type.length; i++) {
                    if (data.harvest_type[i][0] == objdata.harvest_type[i]){
                        harvest_type += `<option selected value="`+data.harvest_type[i][0]+`">`+data.harvest_type[i][1]+`</option>`;
                    }
                    else{
                        harvest_type += `<option value="`+data.harvest_type[i][0]+`">`+data.harvest_type[i][1]+`</option>`;
                    }                        
                }
                harvest_type += `</select>`;

                var product_handling = `<select optional="false" name="product_handling" id="product_handling`+objdata.product_id+`">`;
                for (let i = 0; i < data.product_handling.length; i++) {
                    if (data.product_handling[i][0] == objdata.product_handling[i]){
                        product_handling += `<option selected value="`+data.product_handling[i][0]+`">`+data.product_handling[i][1]+`</option>`;
                    }
                    else{
                        product_handling += `<option value="`+data.product_handling[i][0]+`">`+data.product_handling[i][1]+`</option>`;
                    }                        
                }
                product_handling += `</select>`;

                var organization_buys_product = `<select optional="false" name="organization_buys_product" id="organization_buys_product`+objdata.product_id+`">`;
                for (let i = 0; i < data.organization_buys_product.length; i++) {
                    if (data.organization_buys_product[i][0] == objdata.organization_buys_product[i]){
                        organization_buys_product += `<option selected value="`+data.organization_buys_product[i][0]+`">`+data.organization_buys_product[i][1]+`</option>`;
                    }
                    else{
                        organization_buys_product += `<option value="`+data.organization_buys_product[i][0]+`">`+data.organization_buys_product[i][1]+`</option>`;
                    }                        
                }
                organization_buys_product += `</select>`;

                var product_manipulated_not_certificate = `<select optional="false" name="product_manipulated_not_certificate" id="product_manipulated_not_certificate`+objdata.product_id+`">`;
                for (let i = 0; i < data.product_manipulated_not_certificate.length; i++) {
                    if (data.product_manipulated_not_certificate[i][0] == objdata.product_manipulated_not_certificate[i]){
                        product_manipulated_not_certificate += `<option selected value="`+data.product_manipulated_not_certificate[i][0]+`">`+data.product_manipulated_not_certificate[i][1]+`</option>`;
                    }
                    else{
                        product_manipulated_not_certificate += `<option value="`+data.product_manipulated_not_certificate[i][0]+`">`+data.product_manipulated_not_certificate[i][1]+`</option>`;
                    }                        
                }
                product_manipulated_not_certificate += `</select>`;

                var countries_of_products = `<select class="countries_of_products-select" multiple="true" name="countries_of_products" id="countries_of_products`+objdata.product_id+`">`;
                for (let i = 0; i < data.countries.length; i++) {
                    if (objdata.countries_of_products.includes(data.countries[i].id)){
                        console.log(data.countries[i].id);
                        console.log(objdata.countries_of_products);
                        countries_of_products += `<option selected value="`+data.countries[i].id+`">`+data.countries[i].name+`</option>`;
                    }
                    else{
                            countries_of_products += `<option value="`+data.countries[i].id+`">`+data.countries[i].name+`</option>`;
                    } 
                    
                    
                                            
                }
                countries_of_products += `</select>`;


                var obj = {
                    "product_id": objdata.product_id,
                    "product_name": objdata.product_name,
                    "uncovered_production_area": gridjs.html(`<input type="text"  class="onlyNumber" maxlength="20" id="uncovered_production_area`+objdata.product_id+`" value="`+objdata.uncovered_production_area+`"/>`),
                    "covered_production_area": gridjs.html(`<input type="text" class="onlyNumber" maxlength="20" id="covered_production_area`+objdata.product_id+`" value="`+objdata.covered_production_area+`"/>`),
                    "applicable_harvest": gridjs.html(applicable_harvest),
                    "harvest_type": gridjs.html(harvest_type),
                    "product_handling": gridjs.html(product_handling),
                    "outsourced_activities": gridjs.html(`<input type="text" maxlength="200" id="outsourced_activities`+objdata.product_id+`" value="`+objdata.outsourced_activities+`"/>`),
                    "ggn_gln_outsourced": gridjs.html(`<input type="text" maxlength="20" id="ggn_gln_outsourced`+objdata.product_id+`" value="`+objdata.ggn_gln_outsourced+`"/>`),
                    "product_manipulated_not_certificate": gridjs.html(product_manipulated_not_certificate),
                    "organization_buys_product": gridjs.html(organization_buys_product),
                    "fsma": gridjs.html(fsma),
                    "estimated_yield_in_tons": gridjs.html(`<input type="text" class="onlyNumber" maxlength="20" id="estimated_yield_in_tons`+objdata.product_id+`" value="`+objdata.estimated_yield_in_tons+`"/>`),
                    "start_date_harvest_estimated": gridjs.html(`<input type="date" id="harvest_estimated_start_date`+objdata.product_id+`" value="`+objdata.harvest_estimated_start_date+`"/>`),
                    "end_date_harvest_estimated": gridjs.html(`<input type="date" id="harvest_estimated_end_date`+objdata.product_id+`" value="`+objdata.harvest_estimated_end_date+`"/>`),
                    //"dates_harvest_estimated": gridjs.html(`<input type="text" id="dates_harvest_estimated`+objdata.product_id+`" value="`+objdata.ggn_gln_outsourced+`"/>`),
                    "countries_of_products":  gridjs.html(countries_of_products)
                    };
                    d.push(obj);

            });
            x.updateConfig({
                data: d
            }).forceRender();
                 
            
            

        });
        
        
        
        
        $("#name").focus();
    },
    _onName: function(ev){
        $('.onlyNumber').each(function(){
                $(this).on( "keypress", function (e){
                    var key = e.charCode;
                    if (key <45 || key > 57){
                        e.preventDefault();
                    }
                });
            });
        $(".countries_of_products-select").chosen();
        var product_list = JSON.parse($("#product_ids").val());
        /*for (let i = 0; i < product_list.length; i++) {
            $("#harvest_estimated_start_date"+product_list[i])
                .datepicker({
                defaultDate: "+1w",
                changeMonth: true,
                changeYear: true,
                dateFormat: "yy-mm-dd",
                numberOfMonths: 1,
                })
            .on( "change", function() {
                if ($("#harvest_estimated_start_date"+product_list[i]).val()){
                    $( "#harvest_estimated_end_date"+product_list[i] ).datepicker( "option", "minDate", $("#harvest_estimated_start_date"+product_list[i]).val());
                }
            });
            $( "#harvest_estimated_end_date"+product_list[i] ).datepicker({
                defaultDate: "+1w",
                changeMonth: true,
                changeYear: true,
                dateFormat: "yy-mm-dd",
                numberOfMonths: 1,
            })
            .on( "change", function() {
                if ($("#harvest_estimated_end_date"+product_list[i]).val()){
                    $( "#harvest_estimated_start_date"+product_list[i] ).datepicker( "option", "maxDate", $("#harvest_estimated_end_date"+product_list[i]).val());
                }
                //$("#harvest_estimated_start_date"+product_list[i]).datepicker( "option", "maxDate", $.datepicker.parseDate( "yy/mm/dd", $( "#harvest_estimated_end_date"+product_list[i] ).value ) );
            });

                $("#harvest_estimated_start_date"+product_list[i]).datepicker( "option", "dateFormat", "yy-mm-dd" );
                $("#harvest_estimated_end_date"+product_list[i]).datepicker( "option", "dateFormat", "yy-mm-dd" );


        }*/
    },
    _getDate: function(element) {
        var date;
        try {
            date = $.datepicker.parseDate( "yy/mm/dd", element.value );
        } catch( error ) {
            date = null;
        }
    
        return date;
    },
    _onClickSendProduct: async function (ev) {
        var product_list = JSON.parse($("#product_ids").val());
        var products = []
        for (let i = 0; i < product_list.length; i++) {
            
            if ($("#uncovered_production_area"+product_list[i]).val() == ""){

                alert("Favor de capturar un Área en producción total (ha).");
                $("#uncovered_production_area"+product_list[i]).focus()
                products = [];
                break;
            }
            else if ($("#covered_production_area"+product_list[i]).val() == ""){
                alert("Favor de capturar la Producción cubierta (Invernadero, Macrotúnel con cobertura plástica).");
                $("#covered_production_area"+product_list[i]).focus()
                products = [];
                break;
            }
            else if($("#estimated_yield_in_tons"+product_list[i]).val() == ""){
                alert("Favor de capturar un Rendimiento Estimado en Tons.");
                $("#estimated_yield_in_tons"+product_list[i]).focus()
                products = [];
                break;
            }
            else if($("#harvest_estimated_start_date"+product_list[i] ).val() == ""){
                alert("Favor de seleccionar una Fecha inicio de cosecha estimada.");
                $("#harvest_estimated_start_date"+product_list[i]).focus()
                products = [];
                break;
            }
            else if($("#harvest_estimated_end_date"+product_list[i] ).val() == ""){
                alert("Favor de seleccionar una Fecha fin de cosecha estimada.");
                $("#harvest_estimated_end_date"+product_list[i]).focus()
                products = [];
                break;
            }
            else if($("#countries_of_products"+product_list[i] ).val().length <= 0){
                alert("Favor de seleccionar los Países de Destino.");
                $("#countries_of_products"+product_list[i]).focus()
                products = [];
                break;
            }
            else{
                var obj = {
                    "product_id": product_list[i],
                    "uncovered_production_area": $("#uncovered_production_area"+product_list[i]).val(),
                    "covered_production_area": $("#covered_production_area"+product_list[i]).val(),
                    "applicable_harvest": $('select[id="applicable_harvest'+product_list[i]+'"] option:selected').val(),
                    "harvest_type": $('select[id="harvest_type'+product_list[i]+'"] option:selected').val(),
                    "product_handling": $('select[id="product_handling'+product_list[i]+'"] option:selected').val(),
                    "outsourced_activities": $("#outsourced_activities"+product_list[i]).val(),
                    "ggn_gln_outsourced": $("#ggn_gln_outsourced"+product_list[i]).val(),
                    "product_manipulated_not_certificate": $('select[id="product_manipulated_not_certificate'+product_list[i]+'"] option:selected').val(),
                    "organization_buys_product": $('select[id="organization_buys_product'+product_list[i]+'"] option:selected').val(),
                    "estimated_yield_in_tons": $("#estimated_yield_in_tons"+product_list[i]).val(),
                    "dates_harvest_estimated": "",
                    "harvest_estimated_end_date": $("#harvest_estimated_end_date"+product_list[i] ).val(),
                    "harvest_estimated_start_date": $("#harvest_estimated_start_date"+product_list[i] ).val(),
                    "countries_of_products": $("#countries_of_products"+product_list[i]).val(),
                    };
                products.push(obj);
            }
            
        }
        if (products.length>0){
            await this.rpc('/pao/fan/register/product_information',
            {
                'fan_id': $("#fr_id").val().trim(), 
                'fan_token': $("#fr_token").val().trim(), 
                'products': products, 
            }).then(function (data) {
                window.location = data.redirect_url;           

            });
        }
        

    },

        
});
export default publicWidget.registry.globalgapproductinformation;