odoo.define('nc_management.plan_smi', function(require) {
    'use strict';
    var Widget = require('web.Widget');
    var core = require('web.core');
    var rpc = require('web.rpc');

    var PlanSmi = Widget.extend({
        template: 'NcPlanSmi',
        events: {
            'click .o_export_smi': '_onExportSmi',
        },

        _onExportSmi: function() {
            this.do_action('nc_management.action_export_smi_analysis_wizard');
        },

        start: function() {
            var self = this;
            this._super.apply(this, arguments);
            rpc.query({
                model: 'nc_management.dashboard',
                method: 'get_plan_smi_stats',
                args: [], kwargs: {},
            }).then(function(d) {

                // ── Table efficacité ──
                var tbody = self.$('#smi_body');
                tbody.empty();
                var colors = ['#2980b9','#e74c3c','#27ae60','#e67e22'];
                d.categories.forEach(function(cat, i) {
                    var data = cat.data;
                    var tc = data.taux >= 70 ? '#27ae60' :
                             data.taux >= 50 ? '#e67e22' : '#e74c3c';
                    tbody.append(
                        '<tr>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'font-weight:bold;color:' + colors[i] + '">' +
                            cat.label + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'text-align:center;color:#27ae60;font-weight:bold;">' +
                            data.efficace + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'text-align:center;color:#e74c3c;font-weight:bold;">' +
                            data.non_efficace + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'text-align:center;">' + data.realise_100 + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'text-align:center;">' + data.realise_50plus + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'text-align:center;">' + data.realise_50moins + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'text-align:center;">' +
                            '<span style="background:' + tc +
                            ';color:white;padding:2px 10px;border-radius:99px;' +
                            'font-weight:bold;">' + data.taux + '%</span>' +
                        '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'text-align:center;font-weight:bold;">' +
                            data.total + '</td>' +
                        '</tr>'
                    );
                });

                // ── Diagramme en bâtons — Taux d'efficacité par catégorie ──
                var $cv = self.$('#smi_chart');
                if ($cv.length && d.categories_chart && d.categories_chart.length) {
                    var labels   = d.categories_chart.map(function(c){ return c.label; });
                    var tauxData = d.categories_chart.map(function(c){ return c.taux;  });
                    var cvEl     = $cv[0];
                    var ctx2d    = cvEl.getContext('2d');

                    // Dégradé vertical bleu clair → bleu foncé (palette dashboard)
                    var grad = ctx2d.createLinearGradient(0, 0, 0, cvEl.height);
                    grad.addColorStop(0, '#7AAFEE');
                    grad.addColorStop(1, '#2A5A9A');

                    new Chart(ctx2d, {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: "Taux d'efficacité %",
                                data: tauxData,
                                backgroundColor: grad,
                                borderColor:     '#1e3a8a',
                                borderWidth:     1,
                            }]
                        },
                        options: {
                            responsive:          true,
                            maintainAspectRatio: false,
                            title: {
                                display:   true,
                                text:      "Taux d'efficacité par catégorie (%)",
                                fontSize:  14,
                                fontColor: '#2c3e50',
                                fontStyle: 'bold',
                            },
                            legend: { display: false },
                            scales: {
                                yAxes: [{
                                    ticks: {
                                        beginAtZero: true,
                                        max: 100,
                                        stepSize: 25,
                                        callback: function(v){ return v + '%'; },
                                        fontColor: '#94a3b8',
                                        fontSize:  11,
                                    },
                                    gridLines: {
                                        color:     'rgba(0,0,0,0.06)',
                                        zeroLineColor: '#cbd5e1',
                                    },
                                }],
                                xAxes: [{
                                    gridLines: { display: false },
                                    ticks: {
                                        maxRotation: 45,
                                        minRotation: 45,
                                        fontColor:   '#64748b',
                                        fontSize:    10,
                                    },
                                }],
                            },
                            // Valeur % affichée au-dessus de chaque barre
                            animation: {
                                onComplete: function() {
                                    var c    = this.chart.ctx;
                                    var ds   = this.data.datasets[0];
                                    var meta = this.chart.getDatasetMeta(0);
                                    meta.data.forEach(function(bar, idx) {
                                        var val = ds.data[idx];
                                        if (!val) { return; }
                                        c.save();
                                        c.fillStyle    = '#1e3a8a';
                                        c.font         = 'bold 10px "Segoe UI", Arial';
                                        c.textAlign    = 'center';
                                        c.textBaseline = 'bottom';
                                        c.fillText(val + '%', bar._model.x, bar._model.y - 2);
                                        c.restore();
                                    });
                                },
                            },
                            tooltips: {
                                callbacks: {
                                    label: function(ti, data) {
                                        return data.datasets[ti.datasetIndex]
                                                   .data[ti.index] + '%';
                                    },
                                },
                            },
                        }
                    });
                }

                // ── Table processus ──
                var ptbody = self.$('#proc_body');
                ptbody.empty();
                d.processus.forEach(function(p) {
                    var color = p.taux >= 70 ? '#27ae60' :
                                p.taux >= 50 ? '#e67e22' : '#e74c3c';
                    var bw = Math.min(p.taux, 100);
                    ptbody.append(
                        '<tr>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'font-weight:bold;">' + p.label + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'width:240px;">' +
                            '<div style="background:#eee;border-radius:4px;' +
                                'height:18px;position:relative;">' +
                            '<div style="background:' + color +
                                ';width:' + bw + '%;height:18px;' +
                                'border-radius:4px;"></div>' +
                            '</div></td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'text-align:center;font-weight:bold;' +
                            'font-size:15px;color:' + color + '">' +
                            p.taux + '%</td>' +
                        '</tr>'
                    );
                });
            });
        }
    });

    core.action_registry.add('nc_plan_smi', PlanSmi);
    return PlanSmi;
});
