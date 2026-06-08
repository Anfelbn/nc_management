odoo.define('nc_management.disable_import', function (require) {
    'use strict';

    var ListController = require('web.ListController');

    // En Odoo 11, import="false" sur <tree> n'est pas lu nativement.
    // On retire le bouton du DOM après son rendu si l'arch le demande.
    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.renderer &&
                    this.renderer.arch &&
                    this.renderer.arch.attrs &&
                    this.renderer.arch.attrs['import'] === 'false' &&
                    this.$buttons) {
                this.$buttons.find('.o_button_import').remove();
            }
        },
    });
});
