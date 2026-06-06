odoo.define('nc_management.list_no_export', function (require) {
    'use strict';

    var ListController = require('web.ListController');
    var Sidebar        = require('web.Sidebar');
    var _t             = require('web.core')._t;

    /**
     * Surcharge de renderSidebar : retire l'option "Export" du menu Action
     * lorsque le contexte de l'action contient no_export: true.
     */
    ListController.include({
        renderSidebar: function ($node) {
            if (!this.hasSidebar || this.sidebar) {
                return;
            }

            var ctx = this.model.get(this.handle, {raw: true}).getContext();
            var no_export = ctx && ctx.no_export;

            var other = [];
            if (!no_export) {
                other.push({
                    label:    _t("Export"),
                    callback: this._onExportData.bind(this),
                });
            }
            if (this.archiveEnabled) {
                other.push({
                    label:    _t("Archive"),
                    callback: this._onToggleArchiveState.bind(this, true),
                });
                other.push({
                    label:    _t("Unarchive"),
                    callback: this._onToggleArchiveState.bind(this, false),
                });
            }
            if (this.is_action_enabled('delete')) {
                other.push({
                    label:    _t('Delete'),
                    callback: this._onDeleteSelectedRecords.bind(this),
                });
            }

            this.sidebar = new Sidebar(this, {
                editable: this.is_action_enabled('edit'),
                env: {
                    context:   ctx,
                    activeIds: this.getSelectedIds(),
                    model:     this.modelName,
                },
                actions: _.extend(this.toolbarActions, {other: other}),
            });
            this.sidebar.appendTo($node);
            this._toggleSidebar();
        },
    });
});
