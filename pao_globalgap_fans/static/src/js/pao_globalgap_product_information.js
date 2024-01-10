odoo.define('pao_globalgap_fans.globalgapproductinformation', function (require) {

    'use strict';

    var publicWidget = require('web.public.widget');
    

    publicWidget.registry.globalgapproductinformation = publicWidget.Widget.extend({

        selector: '.o_website_product_information_registration',
        events: {
            /*'change .o_website_product_information_registration_form select[id="sitecountry"]': '_onCountryChange',
            'change .o_website_product_information_registration_form select[id="sitestate"]': '_onStateChange',
            'change .o_website_product_information_registration_form select[id="contaccountry"]': '_onContactCountryChange',
            'change .o_website_product_information_registration_form select[id="contactstate"]': '_onContactStateChange',
            'click .o_website_product_information_registration_form input[name^="addonsgg"]': '_onAddonsChange',
            'click .btn_add_production_site': '_onClickProductionSite',
            'click .btn_add_products': '_onClickProduct'*/
            
        },
        /**
         * @constructor
         */
        init: function () {
            this._super.apply(this, arguments);
            this.datas = []
            this.products = []
            this.grid_selector = new gridjs.Grid({
                columns: [
                    {
                        id: "id",
                        name: "ID",
                        hidden: true,
                    },
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
                        name: "Area en producción (ha)",
                    },
                    {
                        id: "covered_production_area",
                        name: "Producción cubierta (Invernadero, Macrotúnel con cobertura plástica) (Si/No)",
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
                        name: "Manipulación de Producto (No/Sí en campo/Sí en PHU)**",
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
                        name: "¿El producto a auditar es manipulado con producto no certificado GLOBALG.A.P.? (Sí/No/NA)",
                    },
                    {
                        id: "organization_buys_product",
                        name: "¿La organización compra el mismo producto certificado y/o no certificado?",
                    },
                    {
                        id: "estimated_yield_in_tons",
                        name: "Rendimiento Estimado en Tons (voluntario)",
                    },
                    {
                        id: "dates_harvest_estimated",
                        name: "Fechas de cosecha estimadas (Obligatorio)",
                    },
                    {
                        id: "countries_of_products",
                        name: "Países de Destino",
                    },
                ],
                data: [
                    {
                       "id": 123,
                       "product_id": 13,
                       "product_name": "Pomelos",
                       "uncovered_production_area": gridjs.html(`<input type="text" id="samuel21"/>`),
                       "covered_production_area": gridjs.html(`<input type="text" id="samuel21"/>`),
                       "applicable_harvest": gridjs.html(`<select optional="false" id="1" name="organization_buys_product">
                       </select>`),
                       "harvest_type": gridjs.html(`<select optional="false" id="1" name="organization_buys_product">
                       </select>`),
                       "product_handling": gridjs.html(`<select optional="false" id="1" name="organization_buys_product">
                       </select>`),
                       "outsourced_activities": gridjs.html(`<input type="text" id="samuel21"/>`),
                       "ggn_gln_outsourced": gridjs.html(`<input type="text" id="samuel21"/>`),
                       "product_manipulated_not_certificate": gridjs.html(`<select optional="false" id="1" name="organization_buys_product">
                       </select>`),
                       "organization_buys_product": gridjs.html(`<select optional="false" id="1" name="organization_buys_product">
                       </select>`),
                       "estimated_yield_in_tons": gridjs.html(`<input type="text" id="samuel21"/>`),
                       "dates_harvest_estimated": gridjs.html(`<input type="text" id="samuel21"/>`),
                       "countries_of_products":  gridjs.html(`<select id="sasa" class="chzn-select" multiple="true" name="faculty" style="width:200px;">
                                                                    <option value="AC">A</option>
                                                                    <option value="AD">B</option>
                                                                    <option value="AM">C</option>
                                                                    <option value="AP">D</option>
                                                                </select>`)
                    }
                ],
            }).render(document.getElementById("gridProductInformation"));
            console.log("creo");

            
            
        },
        /**
         * @override
         * @param {Object} parent
         */
        start: function (parent) {

        

            this.datas = []
            this.products = []
           
            console.log("entro2");
            $("#sasa").chosen();

        
           /*
            if (d.length > 0){
                this.datas = d;
                this.grid_selector.updateConfig({
                    data: d
                }).forceRender();
                $("#sites").val(JSON.stringify(d));
                $("#btn_send_sites").prop('disabled', false);
            }*/
            

            return this._super.apply(this, arguments);
        },

        
        
    });
});