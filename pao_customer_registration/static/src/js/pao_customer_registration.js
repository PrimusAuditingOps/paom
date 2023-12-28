odoo.define('pao_customer_registration.customer', function (require) {

    'use strict';


    var publicWidget = require('web.public.widget');
    

    publicWidget.registry.customerRegistration = publicWidget.Widget.extend({

        selector: '.o_website_customer_registration',
        events: {
            'change .o_website_customer_registration_form select[id="country"]': '_onAppointmentTypeChange',
            'change .o_website_customer_registration_form select[id="state"]': '_onStateChange',
            'click .btn_add_contact': '_onClickContact'
        },

        /**
         * @constructor
         */
        init: function () {
            this._super.apply(this, arguments);
            this.datas = []

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


            $("#contacts").val("");
            $("#nombrecontacto").val("");
            $("#nombrepuesto").val("");
            $("#correocontacto").val("");
            $("#movilcontacto").val("");
            var contactName = $.parseHTML("<p>hola</p>")[0];
            this.datas = []
            this.grid_selector = new gridjs.Grid({
                columns: [
                    {
                        id: "name",
                        name: gridjs.html('<img src="/pao_customer_registration/static/images/name.png" alt="Icon" width="25px" height="25px"/>'),
                    },
                    {
                        id: "occupation",
                        name: gridjs.html('<img src="/pao_customer_registration/static/images/occupation.png" alt="Icon" width="25px" height="25px"/>'),
                    },
                    {
                        id: "email",
                        name: gridjs.html('<img src="/pao_customer_registration/static/images/email.png" alt="Icon" width="25px" height="25px"/>'),
                    },
                    {
                        id: "phone",
                        name: gridjs.html('<img src="/pao_customer_registration/static/images/phone.png" alt="Icon" width="25px" height="25px"/>'),
                    },
                    /*{
                        name: "Eliminar",
                    }, 
                    {
                        name: "Index",
                    }, */
                ],
                data: [],
            }).render(document.getElementById("wrapper"))

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
        _onAppointmentTypeChange: function (ev) {
            console.log("");
            var selValue = $("#country").val();
            this.states.innerHTML = '';
            for (var i = 0; i < this.optionStates.length; i++) {
                if (this.optionStates[i].dataset.option === selValue) {
                    this.states.appendChild(this.optionStates[i]);
                }
            }

        },
        _onStateChange: function (ev) {
            console.log("");
            var selValue = $("#state").val();
            this.cities.innerHTML = '';
            for (var i = 0; i < this.optionCities.length; i++) {
                if (this.optionCities[i].dataset.option === selValue) {
                    this.cities.appendChild(this.optionCities[i]);
                }
            }

        },
        _onClickContact: function (ev) {
            var nombre = $("#nombrecontacto").val();
            var puesto = $("#nombrepuesto").val();
            var correo = $("#correocontacto").val();
            var movil = $("#movilcontacto").val();

            this.datas.push({ "name": nombre, "occupation": puesto, "email": correo, "phone": movil });
            this.grid_selector.updateConfig({
                data: this.datas
            }).forceRender();
            $("#contacts").val(JSON.stringify(this.datas));
            $("#nombrecontacto").val("");
            $("#nombrepuesto").val("");
            $("#correocontacto").val("");
            $("#movilcontacto").val("");
            $("#nombrecontacto").focus();
        },
    });
});