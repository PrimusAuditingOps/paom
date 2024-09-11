/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.globalgapFans = publicWidget.Widget.extend({
    selector: '.o_website_fans_organization',
    events: {
        'change .o_website_fans_organization_form select[id="country"]': '_onCountryChange',
        'change .o_website_fans_organization_form select[id="state"]': '_onStateChange',
        'click .o_website_fans_organization_form input[name^="addonsgg"]': '_onAddonsChange',
        'click .btn_add_search_address': '_onAddressBlur',
        'blur .o_website_fans_organization_form input[name^="longitude"]': '_onLngLatBlur',
        'blur .o_website_fans_organization_form input[name^="latitude"]': '_onLngLatBlur',
        'click .o_website_fans_organization_form button[id="btn_send_organization"]': '_onClickSaveOrganization',
        'keypress .o_website_fans_organization_form input[name^="contact_telephone"]': '_onOnlyNumbers',
        'keypress .o_website_fans_organization_form input[name^="hired_workers"]': '_onOnlyNumbers',
        'keypress .o_website_fans_organization_form input[name^="subcontracted_workers"]': '_onOnlyNumbers',
        'keypress .o_website_fans_organization_form input[name^="telephone"]': '_onOnlyNumbers',
        'keypress .o_website_fans_organization_form input[name^="zip"]': '_onOnlyNumbers',
        'keypress .o_website_fans_organization_form input[name^="latitude"]': '_onOnlyNumbersAndSpecialCharacter',
        'keypress .o_website_fans_organization_form input[name^="longitude"]': '_onOnlyNumbersAndSpecialCharacter',
        
    },
    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);
        this.rpc = this.bindService("rpc");

    },
    /**
     * @override
     * @param {Object} parent
     */
    start: function (parent) {

        this.countries = document.querySelector('#country');
        this.states = document.querySelector('#state');
        this.optionStates = this.states.querySelectorAll('option');
        this.cities = document.querySelector('#city');
        this.optionCities = this.cities.querySelectorAll('option');

        var countryInit = $("#country").val();
        var stateInit = $("#state").val();
        var cityInit = $("#city").val();
        $("#country").val(countryInit).change();
        $("#state").val(stateInit).change();
        $("#city").val(cityInit).change();

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
            console.log(coordinates);
            marker.setLngLat(coordinates).addTo(map);
            $("#latitude").val(coordinates.lat);
            $("#longitude").val(coordinates.lng);
        });
        var addon_array = $("#addons").val().toString().split(",");
        var grasp_module = $("#grasp_module").val();
        var flag = false;
        if ($("#addons").val().toString().trim() != ""){
            for(let i = 0; i<addon_array.length;i++){
                if (grasp_module.includes(addon_array[i])){
                    flag=true;
                    $('#div_grasp_module').css('visibility','visible');
                    break;
                }
            }
        }
        
        
        if (!flag){
            $('#div_grasp_module').css('visibility','hidden');
            $("#hired_workers").val("0");
            $("#subcontracted_workers").val("0");
        }

        

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
        var selValue = $("#country").val();
        this.states.innerHTML = '';
        for (var i = 0; i < this.optionStates.length; i++) {
            if (this.optionStates[i].dataset.option === selValue) {
                this.states.appendChild(this.optionStates[i]);
            }
        }

    },
    _onStateChange: function (ev) {
        var selValue = $("#state").val();
        this.cities.innerHTML = '';
        for (var i = 0; i < this.optionCities.length; i++) {
            if (this.optionCities[i].dataset.option === selValue) {
                this.cities.appendChild(this.optionCities[i]);
            }
        }

    },
    _onOnlyNumbers: function (e) {
        var key = e.charCode;
        console.log(key);
        return key >= 48 && key <= 57;
    },
    _onOnlyNumbersAndSpecialCharacter: function (e) {
        var key = e.charCode;
        console.log(key);
        return key >= 45 && key <= 57;
    },
    _onAddonsChange: function (ev) {
        var addons = new Array();
        var grasp_module = $("#grasp_module").val();

        var flag = false;
        $.each($("input[name='addonsgg']:checked"), function() {
            if (grasp_module.includes($(this).val())){
                flag = true;
                $('#div_grasp_module').css('visibility','visible')
            }
            addons.push($(this).val());
            
        });
        if(!flag){
            $('#div_grasp_module').css('visibility','hidden');
            $("#hired_workers").val("0");
            $("#subcontracted_workers").val("0");
        }
        let text = addons.toString();
        $("#addons").val(addons);
    },
    _onLngLatBlur: function(ev){
        if ($("#latitude").val().trim() != "" && $("#longitude").val().trim() != ""){
            var lng = parseFloat($("#longitude").val().trim());
            var lat = parseFloat($("#latitude").val().trim());
            this._createMap(lng,lat)
        }
    },
    _onAddressBlur: async function (ev) {
        var country = $('select[name="country"] option:selected').text().trim();
        var state = $('select[name="state"] option:selected').text().trim();
        var city = $('select[name="city"] option:selected').text().trim();
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
                        console.log(coordinates);
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
    _onClickSaveOrganization: async function (ev) {
        if ($('select[name="evaluation_type"] option:selected').val() != "1" && ($("#plmx").val().trim() == "" && $("#previous_cb").val().trim() == "" )){
            alert("Favor de capturar PL_México");
            $("#plmx").focus();
        }
        else if ($('select[name="evaluation_type"] option:selected').val() != "1" && $("#ggn").val().trim() == ""){
            alert("Favor de capturar GGN");
            $("#ggn").focus();
        }
        else if ($("#ggn").val().trim() != "" && $("#ggn").val().trim().length != 13){
            alert("Favor de capturar GGN de 13 digitos");
            $("#ggn").focus();
        }
        else if ($("#name").val().trim() == ""){
            alert("Favor de capturar Nombre de la entidad legal");
            $("#name").focus();
        }
        else if ($("#vat").val().trim() == ""){
            alert("Favor de capturar RFC");
            $("#vat").focus();
        }
        else if ($("#email").val().trim() == ""){
            alert("Favor de capturar Correo eletrónico");
            $("#email").focus();
        }
        else if ($("#telephone").val().trim() == ""){
            alert("Favor de capturar Telefono");
            $("#telephone").focus();
        }
        else if ($("#country").val() == null){
            alert("Favor de capturar País");
            $("#country").focus();
        }
        else if ($("#state").val() == null){
            alert("Favor de capturar Estado");
            $("#state").focus();
        }
        else if ($("#city").val() == null){
            alert("Favor de capturar Ciudad"); 
            $("#city").focus();
        }
        else if ($("#address").val().trim() == ""){
            alert("Favor de capturar Dirección");
            $("#address").focus();
        }
        else if ($("#zip").val().trim() == ""){
            alert("Favor de capturar CP");
            $("#zip").focus();
        }
        else if ($("#latitude").val().trim() == ""){
            alert("Favor de capturar Latitud");
            $("#latitude").focus();
        }
        else if ($("#longitude").val().trim() == ""){
            alert("Favor de capturar Longitud");
            $("#longitude").focus();
        }
        else if ($("#contact_name").val().trim() == ""){
            alert("Favor de capturar Persona de contacto");
            $("#contact_name").focus();
        }
        else if ($("#contact_position").val().trim() == ""){
            alert("Favor de capturar Desempeño o Cargo");
            $("#contact_position").focus();
        }
        else if ($("#contact_telephone").val().trim() == ""){
            alert("Favor de capturar Telefono de contacto");
            $("#contact_telephone").focus();
        }
        else if ($("#contact_email").val().trim() == ""){
            alert("Favor de capturar Correo eletrónico de contacto");
            $("#contact_email").focus();
        }
        else{
            await this.rpc('/pao/fillout/fans/products',
            {   
                'fr_id': $("#fr_id").val().trim(), 
                'fr_token': $("#fr_token").val().trim(),
                'unannounced': $("#unannounced").is(':checked'),
                "plmx": $("#plmx").val().trim(), 
                "ggn": $("#ggn").val().trim(),
                "globalgap_version":  $('select[name="globalgap_version"] option:selected').val(),
                "certification_option": $('select[name="certification_option"] option:selected').val(),
                "evaluation_type": $('select[name="evaluation_type"] option:selected').val(),
                "name": $("#name").val().trim(),
                "website": $("#website").val().trim(),
                "address": $("#address").val().trim(),
                "colony": $("#colony").val().trim(),
                "city": $('select[name="city"] option:selected').val(),
                "state": $('select[name="state"] option:selected').val(),
                "country": $('select[name="country"] option:selected').val(),
                "zip": $("#zip").val().trim(),
                "telephone": $("#telephone").val().trim(),
                "email":  $("#email").val().trim(),
                "gln":  $("#gln").val().trim(),
                "vat":  $("#vat").val().trim(),
                "previous_cb":  $("#previous_cb").val().trim(),
                "latitude":  $("#latitude").val().trim(),
                "longitude":  $("#longitude").val().trim(),
                "contact_name":  $("#contact_name").val().trim(),
                "contact_position": $("#contact_position").val().trim(),
                "contact_telephone":  $("#contact_telephone").val().trim(),
                "contact_email":  $("#contact_email").val().trim(),
                "rights_of_access": $('select[name="rights_of_access"] option:selected').val(),
                "addons": $("#addons").val(),
                "postal_address": $("#postal_address").val().trim(),
                "previous_ggn": $("#previous_ggn").val().trim(),
                "subcontracted_workers": $("#subcontracted_workers").val().trim(),
                "hired_workers": $("#hired_workers").val().trim(),
            }).then(function (data) {
                window.location = data.redirect_url;           
            });
        }
        
    },

});
export default publicWidget.registry.globalgapFans;