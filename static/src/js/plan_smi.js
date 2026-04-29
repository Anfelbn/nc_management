odoo.define('nc_management.plan_smi', function(require) {
    'use strict';
    var Widget = require('web.Widget');
    var core = require('web.core');
    var rpc = require('web.rpc');

    var PlanSmi = Widget.extend({
        template: 'NcPlanSmi',
        start: function() {
            var self = this;
            var sup = this._super.apply(this, arguments);
            rpc.query({
                model: 'nc_management.dashboard',
                method: 'get_plan_smi_stats',
                args: [],
                kwargs: {},
            }).then(function(d) {
                // Table efficacité
                var tbody = self.$('#smi_body');
                tbody.empty();
                var colors = ['#e67e22','#e74c3c','#27ae60','#2980b9'];
                d.categories.forEach(function(cat, i) {
                    var data = cat.data;
                    var tc = data.taux >= 70 ? '#27ae60' :
                             data.taux >= 50 ? '#e67e22' : '#e74c3c';
                    tbody.append(
                        '<tr>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;font-weight:bold;color:' + colors[i] + '">' + cat.label + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;text-align:center;color:#27ae60;font-weight:bold;">' + data.efficace + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;text-align:center;color:#e74c3c;font-weight:bold;">' + data.non_efficace + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;text-align:center;">' + data.realise_100 + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;text-align:center;">' + data.realise_50plus + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;text-align:center;">' + data.realise_50moins + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;text-align:center;">' +
                            '<span style="background:' + tc + ';color:white;padding:3px 10px;border-radius:99px;font-weight:bold;">' +
                            data.taux + '%</span>' +
                        '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;text-align:center;font-weight:bold;">' + data.total + '</td>' +
                        '</tr>'
                    );
                });
                // Graphe
                var labels = d.categories.map(function(c){ return c.label; });
                var eff = d.categories.map(function(c){ return c.data.efficace; });
                var non = d.categories.map(function(c){ return c.data.non_efficace; });
                var ctx = self.$('#smi_chart')[0].getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            { label: 'Efficace', data: eff,
                              backgroundColor: 'rgba(39,174,96,0.8)' },
                            { label: 'Non efficace', data: non,
                              backgroundColor: 'rgba(231,76,60,0.8)' }
                        ]
                    },
                    options: {
                        scales: { yAxes: [{ticks:{beginAtZero:true,stepSize:1}}] }
                    }
                });
                // Table processus
                var ptbody = self.$('#proc_body');
                ptbody.empty();
                d.processus.forEach(function(p) {
                    var color = p.taux >= 70 ? '#27ae60' :
                                p.taux >= 50 ? '#e67e22' : '#e74c3c';
                    var bw = Math.min(p.taux, 100);
                    ptbody.append(
                        '<tr>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;">' + p.label + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;width:200px;">' +
                            '<div style="background:#eee;border-radius:99px;height:14px;">' +
                            '<div style="background:' + color + ';width:' + bw + '%;height:14px;border-radius:99px;"></div>' +
                            '</div></td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;text-align:center;font-weight:bold;color:' + color + '">' + p.taux + '%</td>' +
                        '</tr>'
                    );
                });
            });
            return sup;
        }
    });

    core.action_registry.add('nc_plan_smi', PlanSmi);
    return PlanSmi;
});
