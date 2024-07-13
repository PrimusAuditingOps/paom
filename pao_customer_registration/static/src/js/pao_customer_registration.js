/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PaoCustomerRegistration = publicWidget.Widget.extend({
    selector: '.o_website_customer_registration',
    events: {
        'change .o_website_customer_registration_form select[id="country"]': '_onCountryChange',
        'change .o_website_customer_registration_form select[id="state"]': '_onStateChange',
        'click .o_website_customer_registration_form button[id="btn_add_contact"]': '_onClickContact',
        'click .o_website_customer_registration_form button[id="btn_send"]': '_onSave',
        
    },
    /**
         * @constructor
         */
    init: function () {
        this._super.apply(this, arguments);
        this.datas = []
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


        $("#contacts").val("");
        $("#nombrecontacto").val("");
        $("#nombrepuesto").val("");
        $("#correocontacto").val("");
        $("#movilcontacto").val("");
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
    _onCountryChange: function (ev) {
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
    convertFileToBase64 : (file) => {
        return new Promise((resolve) => {
          const reader = new FileReader()
          reader.onloadend = () => resolve(reader.result.toString().replace(/^data:(.*,)?/, ''))
          reader.readAsDataURL(file)
        })
    },

    _onSave: async function(ev){


        if ($("#attachments").val() == ""){

            alert("Favor de seleccionar un Certificado Fiscal.");
            
        }
        else if ($("#attachments_proof_of_address").val() == ""){

            alert("Favor de seleccionar un Comprobante de Domicilio.");
            
        }
        else if ($("#attachments_bank_account").val() == ""){

            alert("Favor de seleccionar la Carátula de estado de cuenta bancario.");
            
        }
        else if ($("#attachments_sat").val() == ""){

            alert("Favor de seleccionar Opinión de cumplimiento SAT.");
            
        }
        else if ($("#name").val() == ""){

            alert("Favor de capturar un Nombre.");
            
        }
        else if ($("#rfc").val() == ""){

            alert("Favor de capturar un RFC.");
            
        }
        else if ($("#phonenumber").val() == ""){

            alert("Favor de capturar un Teléfono.");
            
        }
        else if ($("#email").val() == ""){

            alert("Favor de capturar un Email.");
            
        }
        else if ($("#street").val() == ""){

            alert("Favor de capturar el domicilio.");
            
        }
        else if ($("#zip").val() == ""){

            alert("Favor de capturar el C.P.");  
        }
        else if ($("#country").val() == ""){

            alert("Favor de capturar un País.");  
        }
        else if ($("#state").val() == ""){

            alert("Favor de capturar un Estado.");  
        }
        else if ($("#city").val() == ""){

            alert("Favor de capturar una Ciudad.");  
        }
        else if ($("#cfdiuse").val() == ""){

            alert("Favor de capturar un USO de CFDI.");  
        }
        else{
            var fileConst = $('#attachments')[0].files[0];
            const attachments = await this.convertFileToBase64(fileConst);

            var fileProof = $('#attachments_proof_of_address')[0].files[0];
            const attachments_proof_of_address = await this.convertFileToBase64(fileProof);

            var fileBank = $('#attachments_bank_account')[0].files[0];
            const attachments_bank_account = await this.convertFileToBase64(fileBank);

            var fileSat = $('#attachments_sat')[0].files[0];
            const attachments_sat = await this.convertFileToBase64(fileSat);
                        
            await this.rpc('/pao/customer/registration/send', {
                cr_token: $("#cr_token").val(), 
                cr_id: $("#cr_id").val(), 
                company: $("#name").val(), 
                rfc: $("#rfc").val(), 
                phonenumber: $("#phonenumber").val(), 
                email: $("#email").val(), 
                street: $("#street").val(), 
                zip: $("#zip").val(), 
                country: $("#country").val(), 
                state: $("#state").val(),
                city: $("#city").val(), 
                cfdiuse: $("#cfdiuse").val(),
                attachments: attachments, 
                attachments_proof_of_address: attachments_proof_of_address, 
                attachments_bank_account: attachments_bank_account, 
                attachments_sat: attachments_sat, 
                contacts: $("#contacts").val(), 
                asesor: $("#asesor").val(),
            }).then(function (link) {
                window.location = link;    
            });

        }







        

        
    },
});
export default publicWidget.registry.PaoCustomerRegistration;