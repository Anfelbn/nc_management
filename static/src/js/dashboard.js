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

                var ae = d.analyse_efficacite;
                var categories = [
                    { key: 'reclamation_pi',  label: 'Réclamation PI',  color: '#e67e22' },
                    { key: 'nc_produit',      label: 'NC Produit',           color: '#e74c3c' },
                    { key: 'environnement',   label: 'Environnement',        color: '#27ae60' },
                    { key: 'sst',             label: 'SST',                  color: '#2980b9' },
                ];

                var efficacite_tbody = self.$('#efficacite_body');
                efficacite_tbody.empty();
                categories.forEach(function (cat) {
                    var data = ae[cat.key];
                    var taux_color = data.taux >= 70 ? '#27ae60' : data.taux >= 50 ? '#e67e22' : '#e74c3c';
                    efficacite_tbody.append(
                        '<tr>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;font-weight:bold;color:' + cat.color + '">' + cat.label + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;text-align:center;">' + data.total + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;text-align:center;color:#27ae60;font-weight:bold;">' + data.efficace + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;text-align:center;color:#e74c3c;font-weight:bold;">' + data.non_efficace + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;text-align:center;">' +
                            '<span style="background:' + taux_color + ';color:white;padding:3px 10px;border-radius:99px;font-weight:bold;">' +
                            data.taux + '%</span>' +
                        '</td>' +
                        '</tr>'
                    );
                });
            });
            return sup;
        },
    });

    core.action_registry.add('nc_dashboard', NcDashboard);
    return NcDashboard;
});
