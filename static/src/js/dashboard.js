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
                fac_audit: 0,
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

            this.$('.nc-tab').on('click', function(){
                var idx = $(this).index();
                self.$('.nc-tab').removeClass('active');
                self.$('.nc-tab-panel').removeClass('active');
                $(this).addClass('active');
                self.$('.nc-tab-panel').eq(idx).addClass('active');
                if(idx === 0) setTimeout(function(){ self._drawEvoChart(); }, 80);
                if(idx === 1) setTimeout(function(){ self._renderDirectionPie(); }, 80);
                if(idx === 2) setTimeout(function(){ self._drawGlobalChart(); }, 80);
            });

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

            this.$el.on('click', '.dir-bar', function(){
                self.$('.dir-bar').removeClass('selected');
                $(this).addClass('selected');
                self._renderDirectionPie($(this).data('direction'), $(this).data('kind') || 'fnc');
            });

            this._initCalendar();
            this._renderReceivedDocs(this.stats.received_docs || [], '');
            this._renderDirectionPie();
            this.$('.pb').removeClass('active');
            this.$('.pb[data-period="' + (this.stats.period || '1m') + '"]').addClass('active');
            setTimeout(function(){ self._drawEvoChart(); }, 120);
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
            var self   = this;
            var now    = new Date();
            var year   = this.stats.calendar_year || now.getFullYear();
            var month  = (this.stats.calendar_month || (now.getMonth() + 1)) - 1;
            var FR_M   = ['Janvier','Février','Mars','Avril','Mai','Juin',
                          'Juillet','Août','Septembre','Octobre','Novembre','Décembre'];

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
                    if(ev.fnc) dots += '<div class="cdot" style="background:#2196F3"></div>';
                    if(ev.fac) dots += '<div class="cdot" style="background:#EF4444"></div>';
                    if(ev.plan) dots += '<div class="cdot" style="background:#7C3AED"></div>';
                    html += '<div class="'+cls+'" data-date="'+key+'">'+d+(dots?'<div class="cal-dot-row">'+dots+'</div>':'')+'</div>';
                }
                var total = startOff + daysInM;
                var next  = 1;
                while(total % 7 !== 0){ html += '<div class="cal-day other-month">'+next+'</div>'; total++; next++; }

                self.$('.cal-grid-body').html(html);
                self.$('.cal-month-label').text(FR_M[m]+' '+y);
                self.$('.cal-grid-body .cal-day:not(.other-month)').off('click').on('click', function(){
                    var key = $(this).data('date');
                    self.$('.cal-day').removeClass('selected');
                    $(this).addClass('selected');
                    self._renderReceivedDocs((self.stats.received_by_date || {})[key] || [], key);
                });
            }

            render(year, month);

            this.$('.cal-prev').off('click').on('click', function(){
                month--; if(month < 0){ month = 11; year--; } render(year, month);
            });
            this.$('.cal-next').off('click').on('click', function(){
                month++; if(month > 11){ month = 0; year++; } render(year, month);
            });
        },

        _renderReceivedDocs: function(docs, key){
            var self = this;
            var label = key ? this._formatDateKey(key) : 'Derniers documents de la période';
            var html = '';
            this.$('.received-sub').text(label);

            if(!docs.length){
                html = '<div class="nc-empty">Aucun document reçu pour cette date.</div>';
                this.$('.received-list').html(html);
                return;
            }

            docs.forEach(function(item){
                var badge = item.badge || 'blue';
                html += '<div class="nc-notif">' +
                    '<div class="nc-avatar avatar-' + badge + '">' + _.escape(item.initials || 'XX') + '</div>' +
                    '<div class="nc-notif-body">' +
                    '<div style="display:flex;justify-content:space-between;align-items:center">' +
                    '<div class="nc-notif-ref">' + _.escape(item.name || '') + ' · ' + _.escape(item.type || '') + '</div>' +
                    '<span class="badge ' + badge + '">' + _.escape(item.kind || '') + '</span>' +
                    '</div>' +
                    '<div class="nc-notif-info">' + _.escape(item.department || '') + ' · ' +
                    _.escape(item.responsible || '') + ' · ' + _.escape(item.date || '') + '</div>' +
                    '<div class="nc-notif-actions">' +
                    '<div class="btn-sm primary btn-open" data-model="' + _.escape(item.model || '') +
                    '" data-id="' + _.escape(String(item.id || '')) + '">Ouvrir la fiche</div>' +
                    '</div></div></div>';
            });
            self.$('.received-list').html(html);
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
            var nc = types.nc_produit || 0;
            var sst = types.sst || 0;
            var env = types.environnement || 0;
            var rec = types.reclamation || 0;
            var audit = types.audit || 0;
            var autres = types.autres || 0;
            var p1 = nc;
            var p2 = p1 + sst;
            var p3 = p2 + env;
            var p4 = p3 + rec;
            var p5 = p4 + audit;
            var bg = 'conic-gradient(#2196F3 0% '+p1+'%,#10B981 '+p1+'% '+p2+'%,#FF9800 '+p2+'% '+p3+'%,#EF4444 '+p3+'% '+p4+'%,#7C3AED '+p4+'% '+p5+'%,#64748B '+p5+'% 100%)';
            this.$('.dir-pie').css('background', bg);
            this.$('.dir-pie-title').text((kind === 'fac' ? 'FAC' : 'FNC') + ' · ' + selected.name);
            this.$('.dir-pie-legend').html(
                '<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#2196F3"></span> NC Produit '+nc+'%</div>' +
                '<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#10B981"></span> SST '+sst+'%</div>' +
                '<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#FF9800"></span> Env. '+env+'%</div>' +
                '<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#EF4444"></span> Réclam. '+rec+'%</div>' +
                '<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#7C3AED"></span> Audit '+audit+'%</div>' +
                '<div><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#64748B"></span> Autres '+autres+'%</div>'
            );
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
