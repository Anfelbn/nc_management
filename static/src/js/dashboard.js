odoo.define('nc_management.dashboard', function(require){
    'use strict';

    var core    = require('web.core');
    var Widget  = require('web.Widget');

    var NcDashboard = Widget.extend({
        template: 'NcDashboard',

        init: function(){
            this._super.apply(this, arguments);
            this.stats = this._emptyStats();
        },

        _emptyStats: function(){
            return {
                today: '',
                fnc_recues: [],
                fac_recues: [],
                received_docs: [],
                received_by_date: {},
                fac_a_cloturer: [],
                fnc_retard_list: [],
                dept_list: [],
                direction_stats: [],
                scope_totals: {
                    direction: {fnc: 0, fac: 0},
                    department: {fnc: 0, fac: 0},
                    service: {fnc: 0, fac: 0},
                },
                type_counts: {
                    nc_produit: 0,
                    sst: 0,
                    environnement: 0,
                    reclamation: 0,
                    audit: 0,
                    autres: 0,
                },
                monthly_labels: [],
                monthly_fnc: [],
                monthly_fac: [],
                monthly_fnc_global: [],
                monthly_fac_global: [],
                calendar_events: {},
                fnc_total: 0,
                fnc_cours: 0,
                fnc_envoyes: 0,
                fnc_closed: 0,
                fnc_retard: 0,
                taux_cloture: 0,
                fac_total: 0,
                fac_open: 0,
                fac_verif: 0,
                fac_closed: 0,
                fac_retard: 0,
                taux_efficacite: 0,
                fnc_audit: 0,
                fnc_audit_interne: 0,
                fnc_audit_externe: 0,
                fac_audit: 0,
                fac_audit_interne: 0,
                fac_audit_externe: 0,
                audit_interne_total: 0,
                audit_externe_total: 0,
                fnc_brouillon: 0,
                fnc_validated: 0,
                fac_brouillon: 0,
                fac_submitted: 0,
                taux_validation_fac: 0,
                taux_cloture_fac: 0,
                period: '1m',
                calendar_year: 0,
                calendar_month: 0,
            };
        },

        willStart: function(){
            var self = this;
            var superDef = this._super.apply(this, arguments);
            var statsDef = this._rpc({
                model:  'nc_management.dashboard',
                method: 'get_stats',
                args:   [],
            }).then(function(stats){
                self.stats = stats;
            });
            return $.when(superDef, statsDef);
        },

        start: function(){
            this._super.apply(this, arguments);
            this._bindAll();
        },

        _bindAll: function(){
            var self = this;

            this.$('.pb').on('click', function(){
                self.$('.pb').removeClass('active');
                $(this).addClass('active');
                var period = $(this).data('period') || '1m';
                self._reload(period);
            });

            this.$el.on('click', '.btn-open', function(){
                var model = $(this).data('model');
                var id    = parseInt($(this).data('id'), 10);
                self.do_action({
                    type:      'ir.actions.act_window',
                    res_model: model,
                    res_id:    id,
                    views:     [[false, 'form']],
                    target:    'current',
                });
            });

            this.$el.on('click', '.btn-list', function(){
                var model  = $(this).data('model') || 'nc_management.nonconformity';
                var domain = JSON.parse($(this).attr('data-domain') || '[]');
                self.do_action({
                    type:      'ir.actions.act_window',
                    res_model: model,
                    domain:    domain,
                    views:     [[false, 'list'], [false, 'form']],
                    target:    'current',
                });
            });

            this.$el.on('click', '.dir-bar, .gc-lbl[data-direction-id]', function(){
                self.$('.dir-bar').removeClass('selected');
                self.$('.gc-lbl').removeClass('selected');
                $(this).addClass('selected');
                var dirId   = parseInt($(this).data('direction-id'), 10);
                var dirName = $(this).data('direction');
                var kind    = $(this).data('kind') || 'fnc';
                self._onDirectionClick(dirId, dirName, kind);
            });

            this.$el.on('click', '.dept-pill', function(){
                self.$('.dept-pill').removeClass('active');
                $(this).addClass('active');
                self.$('.dir-filter-svc-row').hide();
                self.$('.svc-pill').removeClass('active');
                var deptData = JSON.parse($(this).attr('data-dept'));
                var kind = self._currentKind || 'fnc';
                self._onDeptClick(deptData, kind);
            });

            this.$el.on('click', '.svc-pill', function(){
                self.$('.svc-pill').removeClass('active');
                $(this).addClass('active');
                var svcData = JSON.parse($(this).attr('data-svc'));
                var kind = self._currentKind || 'fnc';
                self._onSvcClick(svcData, kind);
            });

            this._initCalendar();
            this._renderDirectionPie();
            this.$('.pb').removeClass('active');
            this.$('.pb[data-period="' + (this.stats.period || '1m') + '"]').addClass('active');
            setTimeout(function(){
                self._drawEvoChart();
                self._drawGlobalChart();
            }, 120);
        },

        _onDirectionClick: function(dirId, dirName, kind){
            var self = this;
            this._currentKind = kind;
            this._rpc({
                model:  'nc_management.dashboard',
                method: 'get_direction_details',
                args:   [dirId, this.stats.period || '1m'],
            }).then(function(data){
                self._currentDirData = data;
                // Update direction stat box
                self.$('.scope-dir-fnc').text(data.fnc_count);
                self.$('.scope-dir-fac').text(data.fac_count);
                self.$('.scope-dir-title').text('Direction : ' + dirName);
                // Reset dept/service boxes
                self.$('.scope-dept-fnc').text('—');
                self.$('.scope-dept-fac').text('—');
                self.$('.scope-dept-title').text('Par département');
                self.$('.scope-svc-fnc').text('—');
                self.$('.scope-svc-fac').text('—');
                self.$('.scope-svc-title').text('Par service');
                // Pie chart
                var types = (kind === 'fac' ? data.fac_types : data.fnc_types) || {};
                self._renderPie(types, (kind === 'fac' ? 'FAC' : 'FNC') + ' · ' + dirName);
                self.$('.dir-pie-scope').text('Types ' + (kind==='fac'?'FAC':'FNC') + ' — ' + dirName);
                // Dept pills
                self._renderDeptPills(data.departments, kind);
                // Show filter zone
                self.$('.dir-filter-zone').show();
                self.$('.dir-filter-svc-row').hide();
            });
        },

        _onDeptClick: function(deptData, kind){
            this.$('.scope-dept-fnc').text(deptData.fnc_count);
            this.$('.scope-dept-fac').text(deptData.fac_count);
            this.$('.scope-dept-title').text('Département : ' + deptData.name);
            this.$('.scope-svc-fnc').text('—');
            this.$('.scope-svc-fac').text('—');
            this.$('.scope-svc-title').text('Par service');
            var types = (kind === 'fac' ? deptData.fac_types : deptData.fnc_types) || {};
            this._renderPie(types, (kind==='fac'?'FAC':'FNC') + ' · ' + deptData.name);
            this.$('.dir-pie-scope').text('Types ' + (kind==='fac'?'FAC':'FNC') + ' — ' + deptData.name);
            this._renderSvcPills(deptData.services || [], kind);
            if(deptData.services && deptData.services.length){
                this.$('.dir-filter-svc-row').show();
            }
        },

        _onSvcClick: function(svcData, kind){
            this.$('.scope-svc-fnc').text(svcData.fnc_count);
            this.$('.scope-svc-fac').text(svcData.fac_count);
            this.$('.scope-svc-title').text('Service : ' + svcData.name);
            var types = (kind === 'fac' ? svcData.fac_types : svcData.fnc_types) || {};
            this._renderPie(types, (kind==='fac'?'FAC':'FNC') + ' · ' + svcData.name);
            this.$('.dir-pie-scope').text('Types ' + (kind==='fac'?'FAC':'FNC') + ' — ' + svcData.name);
        },

        _renderDeptPills: function(departments, kind){
            var html = '';
            if(!departments || !departments.length){
                html = '<span style="font-size:10px;color:#94a3b8">Aucun département configuré</span>';
            } else {
                departments.forEach(function(d){
                    html += '<div class="dir-pill dept-pill" data-dept=\'' +
                        JSON.stringify({id:d.id, name:d.name, fnc_count:d.fnc_count,
                            fac_count:d.fac_count, fnc_types:d.fnc_types,
                            fac_types:d.fac_types, services:d.services}) +
                        '\'>' + _.escape(d.name) +
                        ' <span style="opacity:.6">(' + (kind==='fac'?d.fac_count:d.fnc_count) + ')</span></div>';
                });
            }
            this.$('.dir-dept-pills').html(html);
        },

        _renderSvcPills: function(services, kind){
            var html = '';
            if(!services || !services.length){
                html = '<span style="font-size:10px;color:#94a3b8">Aucun service configuré</span>';
            } else {
                services.forEach(function(s){
                    html += '<div class="dir-pill svc-pill" data-svc=\'' +
                        JSON.stringify({id:s.id, name:s.name, fnc_count:s.fnc_count,
                            fac_count:s.fac_count, fnc_types:s.fnc_types,
                            fac_types:s.fac_types}) +
                        '\'>' + _.escape(s.name) +
                        ' <span style="opacity:.6">(' + (kind==='fac'?s.fac_count:s.fnc_count) + ')</span></div>';
                });
            }
            this.$('.dir-svc-pills').html(html);
        },

        _renderPie: function(types, title){
            var nc = types.nc_produit || 0;
            var sst = types.sst || 0;
            var env = types.environnement || 0;
            var rec = types.reclamation || 0;
            var audit = types.audit || 0;
            var autres = types.autres || 0;
            var p1=nc, p2=p1+sst, p3=p2+env, p4=p3+rec, p5=p4+audit;
            var bg = 'conic-gradient(#2196F3 0% '+p1+'%,#10B981 '+p1+'% '+p2+'%,#FF9800 '+p2+'% '+p3+'%,#EF4444 '+p3+'% '+p4+'%,#7C3AED '+p4+'% '+p5+'%,#64748B '+p5+'% 100%)';
            this.$('.dir-pie').css('background', bg);
            this.$('.dir-pie-title').text(title);
            this.$('.dir-pie-legend').html(
                '<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#2196F3"></span> NC Produit '+nc+'%</div>' +
                '<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#10B981"></span> SST '+sst+'%</div>' +
                '<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#FF9800"></span> Env. '+env+'%</div>' +
                '<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#EF4444"></span> Réclam. '+rec+'%</div>' +
                '<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#7C3AED"></span> Audit '+audit+'%</div>' +
                '<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#64748B"></span> Autres '+autres+'%</div>'
            );
        },

        _reload: function(period){
            var self = this;
            this._rpc({
                model:  'nc_management.dashboard',
                method: 'get_stats',
                args:   [period],
            }).then(function(stats){
                self.stats = stats;
                self.renderElement();
                self._bindAll();
            });
        },

        _initCalendar: function(){
            var self    = this;
            var now     = new Date();
            var year    = this.stats.calendar_year  || now.getFullYear();
            var month   = (this.stats.calendar_month || (now.getMonth() + 1)) - 1;
            var FR_M    = ['Janvier','Février','Mars','Avril','Mai','Juin',
                           'Juillet','Août','Septembre','Octobre','Novembre','Décembre'];
            var pickerYear = year;

            function todayKey(){
                return now.getFullYear() + '-' +
                       String(now.getMonth()+1).padStart(2,'0') + '-' +
                       String(now.getDate()).padStart(2,'0');
            }

            function render(y, m){
                var events   = self.stats.calendar_events || {};
                var first    = new Date(y, m, 1).getDay();
                var startOff = (first === 0) ? 6 : first - 1;
                var daysInM  = new Date(y, m+1, 0).getDate();
                var prevLast = new Date(y, m, 0).getDate();
                var html = '';
                for(var i = 0; i < startOff; i++){
                    html += '<div class="cal-day other-month">'+(prevLast - startOff + i + 1)+'</div>';
                }
                for(var d = 1; d <= daysInM; d++){
                    var key = y+'-'+String(m+1).padStart(2,'0')+'-'+String(d).padStart(2,'0');
                    var ev  = events[key] || {};
                    var isToday = (y===now.getFullYear() && m===now.getMonth() && d===now.getDate());
                    var cls = 'cal-day'+(isToday?' today':'');
                    var dots = '';
                    if(ev.fnc)  dots += '<div class="cdot" style="background:#2196F3"></div>';
                    if(ev.fac)  dots += '<div class="cdot" style="background:#EF4444"></div>';
                    if(ev.plan) dots += '<div class="cdot" style="background:#7C3AED"></div>';
                    html += '<div class="'+cls+'" data-date="'+key+'">'+d+(dots?'<div class="cal-dot-row">'+dots+'</div>':'')+'</div>';
                }
                var total = startOff + daysInM;
                var next = 1;
                while(total % 7 !== 0){ html += '<div class="cal-day other-month">'+next+'</div>'; total++; next++; }
                self.$('.cal-grid-body').html(html);
                self.$('.cal-month-label').text(FR_M[m]+' '+y);
                // Ré-sélectionner aujourd'hui si on est sur le bon mois
                if(y===now.getFullYear() && m===now.getMonth()){
                    self.$('.cal-day.today').addClass('selected');
                }
                self.$('.cal-grid-body .cal-day:not(.other-month)').off('click').on('click', function(){
                    var k = $(this).data('date');
                    self.$('.cal-day').removeClass('selected');
                    $(this).addClass('selected');
                    self._renderReceivedDocs((self.stats.received_by_date || {})[k] || [], k);
                });
            }

            function renderPicker(){
                self.$('.cal-picker-yr').text(pickerYear);
                self.$('.cal-pm').removeClass('cal-pm-active');
                if(pickerYear === year){
                    self.$('.cal-pm[data-m="'+month+'"]').addClass('cal-pm-active');
                }
            }

            // Clic sur l'en-tête → ouvre/ferme le sélecteur
            this.$('.cal-header-pick').off('click').on('click', function(){
                var picker = self.$('.cal-picker');
                picker.toggle();
                if(picker.is(':visible')){
                    pickerYear = year;
                    renderPicker();
                }
            });

            // Navigation année dans le sélecteur
            this.$('.cal-yr-prev').off('click').on('click', function(e){
                e.stopPropagation(); pickerYear--; renderPicker();
            });
            this.$('.cal-yr-next').off('click').on('click', function(e){
                e.stopPropagation(); pickerYear++; renderPicker();
            });

            // Sélection d'un mois → 2e clic
            this.$('.cal-pm').off('click').on('click', function(e){
                e.stopPropagation();
                year  = pickerYear;
                month = parseInt($(this).data('m'), 10);
                self.$('.cal-picker').hide();
                render(year, month);
            });

            render(year, month);

            // Afficher par défaut les fiches d'aujourd'hui
            var tk   = todayKey();
            var tDocs = (self.stats.received_by_date || {})[tk] || [];
            self._renderReceivedDocs(tDocs, tk);
        },

        _renderReceivedDocs: function(docs, key){
            var self = this;
            var label = key ? this._formatDateKey(key) : "Documents reçus aujourd'hui";
            this.$('.received-sub').text(label);

            if(!docs.length){
                this.$('.received-list').html('<div class="nc-empty">Aucun document reçu pour cette date.</div>');
                return;
            }

            // Grouper : chaque FNC avec ses FAC liées
            var groups  = {};   // fnc.id → {fnc, facs:[]}
            var orphFacs = [];
            var plans   = [];

            docs.forEach(function(item){
                if(item.kind === 'FNC') groups[item.id] = {fnc: item, facs: []};
            });
            docs.forEach(function(item){
                if(item.kind === 'FAC'){
                    if(item.fnc_id && groups[item.fnc_id]) groups[item.fnc_id].facs.push(item);
                    else orphFacs.push(item);
                } else if(item.kind === 'Plan'){
                    plans.push(item);
                }
            });

            var html = '';

            // FNC + FAC liées dans le même bloc
            Object.keys(groups).forEach(function(fid){
                var g   = groups[fid];
                var fnc = g.fnc;
                html += '<div style="border:1px solid #e2e8f0;border-radius:10px;margin-bottom:8px;overflow:hidden">';
                // En-tête FNC
                html += '<div style="display:flex;gap:10px;align-items:flex-start;padding:10px;background:#f8fafc">'
                      + '<div class="nc-avatar avatar-blue">' + _.escape(fnc.initials || 'FN') + '</div>'
                      + '<div style="flex:1;min-width:0">'
                      + '<div style="display:flex;justify-content:space-between;align-items:center">'
                      + '<div class="nc-notif-ref">' + _.escape(fnc.name || '') + ' · ' + _.escape(fnc.type || '') + '</div>'
                      + '<span class="badge blue">FNC</span>'
                      + '</div>'
                      + '<div class="nc-notif-info">' + _.escape(fnc.department || '') + (fnc.responsible ? ' · ' + _.escape(fnc.responsible) : '') + ' · ' + _.escape(fnc.date || '') + '</div>'
                      + '<div class="nc-notif-actions"><div class="btn-sm primary btn-open" data-model="nc_management.nonconformity" data-id="' + fnc.id + '">Ouvrir FNC</div></div>'
                      + '</div></div>';
                // FAC liées (indentées avec barre rouge)
                g.facs.forEach(function(fac){
                    html += '<div style="display:flex;gap:8px;align-items:flex-start;padding:8px 10px 8px 16px;border-top:1px solid #f1f5f9;background:white">'
                          + '<div style="width:2px;background:#EF4444;border-radius:2px;align-self:stretch;flex-shrink:0;margin-top:4px"></div>'
                          + '<div class="nc-avatar avatar-red" style="width:28px;height:28px;font-size:10px">' + _.escape(fac.initials || 'FA') + '</div>'
                          + '<div style="flex:1;min-width:0">'
                          + '<div style="display:flex;justify-content:space-between;align-items:center">'
                          + '<div style="font-size:11px;font-weight:600;color:#1e293b">' + _.escape(fac.name || '') + ' · Action corrective</div>'
                          + '<span class="badge red">FAC</span>'
                          + '</div>'
                          + '<div class="nc-notif-info">' + _.escape(fac.department || '') + ' · ' + _.escape(fac.date || '') + '</div>'
                          + '<div class="nc-notif-actions"><div class="btn-sm btn-open" data-model="nc_management.corrective_action" data-id="' + fac.id + '">Ouvrir FAC</div></div>'
                          + '</div></div>';
                });
                html += '</div>';
            });

            // FAC orphelines (sans FNC dans la liste courante)
            orphFacs.forEach(function(item){
                html += '<div class="nc-notif">'
                      + '<div class="nc-avatar avatar-red">' + _.escape(item.initials || 'FA') + '</div>'
                      + '<div class="nc-notif-body">'
                      + '<div style="display:flex;justify-content:space-between;align-items:center">'
                      + '<div class="nc-notif-ref">' + _.escape(item.name || '') + ' · Action corrective</div>'
                      + '<span class="badge red">FAC</span>'
                      + '</div>'
                      + '<div class="nc-notif-info">' + _.escape(item.department || '') + ' · ' + _.escape(item.date || '') + '</div>'
                      + '<div class="nc-notif-actions"><div class="btn-sm btn-open" data-model="nc_management.corrective_action" data-id="' + item.id + '">Ouvrir FAC</div></div>'
                      + '</div></div>';
            });

            // Plans SMI
            plans.forEach(function(item){
                html += '<div class="nc-notif">'
                      + '<div class="nc-avatar avatar-purple">' + _.escape(item.initials || 'PL') + '</div>'
                      + '<div class="nc-notif-body">'
                      + '<div style="display:flex;justify-content:space-between;align-items:center">'
                      + '<div class="nc-notif-ref">' + _.escape(item.name || '') + ' · ' + _.escape(item.type || '') + '</div>'
                      + '<span class="badge purple">Plan</span>'
                      + '</div>'
                      + '<div class="nc-notif-info">' + _.escape(item.department || '') + ' · ' + _.escape(item.date || '') + '</div>'
                      + '<div class="nc-notif-actions"><div class="btn-sm btn-open" data-model="nc_management.plan_action_smi" data-id="' + item.id + '">Ouvrir Plan</div></div>'
                      + '</div></div>';
            });

            if(!html) html = '<div class="nc-empty">Aucun document reçu.</div>';
            this.$('.received-list').html(html);
        },

        _formatDateKey: function(key){
            var p = key.split('-');
            if(p.length !== 3) return key;
            return 'Documents reçus le ' + p[2] + '/' + p[1] + '/' + p[0];
        },

        _renderDirectionPie: function(direction, kind){
            var stats = this.stats.direction_stats || [];
            if(!stats.length) return;
            var selected = stats[0];
            if(direction){
                stats.forEach(function(item){
                    if(item.name === direction) selected = item;
                });
            }
            kind = kind || 'fnc';
            var types = (kind === 'fac' ? selected.fac_types : selected.fnc_types) || {};
            this._renderPie(types, (kind === 'fac' ? 'FAC' : 'FNC') + ' · ' + selected.name);
        },

        _draw3DBars: function(canvasId, labels, datasets, opts){
            var canvas = this.$('#'+canvasId)[0];
            if(!canvas) return;
            var dpr = window.devicePixelRatio || 1;
            var rect = canvas.getBoundingClientRect();
            if(!rect.width) return;
            canvas.width  = rect.width  * dpr;
            canvas.height = rect.height * dpr;
            var ctx = canvas.getContext('2d');
            ctx.scale(dpr, dpr);
            var W = rect.width, H = rect.height;
            var pL=opts.padL||30, pR=opts.padR||10, pT=opts.padT||16, pB=opts.padB||22;
            var cW=W-pL-pR, cH=H-pT-pB;
            var dep=opts.depth||7;
            var nG=labels.length, nS=datasets.length;
            var gGap=opts.groupGap||0.3;
            var gW=cW/nG, bW=(gW*(1-gGap))/nS;
            var allVals=datasets.reduce(function(a,d){return a.concat(d.values||[]);},[]);
            var maxV=Math.max.apply(null,allVals)||1;

            ctx.strokeStyle='#e2e8f0'; ctx.lineWidth=.8;
            for(var i=0;i<=4;i++){
                var gy=pT+cH-(i/4)*cH;
                ctx.beginPath(); ctx.moveTo(pL,gy); ctx.lineTo(pL+cW,gy); ctx.stroke();
                ctx.fillStyle='#94a3b8'; ctx.font='9px Segoe UI'; ctx.textAlign='right';
                ctx.fillText(Math.round((i/4)*maxV), pL-3, gy+3);
            }

            datasets.forEach(function(ds,si){
                (ds.values||[]).forEach(function(val,gi){
                    var bh=(val/maxV)*cH;
                    var x=pL+gi*gW+(gW*gGap/2)+si*bW;
                    var y=pT+cH-bh;
                    var grad=ctx.createLinearGradient(x,y,x+bW,y);
                    grad.addColorStop(0,ds.colorLight); grad.addColorStop(1,ds.colorDark);
                    ctx.fillStyle=grad; ctx.fillRect(x,y,bW,bh);
                    ctx.fillStyle=ds.colorTop;
                    ctx.beginPath(); ctx.moveTo(x,y); ctx.lineTo(x+dep,y-dep);
                    ctx.lineTo(x+bW+dep,y-dep); ctx.lineTo(x+bW,y); ctx.closePath(); ctx.fill();
                    ctx.fillStyle=ds.colorSide;
                    ctx.beginPath(); ctx.moveTo(x+bW,y); ctx.lineTo(x+bW+dep,y-dep);
                    ctx.lineTo(x+bW+dep,y-dep+bh); ctx.lineTo(x+bW,y+bh); ctx.closePath(); ctx.fill();
                    ctx.fillStyle='#374151'; ctx.font='bold 9px Segoe UI'; ctx.textAlign='center';
                    if(val>0) ctx.fillText(val, x+bW/2, y-dep-2);
                });
            });

            ctx.fillStyle='#64748b'; ctx.font='9px Segoe UI'; ctx.textAlign='center';
            labels.forEach(function(lbl,gi){
                ctx.fillText(lbl, pL+gi*gW+gW/2, pT+cH+13);
            });
        },

        _drawEvoChart: function(){
            var s = this.stats || {};
            this._draw3DBars('evoChart',
                s.monthly_labels || ['Déc','Jan','Fév','Mar','Avr','Mai'],
                [
                    {values:s.monthly_fnc||[0,0,0,0,0,0], colorLight:'#7AAFEE',colorDark:'#3A72B8',colorTop:'#A8CCEF',colorSide:'#2A5A9A'},
                    {values:s.monthly_fac||[0,0,0,0,0,0], colorLight:'#E88080',colorDark:'#B03030',colorTop:'#F0A0A0',colorSide:'#8C2020'}
                ],
                {padL:28,padR:16,padT:16,padB:20,depth:7,groupGap:0.28}
            );
        },

        _drawGlobalChart: function(){
            var s = this.stats || {};
            this._draw3DBars('globalChart',
                s.monthly_labels || ['Déc','Jan','Fév','Mar','Avr','Mai'],
                [
                    {values:s.monthly_fnc_global||s.monthly_fnc||[0,0,0,0,0,0], colorLight:'#7AAFEE',colorDark:'#3A72B8',colorTop:'#A8CCEF',colorSide:'#2A5A9A'},
                    {values:s.monthly_fac_global||s.monthly_fac||[0,0,0,0,0,0], colorLight:'#E88080',colorDark:'#B03030',colorTop:'#F0A0A0',colorSide:'#8C2020'}
                ],
                {padL:28,padR:16,padT:16,padB:20,depth:7,groupGap:0.28}
            );
        },
    });

    core.action_registry.add('nc_dashboard', NcDashboard);
    return NcDashboard;
});
