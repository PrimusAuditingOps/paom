odoo.define('pao_osp.form_crop', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.OspFormCrop = publicWidget.Widget.extend({
        selector: '#form-content', // El div principal que envuelve todo
        events: {
            'click #btn_add_site': '_onAddSite',
            'click #btn_save_progress': '_onSaveProgress',
            'click #btn_submit_osp': '_onSubmitForm',
            'click .btn-delete-site': '_onDeleteSite',
            'change .site-input': '_onChangeSiteInput',
        },

        start: function () {
            this.ospId = parseInt(this.$('input[name="osp_id"]').val());
            this.sitesTbody = this.$('#sites_tbody');
            this.sitesJsonInput = this.$('#4g_sites_json');
            
            try {
                this.sitesData = JSON.parse(this.sitesJsonInput.val() || '[]');
            } catch(e) { 
                this.sitesData = []; 
            }

            this._renderSitesTable();
            return this._super.apply(this, arguments);
        },

           _renderSitesTable: function () {
            this.sitesTbody.empty();
            if(this.sitesData.length === 0) {
                this.sitesData.push({id: '', address: '', city: '', zip: ''}); 
            }
            
            var self = this;
            this.sitesData.forEach(function(site, index) {
                var tr = `
                    <tr>
                        <td><input type="text" class="form-control border-0 bg-transparent site-input" data-index="${index}" data-field="id" value="${site.id || ''}" placeholder="ID..."/></td>
                        <td><input type="text" class="form-control border-0 bg-transparent site-input" data-index="${index}" data-field="address" value="${site.address || ''}" placeholder="Address..."/></td>
                        <td><input type="text" class="form-control border-0 bg-transparent site-input" data-index="${index}" data-field="city" value="${site.city || ''}" placeholder="City..."/></td>
                        <td><input type="text" class="form-control border-0 bg-transparent site-input" data-index="${index}" data-field="zip" value="${site.zip || ''}" placeholder="Zip..."/></td>
                        <td><button type="button" class="btn btn-sm text-danger btn-delete-site" data-index="${index}"><i class="fa fa-trash"></i></button></td>
                    </tr>
                `;
                self.sitesTbody.append(tr);
            });
            this.sitesJsonInput.val(JSON.stringify(this.sitesData));
        },

        _onAddSite: function (ev) {
            this.sitesData.push({id: '', address: '', city: '', zip: ''});
            this._renderSitesTable();
        },

        _onChangeSiteInput: function (ev) {
            var $input = $(ev.currentTarget);
            var idx = $input.data('index');
            var fld = $input.data('field');
            this.sitesData[idx][fld] = $input.val();
            this.sitesJsonInput.val(JSON.stringify(this.sitesData));
        },

        _onDeleteSite: function (ev) {
            var idx = $(ev.currentTarget).data('index');
            this.sitesData.splice(idx, 1);
            this._renderSitesTable();
        },

        _gatherFormData: function() {
            var data = {};
            this.$('.osp-input').each(function() {
                if(this.type === 'radio' || this.type === 'checkbox') {
                    if(this.checked) data[this.name] = this.value;
                } else {
                    data[this.name] = this.value;
                }
            });
            return data;
        },

        _onSaveProgress: function (ev) {
            this._saveForm(false);
        },

        _onSubmitForm: function (ev) {
            if(!this.$('#req_name').val() || !this.$('#req_sign').val() || !this.$('#req_date').val()) {
                alert("Please complete the electronic signature fields before submitting.");
                return;
            }
            if(confirm("Are you sure you want to submit your Organic System Plan? You will not be able to edit it after submission.")) {
                this._saveForm(true);
            }
        },

        _saveForm: function(isSubmit) {
            var $statusText = this.$('#save_status');
            $statusText.show().text('Saving...').removeClass('text-danger').addClass('text-muted');
            
            var finalData = this._gatherFormData();

            ajax.jsonRpc(`/my/osp/save/${this.ospId}`, 'call', {
                form_data: finalData,
                is_submit: isSubmit
            }).then(function (data) {
                if(data.success) {
                    $statusText.text('Saved!');
                    setTimeout(function() { $statusText.hide(); }, 2000);
                    if(isSubmit) window.location.href = '/my/osp';
                } else {
                    $statusText.text('Error al guardar').removeClass('text-muted').addClass('text-danger');
                }
            }).catch(function () {
                $statusText.text('Error de conexión').removeClass('text-muted').addClass('text-danger');
            });
        }
    });
});