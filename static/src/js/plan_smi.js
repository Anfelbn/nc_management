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
                // 4 couleurs modérément sombres en rotation : bleu, rouge, vert, ambre
                var colors = ['#2575b8', '#d44535', '#1fa255', '#cc8800'];
                d.categories.forEach(function(cat, i) {
                    var data = cat.data;
                    var tc = data.taux >= 70 ? '#1fa255' :
                             data.taux >= 50 ? '#cc8800' : '#d44535';
                    tbody.append(
                        '<tr>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'font-weight:bold;color:' + colors[i % 4] + '">' +
                            cat.label + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'text-align:center;color:#1fa255;font-weight:bold;">' +
                            data.efficace + '</td>' +
                        '<td style="padding:8px;border:1px solid #dee2e6;' +
                            'text-align:center;color:#d44535;font-weight:bold;">' +
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

                // ── Histogramme vertical moderne — Taux d'efficacité par catégorie ──
                var $cv = self.$('#smi_chart');
                if ($cv.length && d.categories_chart && d.categories_chart.length) {
                    var smi_labels = d.categories_chart.map(function(c){ return c.label; });
                    var smi_taux   = d.categories_chart.map(function(c){ return c.taux;  });

                    setTimeout(function() {
                        var canvas = $cv[0];
                        var dpr    = window.devicePixelRatio || 1;
                        var W      = Math.max($cv.parent().width() || 0, 700);
                        var H      = 420;
                        canvas.width        = W * dpr;
                        canvas.height       = H * dpr;
                        canvas.style.width  = W + 'px';
                        canvas.style.height = H + 'px';
                        var ctx = canvas.getContext('2d');
                        ctx.scale(dpr, dpr);

                        var pL = 52, pR = 24, pT = 50, pB = 100;
                        var cW = W - pL - pR, cH = H - pT - pB;
                        var n  = smi_labels.length;
                        var gW = cW / n;
                        var bW = Math.min(gW * 0.48, 42);

                        // Titre centré
                        ctx.fillStyle = '#1e293b';
                        ctx.font = 'bold 13px Segoe UI';
                        ctx.textAlign = 'center';
                        ctx.fillText('Taux efficacité en %', W / 2, 26);

                        // Fond blanc
                        ctx.fillStyle = '#ffffff';
                        ctx.fillRect(pL, pT, cW, cH);

                        // Grilles horizontales grises
                        for (var i = 0; i <= 4; i++) {
                            var gy = pT + cH * (1 - i / 4);
                            ctx.strokeStyle = i === 0 ? '#cbd5e1' : '#e2e8f0';
                            ctx.lineWidth = i === 0 ? 1.2 : 0.8;
                            ctx.beginPath(); ctx.moveTo(pL, gy); ctx.lineTo(pL + cW, gy); ctx.stroke();
                            // Graduation axe Y
                            ctx.strokeStyle = '#94a3b8'; ctx.lineWidth = 1;
                            ctx.beginPath(); ctx.moveTo(pL - 5, gy); ctx.lineTo(pL, gy); ctx.stroke();
                            // Label axe Y
                            ctx.fillStyle = '#64748b'; ctx.font = '10px Segoe UI'; ctx.textAlign = 'right';
                            ctx.fillText(i * 25 + '%', pL - 8, gy + 3);
                        }

                        // Axe Y
                        ctx.strokeStyle = '#94a3b8'; ctx.lineWidth = 1.5;
                        ctx.beginPath(); ctx.moveTo(pL, pT); ctx.lineTo(pL, pT + cH); ctx.stroke();
                        // Axe X
                        ctx.beginPath(); ctx.moveTo(pL, pT + cH); ctx.lineTo(pL + cW, pT + cH); ctx.stroke();

                        // Barres avec coins arrondis en haut
                        smi_taux.forEach(function(val, gi) {
                            var bh  = (Math.min(val, 100) / 100) * cH;
                            var x   = pL + gi * gW + (gW - bW) / 2;
                            var y   = pT + cH - bh;
                            var r   = Math.min(4, bh / 2);

                            // Couleur selon taux (mêmes couleurs qu'avant)
                            var cLight, cDark;
                            if (val >= 70)      { cLight = '#7AAFEE'; cDark = '#3A72B8'; }
                            else if (val >= 50) { cLight = '#F5C877'; cDark = '#C9920A'; }
                            else                { cLight = '#E88080'; cDark = '#B03030'; }

                            if (bh > 0) {
                                // Dégradé vertical clair → foncé
                                var grad = ctx.createLinearGradient(x, y, x, y + bh);
                                grad.addColorStop(0, cLight);
                                grad.addColorStop(1, cDark);
                                ctx.fillStyle = grad;
                                // Barre avec coins arrondis en haut
                                ctx.beginPath();
                                ctx.moveTo(x + r, y);
                                ctx.lineTo(x + bW - r, y);
                                ctx.quadraticCurveTo(x + bW, y, x + bW, y + r);
                                ctx.lineTo(x + bW, y + bh);
                                ctx.lineTo(x, y + bh);
                                ctx.lineTo(x, y + r);
                                ctx.quadraticCurveTo(x, y, x + r, y);
                                ctx.closePath();
                                ctx.fill();
                            }

                            // Valeur % au-dessus de la barre
                            ctx.fillStyle = val >= 70 ? '#2A5A9A' : val >= 50 ? '#A07808' : '#8C2020';
                            ctx.font = 'bold 10px Segoe UI'; ctx.textAlign = 'center';
                            ctx.fillText(val + '%', x + bW / 2, Math.max(y - 5, pT + 12));
                        });

                        // Labels axe X inclinés vers la gauche
                        ctx.fillStyle = '#475569'; ctx.font = '10px Segoe UI';
                        smi_labels.forEach(function(lbl, gi) {
                            var cx = pL + gi * gW + gW / 2;
                            ctx.save();
                            ctx.translate(cx, pT + cH + 10);
                            ctx.rotate(-Math.PI / 5);
                            ctx.textAlign = 'right';
                            ctx.fillText(lbl, 0, 0);
                            ctx.restore();
                        });
                    }, 150);
                }

                // ── Table processus ──
                var ptbody = self.$('#proc_body');
                ptbody.empty();
                d.processus.forEach(function(p) {
                    var color = p.taux >= 70 ? '#1fa255' :
                                p.taux >= 50 ? '#cc8800' : '#d44535';
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
