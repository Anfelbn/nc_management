odoo.define('nc_management.dashboard', function(require) {
    'use strict';
    var Widget = require('web.Widget');
    var core   = require('web.core');
    var rpc    = require('web.rpc');

    var NcDashboard = Widget.extend({
        template: 'NcDashboard',

        start: function() {
            var self = this;
            this._super.apply(this, arguments);
            rpc.query({
                model: 'nc_management.dashboard',
                method: 'get_stats',
                args: [], kwargs: {}
            }).then(function(d) {

                // ── KPI FNC ──
                self.$('#fnc_total').text(d.fnc_total);
                self.$('#fnc_cours').text(d.fnc_cours);
                self.$('#fnc_envoyes').text(d.fnc_envoyes);
                self.$('#fnc_closed').text(d.fnc_closed);
                self.$('#fnc_retard').text(d.fnc_retard);
                self.$('#taux_cloture').text(d.taux_cloture + '%');
                self.$('#fnc_recues').text(d.fnc_recues);

                // ── KPI FAC ──
                self.$('#fac_total').text(d.fac_total);
                self.$('#fac_open').text(d.fac_open);
                self.$('#fac_verif').text(d.fac_verif);
                self.$('#fac_closed').text(d.fac_closed);
                self.$('#fac_retard').text(d.fac_retard);
                self.$('#taux_eff').text(d.taux_efficacite + '%');
                self.$('#fac_recues').text(d.fac_recues);

                Chart.defaults.global.defaultFontColor = '#8BABC8';

                // ── Graphe évolution ──
                var labels = d.monthly_fnc.map(function(m){ return m.short; });
                var fnc_data = d.monthly_fnc.map(function(m){ return m.count; });
                var fac_data = d.monthly_fac.map(function(m){ return m.count; });
                var ctx1 = self.$('#evo_chart')[0].getContext('2d');
                new Chart(ctx1, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            { label: 'FNC', data: fnc_data,
                              backgroundColor: 'rgba(59,158,255,0.8)',
                              borderColor: '#3B9EFF', borderWidth: 1 },
                            { label: 'FAC', data: fac_data,
                              type: 'line',
                              borderColor: '#00D98B',
                              backgroundColor: 'transparent',
                              borderWidth: 2, pointRadius: 3,
                              borderDash: [4,3] }
                        ]
                    },
                    options: {
                        scales: {
                            yAxes: [{ ticks: { beginAtZero: true, stepSize: 1 } }]
                        },
                        legend: { display: true, position: 'top',
                            labels: { fontSize: 11, boxWidth: 12 } }
                    }
                });

                // ── Donut FNC par type ──
                var tc = d.type_counts;
                var type_labels = Object.keys(tc);
                var type_data   = Object.values(tc);
                var type_colors = [
                    '#3B9EFF','#00D98B','#FF9500',
                    '#FF4D4D','#8B7CF6','#5C7A99'];
                var ctx2 = self.$('#type_chart')[0].getContext('2d');
                new Chart(ctx2, {
                    type: 'doughnut',
                    data: {
                        labels: type_labels,
                        datasets: [{ data: type_data,
                            backgroundColor: type_colors,
                            borderWidth: 1 }]
                    },
                    options: {
                        legend: { display: true, position: 'right',
                            labels: { fontSize: 10, boxWidth: 10 } },
                        cutoutPercentage: 60
                    }
                });

                // ── Barres FNC par département ──
                var dept_labels = d.dept_list.map(function(x){ return x[0]; });
                var dept_data   = d.dept_list.map(function(x){ return x[1]; });
                var ctx3 = self.$('#dept_chart')[0].getContext('2d');
                new Chart(ctx3, {
                    type: 'horizontalBar',
                    data: {
                        labels: dept_labels,
                        datasets: [{ data: dept_data,
                            backgroundColor: 'rgba(59,158,255,0.8)',
                            borderColor: '#3B9EFF', borderWidth: 1 }]
                    },
                    options: {
                        legend: { display: false },
                        scales: {
                            xAxes: [{ ticks: { beginAtZero: true, stepSize: 1 } }]
                        }
                    }
                });

                // ── Barres état global ──
                function setStatBar(id, pct, color) {
                    self.$('#' + id + '_bar').css('width', Math.min(pct,100) + '%')
                        .css('background', color);
                    self.$('#' + id + '_pct').text(pct + '%');
                }
                setStatBar('s_fnc_closed', d.pct_fnc_closed, '#00D98B');
                setStatBar('s_fnc_cours',  d.pct_fnc_cours,  '#3B9EFF');
                setStatBar('s_fac_eff',    d.pct_fac_eff,    '#00D98B');
                setStatBar('s_fac_retard', d.pct_fac_retard, '#FF4D4D');
                setStatBar('s_fnc_retard', d.pct_fnc_retard, '#FF4D4D');

                // ── FAC à clôturer ──
                var fac_list = self.$('#fac_cloturer_list');
                fac_list.empty();
                if (d.fac_a_cloturer.length === 0) {
                    fac_list.append(
                        '<div style="text-align:center;color:#5C7A99;' +
                        'padding:12px;font-size:12px;">Aucune FAC en attente</div>');
                } else {
                    d.fac_a_cloturer.forEach(function(f) {
                        var bcls = f.badge === 'red' ?
                            'background:rgba(255,77,77,0.15);color:#FF4D4D' :
                            f.badge === 'orange' ?
                            'background:rgba(255,149,0,0.15);color:#FF9500' :
                            'background:rgba(0,217,139,0.15);color:#00D98B';
                        fac_list.append(
                            '<div style="display:flex;justify-content:space-between;' +
                            'align-items:center;padding:9px 12px;border-radius:8px;' +
                            'border:0.5px solid #243D5C;margin-bottom:7px;' +
                            'background:#162438;">' +
                            '<div><div style="font-size:13px;font-weight:500;' +
                            'color:#E8F0F8;">' + f.name +
                            '</div><div style="font-size:11px;color:#8BABC8;' +
                            'margin-top:2px;">' +
                            f.dept + ' · ' + f.date + '</div></div>' +
                            '<span style="font-size:10px;padding:2px 8px;' +
                            'border-radius:99px;' + bcls + '">' +
                            f.label + '</span></div>'
                        );
                    });
                }

                // ── FNC en retard ──
                var fnc_list = self.$('#fnc_retard_list');
                fnc_list.empty();
                if (d.fnc_retard_list.length === 0) {
                    fnc_list.append(
                        '<div style="text-align:center;color:#5C7A99;' +
                        'padding:12px;font-size:12px;">Aucune FNC en retard</div>');
                } else {
                    d.fnc_retard_list.forEach(function(f) {
                        var dept = f.direction_id ? f.direction_id[1] : '';
                        var days = Math.floor(
                            (new Date() - new Date(f.date)) / 86400000);
                        var bcls = days > 7 ?
                            'background:rgba(255,77,77,0.15);color:#FF4D4D' :
                            'background:rgba(255,149,0,0.15);color:#FF9500';
                        fnc_list.append(
                            '<div style="display:flex;justify-content:space-between;' +
                            'align-items:center;padding:9px 12px;border-radius:8px;' +
                            'border:0.5px solid #243D5C;margin-bottom:7px;' +
                            'background:#162438;">' +
                            '<div><div style="font-size:13px;font-weight:500;' +
                            'color:#E8F0F8;">' + f.name +
                            '</div><div style="font-size:11px;color:#8BABC8;' +
                            'margin-top:2px;">' +
                            dept + '</div></div>' +
                            '<span style="font-size:10px;padding:2px 8px;' +
                            'border-radius:99px;' + bcls + '">' +
                            days + ' jours</span></div>'
                        );
                    });
                }

                // ── Barres FNC par département (bas de page) ──
                var dept_mini = self.$('#dept_mini_list');
                dept_mini.empty();
                var max_d = d.dept_list.length > 0 ?
                    Math.max.apply(null, d.dept_list.map(function(x){
                        return x[1]; })) : 1;
                d.dept_list.forEach(function(item) {
                    var pct = Math.round(item[1] / max_d * 100);
                    dept_mini.append(
                        '<div style="display:flex;align-items:center;' +
                        'gap:8px;margin-bottom:7px;">' +
                        '<div style="font-size:11px;color:#8BABC8;width:90px;' +
                        'text-align:right;flex-shrink:0;">' + item[0] + '</div>' +
                        '<div style="flex:1;height:8px;background:#243D5C;' +
                        'border-radius:4px;overflow:hidden;">' +
                        '<div style="height:100%;border-radius:4px;' +
                        'background:#3B9EFF;width:' + pct + '%;"></div></div>' +
                        '<div style="font-size:11px;color:#8BABC8;width:20px;' +
                        'text-align:right;">' + item[1] + '</div></div>'
                    );
                });
            });
        }
    });

    core.action_registry.add('nc_dashboard', NcDashboard);
    return NcDashboard;
});
