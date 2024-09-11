/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.globalgapproductionsite = publicWidget.Widget.extend({

    selector: '.o_website_production_site_registration',
        events: {
            'change .o_website_production_site_registration_form select[id="sitecountry"]': '_onCountryChange',
            'change .o_website_production_site_registration_form select[id="sitestate"]': '_onStateChange',
            'change .o_website_production_site_registration_form select[id="contaccountry"]': '_onContactCountryChange',
            'change .o_website_production_site_registration_form select[id="contactstate"]': '_onContactStateChange',
            'click .btn_add_production_site': '_onClickProductionSite',
            'click .btn_add_products': '_onClickProduct',
            'click .btn_add_search_site_address': '_searchAddress',
            'blur .o_website_production_site_registration_form input[name^="longitude"]': '_onLngLatSiteBlur',
            'blur .o_website_production_site_registration_form input[name^="latitude"]': '_onLngLatSiteBlur',
            'keypress .o_website_production_site_registration_form input[name^="contacttelephone"]': '_onOnlyNumbers',
            'keypress .o_website_production_site_registration_form input[name^="hect"]': '_onOnlyNumbersAndSpecialCharacter',
            'keypress .o_website_production_site_registration_form input[name^="contactzip"]': '_onOnlyNumbers',
            'keypress .o_website_production_site_registration_form input[name^="telephone"]': '_onOnlyNumbers',
            'keypress .o_website_production_site_registration_form input[name^="zip"]': '_onOnlyNumbers',
            'keypress .o_website_production_site_registration_form input[name^="latitude"]': '_onOnlyNumbersAndSpecialCharacter',
            'keypress .o_website_production_site_registration_form input[name^="longitude"]': '_onOnlyNumbersAndSpecialCharacter',
            'click .o_website_production_site_registration_form button[id="btn_send_sites"]': '_onClickSaveProductionSite',
            
        },
        /**
         * @constructor
         */
        init: function () {
            this._super.apply(this, arguments);
            this.datas = []
            this.products = []
            this.rpc = this.bindService("rpc");

        },
        /**
         * @override
         * @param {Object} parent
         */
        start: function (parent) {

            

            $("#btn_send_sites").prop('disabled', true);

            this.countries = document.querySelector('#sitecountry');
            this.states = document.querySelector('#sitestate');
            this.optionStates = this.states.querySelectorAll('option');
            this.cities = document.querySelector('#sitecity');
            this.optionCities = this.cities.querySelectorAll('option');

            var countryInit = $("#sitecountry").val();
            var stateInit = $("#sitestate").val();
            var cityInit = $("#sitecity").val();
            $("#sitecountry").val(countryInit).change();
            $("#sitestate").val(stateInit).change();
            $("#sitecity").val(cityInit).change();


            this.contactCountries = document.querySelector('#contaccountry');
            this.contactStates = document.querySelector('#contactstate');
            this.optionContactStates = this.contactStates.querySelectorAll('option');
            this.contactCities = document.querySelector('#contaccity');
            this.optionContactCities = this.contactCities.querySelectorAll('option');

            var contactCountryInit = $("#contaccountry").val();
            var contactStateInit = $("#contactstate").val();
            var contactCityInit = $("#contaccity").val();
            $("#contaccountry").val(contactCountryInit).change();
            $("#contactstate").val(contactStateInit).change();
            $("#contaccity").val(contactCityInit).change();





            $("#productionsite").val("");
            $("#address").val("");
            $("#postal_address").val("");
            $("#zip").val("");
            $("#telephone").val("");
            $("#email").val("");
            $("#latitude").val("");
            $("#longitude").val("");
            $("#contactname").val("");
            $("#contactaddress").val("");
            $("#contactpostaladdress").val("");
            $("#contactzip").val("");
            $("#contacttelephone").val("");
            $("#contactemail").val("");

            this.datas = []
            this.products = []
            this.grid_selector = new gridjs.Grid({
                columns: [
                    {
                        id: "name",
                        name: "Sitio de producción",
                    },
                    {
                        id: "type_name",
                        name: "Tipo",
                    },
                    {
                        id: "type",
                        name: "Tipo",
                        hidden: true,
                    },
                    {
                        id: "address",
                        name: "Dirección",
                        hidden: true,
                    },
                    {
                        id: "postal_address",
                        name: "Dirección postal",
                        hidden: true,
                    },
                    
                    {
                        id: "country",
                        name: "País",
                        hidden: true,
                    },
                    {
                        id: "state",
                        name: "Estado",
                        hidden: true,
                    },
                    {
                        id: "city",
                        name: "Ciudad",
                        hidden: true,
                    },
                    {
                        id: "zip",
                        name: "Código postal",
                        hidden: true,
                    },
                    {
                        id: "telephone",
                        name: "Telefono",
                        hidden: true,
                    },
                    {
                        id: "email",
                        name: "Correo electrónico",
                        hidden: true,
                    },
                    {
                        id: "latitude",
                        name: "latitud",
                        hidden: true,
                    },
                    {
                        id: "longitude",
                        name: "longitud",
                        hidden: true,
                    },
                    {
                        id: "contactname",
                        name: "Contacto",
                        hidden: true,
                    },
                    {
                        id: "contactaddress",
                        name: "Dirección del contacto",
                        hidden: true,
                    },
                    {
                        id: "contactpostaladdress",
                        name: "Dirección postal del contacto",
                        hidden: true,
                    },
                    {
                        id: "contactcountry",
                        name: "País del contacto",
                        hidden: true,
                    },
                    {
                        id: "contactstate",
                        name: "Estado del contacto",
                        hidden: true,
                    },
                    {
                        id: "contactcity",
                        name: "Ciudad del contacto",
                        hidden: true,
                    },
                    {
                        id: "contactzip",
                        name: "Código postal del contacto",
                        hidden: true,
                    },
                    {
                        id: "contacttelephone",
                        name: "Telefono del contacto",
                        hidden: true,
                    },
                    {
                        id: "contactemail",
                        name: "Correo electrónico del contacto",
                        hidden: true,
                    },
                    {
                        id: "index",
                        name: "index",
                        hidden: true,
                    }, 
                    { 
                        id:"deleteaction",
                        name: '',
                        formatter: (cell, row) => {
                          return gridjs.h('icon', {
                            style:'padding: 10px 20px;background-color: red;color: white;border: none; border-radius: 5px;cursor: pointer;',
                            onClick: () => {
                                const list = this.datas.filter(d => d.index != row.cells[22].data);
                                this.datas = list;
                                this.grid_selector.updateConfig({
                                    data: list
                                }).forceRender();
                                $("#sites").val(JSON.stringify(list));  
                            }
                          }, 'Eliminar');
                        }
                    },
                    { 
                        id:"updateaction",
                        name: '',
                        formatter: (cell, row) => {
                          return gridjs.h('icon', {
                            style:'padding: 10px 20px;background-color: #17a2b8; color: white;border: none; border-radius: 5px;cursor: pointer;',
                            onClick: () => {
                                const list = this.datas.filter(d => d.index == row.cells[22].data);
                                $("#productionsite").val(list[0].name);
                                $("#address").val(list[0].address); 
                                $("#postal_address").val(list[0].postal_address);
                                $("#sitecountry").val(list[0].country);
                                $("#sitestate").val(list[0].state); 
                                $("#zip").val(list[0].zip);
                                $("#telephone").val(list[0].telephone); 
                                $("#email").val(list[0].email); 
                                $("#latitude").val(list[0].latitude);
                                $("#longitude").val(list[0].longitude);
                                $("#contactname").val(list[0].contactname); 
                                $("#contactaddress").val(list[0].contactaddress); 
                                $("#contaccountry").val(list[0].contaccountry); 
                                $("#contactstate").val(list[0].contactstate); 
                                $("#contaccity").val(list[0].contactcity); 
                                $("#contactzip").val(list[0].contactzip); 
                                $("#contacttelephone").val(list[0].contacttelephone);
                                $("#contactemail").val(list[0].contactemail);
                                $("#site_index").val(list[0].index);
                                $("#sitecountry").val(list[0].country).change();
                                $("#sitestate").val(list[0].state).change();
                                $("#sitecity").val(list[0].city).change();
                                $("#contaccountry").val(list[0].contactcountry).change();
                                $("#contactstate").val(list[0].contactstate).change();
                                $("#contaccity").val(list[0].contactcity).change();
                                
                                if (list[0].type == "1") {
                                    $("#sitio").prop("checked",true);
                                    $("#phu").prop("checked",false);
                                }
                                else{
                                    $("#phu").prop("checked",true);
                                    $("#sitio").prop("checked",false);
                                }


                                this.products = list[0].products;
                                this.grid_selector_products.updateConfig({
                                    data: list[0].products
                                }).forceRender();
                                $("#products").val(JSON.stringify(list[0].products));  

                                /*
                        "type_name": $('input[name=site_type]:checked', '#production_site_form').val() == 1 ? "Sitio" : "PHU", 
                        "type": $('input[name=site_type]:checked', '#production_site_form').val(), 
                        
                        "index": this.datas.length,
                        "products": this.products,
                                
                                */
                            }
                          }, 'Actualizar');
                        }
                    },
                ],
                data: [],
            }).render(document.getElementById("gridProductionSite"));

            this.grid_selector_products = new gridjs.Grid({
                columns: [
                    {
                        id: "productid",
                        name: "Producto",
                        hidden: true,
                    },
                    {
                        id: "product",
                        name: "Producto",
                    },
                    {
                        id: "hectareas",
                        name: "Hectareas",
                    },
                    {
                        id: "certify",
                        name: "Certificar",
                        hidden: true,
                    },
                    {
                        id: "pp",
                        name: "PP",
                        hidden: true,
                    },
                    {
                        id: "po",
                        name: "PO",
                        hidden: true,
                    },
                    {
                        id: "certify_text",
                        name: "Certificar",
                    },
                    {
                        id: "pp_text",
                        name: "PP",
                    },
                    {
                        id: "po_text",
                        name: "PO",
                    },
                    {
                        id: "index",
                        name: "index",
                        hidden: true,
                    }, 
                    { 
                        id:"action",
                        name: '',
                        formatter: (cell, row) => {
                          return gridjs.h('icon', {
                            style:'padding: 10px 20px;background-color: red;color: white;border: none; border-radius: 5px;cursor: pointer;',
                            onClick: () => {
                                const list = this.products.filter(prod => prod.index != row.cells[9].data);
                                this.products = list;
                                this.grid_selector_products.updateConfig({
                                    data: list
                                }).forceRender();
                                $("#products").val(JSON.stringify(list));  
                            }
                          }, 'Eliminar');
                        }
                    },
                ],
                data: [],
            }).render(document.getElementById("gridProducts"))

        
            var obj = JSON.parse($("#sites").val());
            var d = [];
            obj.forEach(function(objdata) {
                var product_list = [];
            
                objdata.products.forEach(function(objproduct){
                    product_list.push(
                        { 
                            "product": objproduct.product, 
                            "hectareas": objproduct.hectareas, 
                            "certify": objproduct.certify, 
                            "pp": objproduct.pp,
                            "po": objproduct.po,
                            "index": product_list.length,
                            "productid": objproduct.productid,
                            "certify_text": objproduct.certify_text,
                            "pp_text": objproduct.pp_text,
                            "po_text": objproduct.po_text,
                        }
                    );
                });
                d.push(
                    { 
                        "name": objdata.name, 
                        "type_name": objdata.type_name, 
                        "type": objdata.type, 
                        "address": objdata.address, 
                        "postal_address": objdata.postal_address,
                        "country": objdata.country_id, 
                        "state": objdata.state_id, 
                        "city": objdata.city_id, 
                        "zip": objdata.zip,
                        "telephone": objdata.telephone, 
                        "email": objdata.email, 
                        "latitude": objdata.latitude, 
                        "longitude": objdata.longitude,
                        "contactname": objdata.contactname, 
                        "contactaddress": objdata.contactaddress, 
                        "contactcountry": objdata.contactcountry, 
                        "contactstate": objdata.contactstate, 
                        "contactcity": objdata.contactcity, 
                        "contactzip": objdata.contactzip, 
                        "contacttelephone": objdata.contacttelephone,
                        "contactemail": objdata.contactemail,
                        "index": d.length,
                        "products": product_list,
                    }
                );
            });
            if (d.length > 0){
                this.datas = d;
                this.grid_selector.updateConfig({
                    data: d
                }).forceRender();
                $("#sites").val(JSON.stringify(d));
                $("#btn_send_sites").prop('disabled', false);
            }


            mapboxgl.accessToken = "pk.eyJ1IjoiYWJyczIiLCJhIjoiY2xsNXBmcXV0MDRreTNjdGpwMGh5ODQzcCJ9.z5jbioKMgT4Z0YhPMzJjJw";
            if ($("#latitude").val().trim() != "" && $("#longitude").val().trim() != ""){
                var lng = parseFloat($("#longitude").val().trim());
                var lat = parseFloat($("#latitude").val().trim());
                this._createMap(lng,lat)
            }
            let map = new mapboxgl.Map({
                container: "ubicationMap",
                style: "mapbox://styles/mapbox/streets-v11",
                center: [-102.1, 23.3],
                zoom: 10
            });
            let marker = new mapboxgl.Marker()
                .setLngLat([-102.1, 23.3])
                .addTo(map);

            map.on('click', (event) => {
                var coordinates = event.lngLat;
                marker.setLngLat(coordinates).addTo(map);
                $("#latitude").val(coordinates.lat);
                $("#longitude").val(coordinates.lng);
            });

            

            return this._super.apply(this, arguments);
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * On appointment type change: adapt appointment intro text and available
         * employees (if option enabled)
         *
         * @override
         * @param {Event} ev
         */
        _onCountryChange: function (ev) {
            var selValue = $("#sitecountry").val();
            this.states.innerHTML = '';
            for (var i = 0; i < this.optionStates.length; i++) {
                if (this.optionStates[i].dataset.option === selValue) {
                    this.states.appendChild(this.optionStates[i]);
                }
            }

        },
        _clearFields: function() {
                $("#productionsite").val("");
                $("#address").val("");
                $("#postal_address").val("");
                $("#zip").val("");
                $("#telephone").val("");
                $("#email").val("");
                $("#latitude").val("");
                $("#longitude").val("");
                $("#contactname").val("");
                $("#contactaddress").val("");
                $("#contactpostaladdress").val("");
                $("#contactzip").val("");
                $("#contacttelephone").val("");
                $("#contactemail").val("");
                $("#products").val("");
                this.products = [];
                this.grid_selector_products.updateConfig({
                    data: this.products
                }).forceRender();
        },
        _onStateChange: function (ev) {
            var selValue = $("#sitestate").val();
            this.cities.innerHTML = '';
            for (var i = 0; i < this.optionCities.length; i++) {
                if (this.optionCities[i].dataset.option === selValue) {
                    this.cities.appendChild(this.optionCities[i]);
                }
            }

        },
        _onOnlyNumbers: function (e) {
            var key = e.charCode;
            return key >= 48 && key <= 57;
        },
        _onOnlyNumbersAndSpecialCharacter: function (e) {
            var key = e.charCode;
            return key >= 45 && key <= 57;
        },
        _onClickProductionSite: function (ev) {

            if($("#productionsite").val().trim() == ""){
                $("#productionsite").focus();
                alert("Por favor capture un nombre para el Sitio de producción o PHU.");
            }
            else if($("#address").val().trim() == ""){
                $("#address").focus();
                alert("Por favor capture una dirección para el Sitio de producción o PHU.");
            }
            else if($("#sitecountry").val().length == 0){
                $("#sitecountry").focus();
                alert("Por favor capture un País para el Sitio de producción o PHU.");
            }
            else if($("#sitestate").val().trim().length == 0){
                $("#sitestate").focus();
                alert("Por favor capture un Estado para el Sitio de producción o PHU.");
            }
            else if($("#sitecity").val().trim().length == 0){
                $("#sitecity").focus();
                alert("Por favor capture una Ciudad para el Sitio de producción o PHU.");
            }
            else if($("#zip").val().trim() == ""){
                $("#zip").focus();
                alert("Por favor capture un Código Postal para el Sitio de producción o PHU.");
            }
            else if($("#telephone").val().trim() == ""){
                $("#telephone").focus();
                alert("Por favor capture un Teléfono para el Sitio de producción o PHU.");
            }
            else if($("#email").val().trim() == ""){
                $("#email").focus();
                alert("Por favor capture un Correo Electrónico para el Sitio de producción o PHU.");
            }
            else if($("#latitude").val().trim() == ""){
                $("#latitude").focus();
                alert("Por favor capture una Latitud para el Sitio de producción o PHU.");
            }
            else if($("#longitude").val().trim() == ""){
                $("#longitude").focus();
                alert("Por favor capture una Longitud para el Sitio de producción o PHU.");
            }
            else if($("#contactname").val().trim() == ""){
                $("#contactname").focus();
                alert("Por favor capture un Nombre de Contacto para el Sitio de producción o PHU.");
            }
            else if($("#contactaddress").val().trim() == ""){
                $("#contactaddress").focus();
                alert("Por favor capture una Dirección del Contacto para el Sitio de producción o PHU.");
            }
            else if($("#contaccountry").val().trim().length == 0){
                $("#contaccountry").focus();
                alert("Por favor capture una País del Contacto para el Sitio de producción o PHU.");
            }
            else if($("#contactstate").val().trim().length == 0){
                $("#contactstate").focus();
                alert("Por favor capture un Estado del Contacto para el Sitio de producción o PHU.");
            }
            else if($("#contaccity").val().trim().length == 0){
                $("#contaccity").focus();
                alert("Por favor capture una Ciudad del Contacto para el Sitio de producción o PHU.");
            }
            else if($("#contactzip").val().trim() == ""){
                $("#contactzip").focus();
                alert("Por favor capture una Código Postal del Contacto para el Sitio de producción o PHU.");
            }
            else if($("#contacttelephone").val().trim() == ""){
                $("#contacttelephone").focus();
                alert("Por favor capture un Teléfono del Contacto para el Sitio de producción o PHU.");
            }
            else if($("#contactemail").val().trim() == ""){
                $("#contactemail").focus();
                alert("Por favor capture un Correo Electrónico del Contacto para el Sitio de producción o PHU.");
            }
            else if(this.products.length <= 0){
                $("#product").focus();
                alert("Por favor capture por lo menos un producto para el Sitio de producción o PHU.");
            }
            else{

                if ($("#site_index").val() != ""){
                    const list = this.datas.filter(d => d.index != $("#site_index").val());
                    this.datas = list;

                }
                this.datas.push(
                    { 
                        "name": $("#productionsite").val().trim(), 
                        "type_name": $('input[name=site_type]:checked', '#production_site_form').val() == 1 ? "Sitio" : "PHU", 
                        "type": $('input[name=site_type]:checked', '#production_site_form').val(), 
                        "address": $("#address").val().trim(), 
                        "postal_address": $("#postal_address").val().trim(), 
                        "country": $("#sitecountry").val(), 
                        "state": $("#sitestate").val().trim(), 
                        "city": $("#sitecity").val().trim(), 
                        "zip": $("#zip").val().trim(),
                        "telephone": $("#telephone").val().trim(), 
                        "email": $("#email").val().trim(), 
                        "latitude": $("#latitude").val().trim(), 
                        "longitude": $("#longitude").val().trim(),
                        "contactname": $("#contactname").val().trim(), 
                        "contactaddress": $("#contactaddress").val().trim(), 
                        "contactcountry": $("#contaccountry").val().trim(), 
                        "contactstate": $("#contactstate").val().trim(), 
                        "contactcity": $("#contaccity").val().trim(), 
                        "contactzip": $("#contactzip").val().trim(), 
                        "contacttelephone": $("#contacttelephone").val().trim(),
                        "contactemail": $("#contactemail").val().trim(),
                        "index": this.datas.length,
                        "products": this.products,
                    }
                );
                

                
                this.grid_selector.updateConfig({
                    data: this.datas
                }).forceRender();
                $("#sites").val(JSON.stringify(this.datas));
                this._clearFields();
                if(this.datas.length > 0 ){
                    $("#btn_send_sites").prop('disabled', false);
                }
                $("#site_index").val("");
            }  

        },
        _onClickProduct: function (ev) {
            if($("#product").val().length == 0){
                $("#product").focus();
                alert("Por favor capture un Producto.");
            }
            else if($("#hect").val().trim() == ""){
                $("#hect").focus();
                alert("Por favor capture Hectareas para el producto.");
            }
            else if($("#forcertify").val().length == 0){
                $("#forcertify").focus();
                alert("Por favor capture la opción para certificar.");
            }
            else if($("#pp").val().length == 0){
                $("#pp").focus();
                alert("Por favor capture la opción PP.");
            }
            else if($("#po").val().length == 0){
                $("#po").focus();
                alert("Por favor capture la opción PO.");
            }
            else{
                this.products.push(
                    { 
                        "product": $('select[name="product"] option:selected').text().trim(), 
                        "hectareas": $("#hect").val(), 
                        "certify": $("#forcertify").val(), 
                        "pp": $("#pp").val(),
                        "po": $("#po").val(),
                        "productid": $("#product").val(),
                        "certify_text": $('select[name="forcertify"] option:selected').text().trim(),
                        "pp_text": $('select[name="pp"] option:selected').text().trim(),
                        "po_text": $('select[name="po"] option:selected').text().trim(),
                        "index": this.products.length,
                    }
                );
                this.grid_selector_products.updateConfig({
                    data: this.products
                }).forceRender();
                $("#products").val(JSON.stringify(this.products));  
                $("#product").val("");
                $("#hect").val("");
            }
        },

        _onContactStateChange: function (ev) {
            var selValue = $("#contactstate").val();
            this.contactCities.innerHTML = '';
            for (var i = 0; i < this.optionContactCities.length; i++) {
                if (this.optionContactCities[i].dataset.option === selValue) {
                    this.contactCities.appendChild(this.optionContactCities[i]);
                }
            }

        },
        _onContactCountryChange: function (ev) {
            var selValue = $("#contaccountry").val();
            this.contactStates.innerHTML = '';
            for (var i = 0; i < this.optionContactStates.length; i++) {
                if (this.optionContactStates[i].dataset.option === selValue) {
                    this.contactStates.appendChild(this.optionContactStates[i]);
                }
            }

        },
        _onLngLatSiteBlur: function(ev){
            if ($("#latitude").val().trim() != "" && $("#longitude").val().trim() != ""){
                var lng = parseFloat($("#longitude").val().trim());
                var lat = parseFloat($("#latitude").val().trim());
                this._createMap(lng,lat)
            }
        },
        _searchAddress: async function (ev) {
            var country = $('select[name="sitecountry"] option:selected').text().trim();
            var state = $('select[name="sitestate"] option:selected').text().trim();
            var city = $('select[name="sitecity"] option:selected').text().trim();
            if ($("#address").val().trim() != "" && country != "" && state != "" && city != "" 
            && $("#zip").val().trim() != ""){
                await this.rpc('/pao_get_geolocation',
                {
                    'fan_id': $("#fr_id").val().trim(), 
                    'fan_token': $("#fr_token").val().trim(), 
                    'street': $("#address").val().trim(), 
                    'zip': $("#zip").val().trim(),
                    'city': city, 
                    'state': state, 
                    'country': country,
                }).then(function (data) {
                    if (data.latitude != 0.00 && data.longitude != 0.00){
                         let map = new mapboxgl.Map({
                            container: "ubicationMap",
                            style: "mapbox://styles/mapbox/streets-v11",
                            center: [data.longitude,data.latitude],
                            zoom: 13
                        });
                        let marker = new mapboxgl.Marker()
                            .setLngLat([data.longitude, data.latitude])
                            .addTo(map);

                        map.on('click', (event) => {
                            var coordinates = event.lngLat;
                            marker.setLngLat(coordinates).addTo(map);
                            $("#latitude").val(coordinates.lat);
                            $("#longitude").val(coordinates.lng);
                        });
                        $("#longitude").val(data.longitude);
                        $("#latitude").val(data.latitude);
                    }
                    else{
                        alert("Oops! no se encontró el domicilio exacto, puedes ingresar las coordenadas y continuar con el llenado.")
                    }

                });
            }
        },
        _createMap: function(longitude, latitude) {
            let map = new mapboxgl.Map({
                container: "ubicationMap",
                style: "mapbox://styles/mapbox/streets-v11",
                center: [longitude,latitude],
                zoom: 13
            });
            let marker = new mapboxgl.Marker()
                .setLngLat([longitude,latitude])
                .addTo(map);
            map.on('click', (event) => {
                var coordinates = event.lngLat;
                marker.setLngLat(coordinates).addTo(map);
                $("#latitude").val(coordinates.lat);
                $("#longitude").val(coordinates.lng);
            });  
        },
        _onClickSaveProductionSite: async function (ev) {
            var production_site = JSON.parse($("#sites").val());
            
            if (production_site.length>0){
                await this.rpc('/pao/fillout/fans/production_site_phu',
                {
                    'cr_token': $("#fr_token").val().trim(),
                    'cr_id': $("#fr_id").val().trim(), 
                    'sites': $("#sites").val().trim(), 
                }).then(function (data) {
                    window.location = data.redirect_url;           
    
                });
            }
            else{
                alert("Favor de agregar un sitio de producción.");
            }
            
    
        },
    
});
export default publicWidget.registry.globalgapproductionsite;