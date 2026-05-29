odoo.define('nc_management.fnc_form', function (require) {
    'use strict';

    var FormController = require('web.FormController');
    var core = require('web.core');
    var _t = core._t;

    FormController.include({

        /**
         * Bloque le save si le numéro FNC n'est pas encore généré.
         * Le flag _skipFncSaveValidation est posé par _onButtonClicked
         * et _callButtonAction pour laisser passer l'auto-save du wizard.
         */
        saveRecord: function (handle, options) {
            if (this.modelName !== 'nc_management.nonconformity') {
                return this._super.apply(this, arguments);
            }
            var record = this.model.get(handle || this.handle);
            var name = record && record.data && record.data.name;
            // Bloque si name est vide, false, ou encore 'New'
            if ((!name || name === 'New') && !this._skipFncSaveValidation) {
                this.do_warn(
                    _t("Numéro FNC requis"),
                    _t("Veuillez générer le numéro FNC avant de sauvegarder la fiche.")
                );
                return $.Deferred().reject();
            }
            this._skipFncSaveValidation = false;
            return this._super.apply(this, arguments);
        },

        // Interception via _callButtonAction (Odoo 11 standard)
        _callButtonAction: function (attrs, record) {
            if (this.modelName === 'nc_management.nonconformity' &&
                    attrs && attrs.name === 'action_open_number_wizard') {
                this._skipFncSaveValidation = true;
            }
            return this._super.apply(this, arguments);
        },

        // Double interception via _onButtonClicked (filet de sécurité)
        _onButtonClicked: function (event) {
            var attrs = event.data && event.data.attrs;
            if (this.modelName === 'nc_management.nonconformity' &&
                    attrs && attrs.name === 'action_open_number_wizard') {
                this._skipFncSaveValidation = true;
            }
            return this._super.apply(this, arguments);
        },
    });
});
