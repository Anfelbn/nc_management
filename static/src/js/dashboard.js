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
                global_fnc_total: 0,
                global_fac_total: 0,
                global_fnc_types: {},
                global_fac_types: {},
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
                fac_validated: 0,
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
                plan_total: 0,
                plan_en_attente: 0,
                plan_integres: 0,
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

            this.$el.on('click', '.btn-reply', function(){
                var model = $(this).data('model');
                var id    = parseInt($(this).data('id'), 10);
                self.do_action({
                    type:      'ir.actions.act_window',
                    name:      'Répondre à la fiche',
                    res_model: 'nc_management.reply_wizard',
                    views:     [[false, 'form']],
                    target:    'new',
                    context: {
                        default_record_model: model,
                        default_record_id:    id,
                    },
                });
            });

            this.$el.on('click', '.btn-list', function(){
                var model   = $(this).data('model') || 'nc_management.nonconformity';
                var domain  = JSON.parse($(this).attr('data-domain') || '[]');
                var context = JSON.parse($(this).attr('data-context') || '{}');
                self.do_action({
                    type:      'ir.actions.act_window',
                    res_model: model,
                    domain:    domain,
                    views:     [[false, 'list'], [false, 'form']],
                    target:    'current',
                    context:   context,
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

            this.$el.on('click', '.avatar-clickable', function(e){
                e.stopPropagation();
                var model = $(this).data('model');
                var id    = parseInt($(this).data('id'), 10);
                self._onAvatarClick(model, id);
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
            var TYPE_DEFS = [
                {key: 'nc_produit',        label: 'NC Produit',          color: '#2196F3'},
                {key: 'reclamation',       label: 'Réclamation',         color: '#EF4444'},
                {key: 'sst',               label: 'SST',                 color: '#10B981'},
                {key: 'environnement',     label: 'Environnement',       color: '#FF9800'},
                {key: 'audit_interne',     label: 'Audit Interne',       color: '#7C3AED'},
                {key: 'audit_externe',     label: 'Audit Externe',       color: '#9B59B6'},
                {key: 'achat',             label: 'Achat',               color: '#F59E0B'},
                {key: 'reception',         label: 'Réception',           color: '#06B6D4'},
                {key: 'dysfonctionnement', label: 'Dysfonctionnement',   color: '#EC4899'},
                {key: 'travaux',           label: 'Travaux',             color: '#84CC16'},
                {key: 'autres',            label: 'Autres',              color: '#64748B'},
            ];

            var active = TYPE_DEFS.filter(function(t){ return (types[t.key] || 0) > 0; });

            var cum = 0;
            var segments = active.map(function(t){
                var pct = types[t.key] || 0;
                var seg = t.color + ' ' + cum + '% ' + (cum + pct) + '%';
                cum += pct;
                return seg;
            });

            var bg = active.length
                ? 'conic-gradient(' + segments.join(',') + ')'
                : '#e2e8f0';
            this.$('.dir-pie').css('background', bg);
            this.$('.dir-pie-title').text(title);

            var dot = 'display:inline-block;width:8px;height:8px;border-radius:50%;background:';
            var legendHtml = active.map(function(t){
                return '<div><span style="' + dot + t.color + '"></span> ' + t.label + ' ' + (types[t.key] || 0) + '%</div>';
            }).join('');
            this.$('.dir-pie-legend').html(
                legendHtml || '<div style="color:#94a3b8;font-size:10px">Aucun type renseigné</div>'
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
                      + '<div class="nc-avatar avatar-blue avatar-clickable" data-model="nc_management.nonconformity" data-id="' + fnc.id + '" title="' + _.escape(fnc.sender_name || 'Émetteur') + '">' + _.escape(fnc.sender_initials || '?') + '</div>'
                      + '<div style="flex:1;min-width:0">'
                      + '<div style="display:flex;justify-content:space-between;align-items:center">'
                      + '<div class="nc-notif-ref">' + _.escape(fnc.name || '') + ' · ' + _.escape(fnc.type || '') + '</div>'
                      + '<span class="badge blue">FNC</span>'
                      + '</div>'
                      + '<div class="nc-notif-actions">'
                      + '<div class="btn-sm primary btn-open" data-model="nc_management.nonconformity" data-id="' + fnc.id + '">Ouvrir FNC</div>'
                      + '<div class="btn-sm btn-reply" data-model="nc_management.nonconformity" data-id="' + fnc.id + '" data-partner-id="">Répondre</div>'
                      + '</div>'
                      + '</div></div>';
                // FAC liées (indentées avec barre rouge)
                g.facs.forEach(function(fac){
                    html += '<div style="display:flex;gap:8px;align-items:flex-start;padding:8px 10px 8px 16px;border-top:1px solid #f1f5f9;background:white">'
                          + '<div style="width:2px;background:#EF4444;border-radius:2px;align-self:stretch;flex-shrink:0;margin-top:4px"></div>'
                          + '<div class="nc-avatar avatar-red avatar-clickable" style="width:28px;height:28px;font-size:10px" data-model="nc_management.corrective_action" data-id="' + fac.id + '" title="' + _.escape(fac.sender_name || 'Émetteur') + '">' + _.escape(fac.sender_initials || '?') + '</div>'
                          + '<div style="flex:1;min-width:0">'
                          + '<div style="display:flex;justify-content:space-between;align-items:center">'
                          + '<div style="font-size:11px;font-weight:600;color:#1e293b">' + _.escape(fac.name || '') + ' · Action corrective</div>'
                          + '<span class="badge red">FAC</span>'
                          + '</div>'
                          + '<div class="nc-notif-actions">'
                          + '<div class="btn-sm btn-open" data-model="nc_management.corrective_action" data-id="' + fac.id + '">Ouvrir FAC</div>'
                          + '<div class="btn-sm btn-reply" data-model="nc_management.corrective_action" data-id="' + fac.id + '" data-partner-id="">Répondre</div>'
                          + '</div>'
                          + '</div></div>';
                });
                html += '</div>';
            });


            // Plans SMI
            plans.forEach(function(item){
                var stateMap = {
                    soumis:    {label: 'En attente',  color: '#7c3aed', bg: '#f5f3ff'},
                    integre:   {label: 'Intégré',     color: '#059669', bg: '#f0fdf4'},
                    cloture:   {label: 'Clôturé',     color: '#64748b', bg: '#f1f5f9'},
                    brouillon: {label: 'Brouillon',   color: '#94a3b8', bg: '#f8fafc'},
                };
                var st = stateMap[item.submission_state] || null;
                var stateBadge = st
                    ? '<span class="badge" style="background:' + st.bg + ';color:' + st.color + ';border:1px solid ' + st.color + '33">' + st.label + '</span>'
                    : '';

                var echeanceLine = item.date_prevue
                    ? '<div class="nc-notif-info" style="color:#94a3b8">Échéance : ' + _.escape(item.date_prevue) + '</div>'
                    : '';

                html += '<div style="border:1px solid #e9d5ff;border-radius:10px;margin-bottom:8px;overflow:hidden;background:#faf5ff">'
                      + '<div style="display:flex;gap:10px;align-items:flex-start;padding:10px;">'
                      + '<div class="nc-avatar avatar-purple avatar-clickable" data-model="nc_management.plan_action_smi" data-id="' + item.id + '" title="' + _.escape(item.sender_name || 'Émetteur') + '">' + _.escape(item.sender_initials || '?') + '</div>'
                      + '<div style="flex:1;min-width:0">'
                      + '<div style="display:flex;justify-content:space-between;align-items:center;gap:6px;flex-wrap:wrap">'
                      + '<div class="nc-notif-ref" style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + _.escape(item.name || '') + '</div>'
                      + '<div style="display:flex;gap:4px;flex-shrink:0"><span class="badge purple">PLAN</span>' + stateBadge + '</div>'
                      + '</div>'
                      + '<div class="nc-notif-info" style="margin-top:3px;color:#6d28d9">' + _.escape(item.type || 'Plan action') + '</div>'
                      + echeanceLine
                      + '<div class="nc-notif-actions">'
                      + '<div class="btn-sm primary btn-open" style="background:#7c3aed;border-color:#7c3aed" data-model="nc_management.plan_action_smi" data-id="' + item.id + '">Ouvrir Plan</div>'
                      + '<div class="btn-sm btn-reply" data-model="nc_management.plan_action_smi" data-id="' + item.id + '" data-partner-id="">Répondre</div>'
                      + '</div>'
                      + '</div></div></div>';
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
            kind = kind || 'fnc';
            if(!direction){
                var globalTypes = kind === 'fac'
                    ? (this.stats.global_fac_types || {})
                    : (this.stats.global_fnc_types || {});
                this.$('.dir-pie-scope').text(
                    'Types ' + (kind === 'fac' ? 'FAC' : 'FNC') + ' — Vue globale');
                this._renderPie(globalTypes, 'Toutes directions');
                return;
            }
            var stats = this.stats.direction_stats || [];
            if(!stats.length) return;
            var selected = null;
            stats.forEach(function(item){
                if(item.name === direction) selected = item;
            });
            if(!selected) return;
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

        _onAvatarClick: function(model, id) {
            var self = this;
            this._rpc({
                model:  'nc_management.dashboard',
                method: 'get_sender_info',
                args:   [model, id],
            }).then(function(data) {
                self._showSenderModal(data);
            });
        },

        _showSenderModal: function(data) {
            $('#nc-sender-modal').remove();
            $(document).off('keydown.nsm');

            var nom    = data.nom    || '';
            var prenom = data.prenom || '';
            var fullName = (nom + ' ' + prenom).trim() || 'Inconnu';
            var initials = fullName.split(' ').slice(0, 2).map(function(w) {
                return (w[0] || '').toUpperCase();
            }).join('') || '?';

            function row(label, val) {
                if (!val) return '';
                return '<div class="nsm-row">'
                     + '<span class="nsm-label">' + label + '</span>'
                     + '<span class="nsm-val">' + _.escape(val) + '</span>'
                     + '</div>';
            }

            // Construire "direction, service/département"
            var orgParts = [];
            if (data.direction)  orgParts.push(_.escape(data.direction));
            var sdPart = [data.service, data.department].filter(Boolean).map(_.escape).join('/');
            if (sdPart) orgParts.push(sdPart);
            var orgLine = orgParts.join(', ');

            var rows = row('Nom',        nom)
                     + row('Prénom',     prenom)
                     + (orgLine ? '<div class="nsm-row"><span class="nsm-label">Org.</span><span class="nsm-val">' + orgLine + '</span></div>' : '')
                     + row('Envoyé le',  data.send_datetime);

            var msgHtml = '';
            if (data.message) {
                msgHtml = '<div class="nsm-msg-box">'
                        + '<div class="nsm-msg-label">Message envoyé</div>'
                        + '<div class="nsm-msg-body">' + _.escape(data.message) + '</div>'
                        + '</div>';
            }

            if (!nom && !prenom && !orgLine && !data.send_datetime && !data.message) {
                rows = '<div class="nsm-row"><span class="nsm-val" style="color:#94a3b8;font-style:italic">Aucune information disponible.</span></div>';
            }

            var modal = $(
                '<div id="nc-sender-modal" class="nsm-overlay">'
              + '<div class="nsm-card">'
              + '<button class="nsm-close" title="Fermer">&times;</button>'
              + '<div class="nsm-avatar-lg">' + _.escape(initials) + '</div>'
              + '<div class="nsm-name">' + _.escape(fullName) + '</div>'
              + '<div class="nsm-rows">' + rows + '</div>'
              + msgHtml
              + '</div>'
              + '</div>'
            );

            $('body').append(modal);
            modal[0].offsetHeight;
            modal.addClass('nsm-visible');

            function closeModal() {
                modal.removeClass('nsm-visible');
                $(document).off('keydown.nsm');
                setTimeout(function() { modal.remove(); }, 260);
            }

            modal.on('click', function(e) {
                if ($(e.target).is('#nc-sender-modal') || $(e.target).hasClass('nsm-close')) {
                    closeModal();
                }
            });

            $(document).on('keydown.nsm', function(e) {
                if (e.key === 'Escape') { closeModal(); }
            });
        },
    });

    core.action_registry.add('nc_dashboard', NcDashboard);
    return NcDashboard;
});
