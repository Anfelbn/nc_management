odoo.define('nc_management.dashboard', function (require) {
    'use strict';

    var Widget = require('web.Widget');
    var core = require('web.core');
    var rpc = require('web.rpc');

    var NcDashboard = Widget.extend({
        template: 'NcDashboard',
        events: {},

        start: function () {
            var self = this;
            var sup = this._super.apply(this, arguments);
            rpc.query({
                model: 'nc_management.dashboard',
                method: 'get_stats',
                args: [],
                kwargs: {},
            }).then(function (d) {
                self.$('#fnc_draft').text(d.fnc_draft);
                self.$('#fnc_submitted').text(d.fnc_submitted);
                self.$('#fnc_in_progress').text(d.fnc_in_progress);
                self.$('#fnc_closed').text(d.fnc_closed);
                self.$('#fac_draft').text(d.fac_draft);
                self.$('#fac_open').text(d.fac_open);
                self.$('#fac_verified').text(d.fac_verified);
                self.$('#fac_closed').text(d.fac_closed);
                self.$('#taux').text(d.taux_cloture + '%');

                var labels = d.monthly.map(function (m) { return m.month; });
                var data   = d.monthly.map(function (m) { return m.count; });
                var ctx = self.$('#nc_chart')[0].getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'FNC ouvertes',
                            data: data,
                            backgroundColor: 'rgba(83,74,183,0.7)',
                            borderColor: 'rgba(83,74,183,1)',
                            borderWidth: 1,
                        }],
                    },
                    options: {
                        scales: { yAxes: [{ ticks: { beginAtZero: true, stepSize: 1 } }] },
                        legend: { display: false },
                    },
                });

                var tbody = self.$('#urgent_body');
                tbody.empty();
                if (d.urgent.length === 0) {
                    tbody.append('<tr><td colspan="4" style="text-align:center;color:#888;">Aucune fiche en retard</td></tr>');
                } else {
                    d.urgent.forEach(function (f) {
                        tbody.append(
                            '<tr>' +
                            '<td>' + f.name + '</td>' +
                            '<td>' + (f.direction_id ? f.direction_id[1] : '') + '</td>' +
                            '<td>' + (f.service_dpt || '') + '</td>' +
                            '<td>' + (f.date || '') + '</td>' +
                            '</tr>'
                        );
                    });
                }

                var rev_body = self.$('#revision_body');
                rev_body.empty();
                if (d.revisions.length === 0) {
                    rev_body.append('<tr><td colspan="4" style="text-align:center;color:#888;">Aucune revision enregistree</td></tr>');
                } else {
                    d.revisions.forEach(function (r) {
                        var type_lbl = r.doc_type === 'fnc' ? 'FNC' : 'FAC';
                        var row = $(
                            '<tr>' +
                            '<td>' + type_lbl + '</td>' +
                            '<td style="text-align:center;"><a href="#" class="o_rev_link" data-id="' + r.id + '" style="font-weight:bold;color:#534AB7;">Rev ' + (r.revision_number < 10 ? '0' + r.revision_number : r.revision_number) + '</a></td>' +
                            '<td>' + r.revision_date + '</td>' +
                            '<td>' + (r.description || '') + '</td>' +
                            '</tr>'
                        );
                        row.find('.o_rev_link').on('click', function (e) {
                            e.preventDefault();
                            self.do_action('nc_management.action_report_revision', {
                                additional_context: {
                                    active_ids: [r.id],
                                },
                            });
                        });
                        rev_body.append(row);
                    });
                }
            });
            return sup;
        },
    });

    core.action_registry.add('nc_dashboard', NcDashboard);
    return NcDashboard;
});
