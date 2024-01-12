odoo.define('pao_globalgap_fans.globalgapfans', function (require) {

    'use strict';


    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.globalgapFans = publicWidget.Widget.extend({

        selector: '.o_website_fans_organization',
        events: {
            'change .o_website_fans_organization_form select[id="country"]': '_onCountryChange',
            'change .o_website_fans_organization_form select[id="state"]': '_onStateChange',
            'click .o_website_fans_organization_form input[name^="addonsgg"]': '_onAddonsChange',
            'click .btn_add_search_address': '_onAddressBlur',
            'blur .o_website_fans_organization_form input[name^="longitude"]': '_onLngLatBlur',
            'blur .o_website_fans_organization_form input[name^="latitude"]': '_onLngLatBlur',
        },
        /**
         * @constructor
         */
        init: function () {
            this._super.apply(this, arguments);

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
                zoom: 4
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
            for(let i = 0; i<addon_array.length;i++){
                if (grasp_module.includes(addon_array[i])){
                    flag=true;
                    $('#div_grasp_module').css('visibility','visible');
                    break;
                }
            }
            if (!flag){
                $('#div_grasp_module').css('visibility','hidden');
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
        _onAddressBlur: function (ev) {
            var country = $('select[name="country"] option:selected').text().trim();
            var state = $('select[name="state"] option:selected').text().trim();
            var city = $('select[name="city"] option:selected').text().trim();
            if ($("#address").val().trim() != "" && country != "" && state != "" && city != "" 
            && $("#zip").val().trim() != ""){
                ajax.jsonRpc('/pao_get_geolocation', 'call', 
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
                            zoom: 4
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

                });
            }
        },
        _createMap: function(longitude, latitude) {
            let map = new mapboxgl.Map({
                container: "ubicationMap",
                style: "mapbox://styles/mapbox/streets-v11",
                center: [longitude,latitude],
                zoom: 10
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

        
        
    });
});