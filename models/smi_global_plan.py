# -*- coding: utf-8 -*-
from datetime import datetime as _dt
from odoo import models, fields, api


class SmiGlobalPlan(models.Model):
    """Niveau 3 — Plan d'Action Global SMI (unique, Responsable Qualité).
    Consolide en temps réel TOUS les plans d'amélioration soumis
    par toutes les directions. Ne se clôture jamais."""

    _name = 'nc_management.smi_global_plan'
    _description = "Plan d'Action Global SMI"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nom', required=True,
        default="Plan d'Action Global SMI",
        track_visibility='onchange')

    date_derniere_maj = fields.Datetime(
        string='Dernière mise à jour', readonly=True)

    # ── Plans d'amélioration soumis par les directions ───────────
    improvement_plan_ids = fields.One2many(
        'nc_management.smi_improvement_plan', 'global_plan_id',
        string="Plans d'Amélioration par direction",
        readonly=True)

    # ── Plans ajoutés directement par la RMQSE ───────────────────
    direct_plan_ids = fields.One2many(
        'nc_management.plan_action_smi', 'direct_global_plan_id',
        string="Plans RMQSE (directs)")

    # ── Navigation historique ────────────────────────────────────
    date_consultation = fields.Date(
        string='Voir l\'état à la date',
        help="Sélectionnez une date passée pour voir l'état du plan global "
             "à ce moment précis. Laissez vide pour l'état actuel.")

    vue_historique = fields.Boolean(
        string='Vue historique active',
        compute='_compute_vue_historique',
        store=False)

    historique_html = fields.Html(
        string='État historique',
        compute='_compute_historique_html',
        sanitize=False,
        store=False)

    # ── Statistiques globales ────────────────────────────────────
    nb_directions = fields.Integer(
        string='Directions', compute='_compute_global_stats')
    nb_plans_total = fields.Integer(
        string='Plans total', compute='_compute_global_stats')
    nb_en_cours = fields.Integer(
        string='En cours', compute='_compute_global_stats')
    nb_realises = fields.Integer(
        string='Réalisés', compute='_compute_global_stats')
    nb_clotures = fields.Integer(
        string='Clôturés (Efficaces)', compute='_compute_global_stats')
    taux_avancement = fields.Integer(
        string='Avancement global (%)', compute='_compute_global_stats')
    taux_efficacite = fields.Integer(
        string="Taux d'efficacité (%)", compute='_compute_global_stats')

    # ── Vue consolidée : tous les plans niveau 1 ─────────────────
    # Affichée dans la vue form via One2many calculé vers plan_action_smi
    # (filtre : plans liés aux improvement_plan_ids OU direct_plan_ids)

    def _get_all_plans(self):
        """Retourne tous les plans niveau 1 consolidés dans ce plan global."""
        self.ensure_one()
        direction_plans = self.improvement_plan_ids.mapped('plan_ids')
        direct_plans = self.direct_plan_ids
        return direction_plans | direct_plans

    @api.depends('date_consultation')
    def _compute_vue_historique(self):
        for rec in self:
            rec.vue_historique = bool(rec.date_consultation)

    @api.depends(
        'improvement_plan_ids.plan_ids.state',
        'improvement_plan_ids.plan_ids.avancement',
        'improvement_plan_ids.plan_ids.efficacite',
        'improvement_plan_ids.direction_id',
        'direct_plan_ids.state',
        'direct_plan_ids.avancement',
    )
    def _compute_global_stats(self):
        for rec in self:
            plans = rec._get_all_plans()
            nb = len(plans)
            rec.nb_plans_total = nb
            directions = set()
            for p in plans:
                if p.improvement_plan_id and p.improvement_plan_id.direction_id:
                    directions.add(p.improvement_plan_id.direction_id.id)
            rec.nb_directions = len(directions)
            rec.nb_en_cours = sum(
                1 for p in plans if p.state in ('en_cours', 'draft'))
            rec.nb_realises = sum(
                1 for p in plans if p.state == 'realise')
            rec.nb_clotures = sum(
                1 for p in plans if p.state in ('cloture', 'done'))
            rec.taux_avancement = (
                int(sum(p.avancement for p in plans) / nb)
                if nb else 0)
            efficaces = sum(1 for p in plans if p.efficacite == 'oui')
            rec.taux_efficacite = int(efficaces / nb * 100) if nb else 0

    @api.depends('date_consultation',
                 'improvement_plan_ids.plan_ids',
                 'direct_plan_ids')
    def _compute_historique_html(self):
        """Reconstitue l'état de chaque plan à la date de consultation
        en interrogeant mail.tracking.value."""

        th = 'padding:8px 12px;text-align:left;white-space:nowrap;' \
             'border-bottom:2px solid #dee2e6;'
        td = 'padding:7px 12px;border-bottom:1px solid #eee;'
        tdc = td + 'text-align:center;'

        STATE_LABELS = {
            'en_cours': 'En cours', 'realise': 'Réalisé',
            'cloture': 'Clôturé', 'draft': 'Brouillon', 'done': 'Réalisé',
        }
        EFF_LABELS = {'oui': 'OUI', 'non': 'NON', False: '-', None: '-'}

        for rec in self:
            if not rec.date_consultation:
                rec.historique_html = ''
                continue

            date_limit = fields.Datetime.to_string(
                _dt.combine(
                    fields.Date.from_string(str(rec.date_consultation)),
                    _dt.max.time()))

            plans = rec._get_all_plans()
            # Filtrer les plans créés avant ou à la date de consultation
            plans = plans.filtered(
                lambda p: p.create_date and p.create_date <= date_limit)

            if not plans:
                rec.historique_html = (
                    '<p style="color:#888;padding:16px;">'
                    'Aucun plan existait à cette date.</p>')
                continue

            def _get_val_at_date(model, res_id, field_name, default):
                """Retrouve la valeur d'un champ à la date de consultation."""
                tracking = self.env['mail.tracking.value'].sudo().search([
                    ('mail_message_id.res_id',  '=', res_id),
                    ('mail_message_id.model',   '=', model),
                    ('field', '=', field_name),
                    ('mail_message_id.date',    '<=', date_limit),
                ], order='mail_message_id.date desc', limit=1)
                if not tracking:
                    return default
                if field_name in ('avancement',):
                    return tracking.new_value_integer
                return tracking.new_value_char or default

            rows = ''
            for i, plan in enumerate(plans):
                model = 'nc_management.plan_action_smi'
                hist_state = _get_val_at_date(
                    model, plan.id, 'state', plan.state)
                hist_av = _get_val_at_date(
                    model, plan.id, 'avancement', plan.avancement)
                hist_eff = _get_val_at_date(
                    model, plan.id, 'efficacite', plan.efficacite)
                hist_action = _get_val_at_date(
                    model, plan.id, 'action', plan.action or '')

                state_lbl = STATE_LABELS.get(hist_state, hist_state or '-')
                eff_lbl = EFF_LABELS.get(hist_eff, '-')
                bg = '#fff' if i % 2 == 0 else '#f8f9fa'

                if hist_state in ('cloture', 'done'):
                    state_color = '#1fa255'
                elif hist_state == 'realise':
                    state_color = '#cc8800'
                else:
                    state_color = '#2575b8'

                direction_name = (
                    plan.improvement_plan_id.direction_id.name
                    if plan.improvement_plan_id and
                    plan.improvement_plan_id.direction_id
                    else '-')

                rows += (
                    '<tr style="background:{bg};">'
                    '<td style="{td}">{direction}</td>'
                    '<td style="{td}">{nature}</td>'
                    '<td style="{td}"><b>{ref}</b></td>'
                    '<td style="{td}">{desc}</td>'
                    '<td style="{td}">{action}</td>'
                    '<td style="{td}">{responsable}</td>'
                    '<td style="{tdc}">{av}%</td>'
                    '<td style="{tdc}">'
                    '<span style="color:{sc};font-weight:bold;">'
                    '{state}</span></td>'
                    '<td style="{tdc}">{eff}</td>'
                    '</tr>'
                ).format(
                    bg=bg, td=td, tdc=tdc,
                    direction=direction_name,
                    nature=dict(
                        plan._fields['nature'].selection
                    ).get(plan.nature, '-') if plan.nature else '-',
                    ref=plan.name,
                    desc=(plan.description or '')[:60] +
                         ('…' if plan.description and
                          len(plan.description) > 60 else ''),
                    action=(hist_action or '')[:60] +
                           ('…' if hist_action and
                            len(hist_action) > 60 else ''),
                    responsable=plan.responsable_id.name
                    if plan.responsable_id else '-',
                    av=hist_av if hist_av is not None else plan.avancement,
                    state=state_lbl,
                    sc=state_color,
                    eff=eff_lbl,
                )

            consul_str = fields.Date.from_string(
                str(rec.date_consultation)).strftime('%d/%m/%Y')
            thead = (
                '<thead><tr style="background:#2c3e50;color:white;">'
                '<th style="{th}">Direction</th>'
                '<th style="{th}">Nature</th>'
                '<th style="{th}">Référence</th>'
                '<th style="{th}">Description</th>'
                '<th style="{th}">Action</th>'
                '<th style="{th}">Responsable</th>'
                '<th style="{th}">Avancement</th>'
                '<th style="{th}">État</th>'
                '<th style="{th}">Efficacité</th>'
                '</tr></thead>'
            ).format(th=th)

            rec.historique_html = (
                '<div style="font-family:Arial,sans-serif;">'
                '<div style="background:#fff3cd;border:1px solid #ffc107;'
                'border-radius:4px;padding:12px 16px;margin-bottom:12px;">'
                '<b>&#9888; Vue historique au {date}</b> — '
                'Les valeurs ci-dessous reflètent l\'état du plan global '
                'à cette date. Ce n\'est pas l\'état actuel.</div>'
                '<table style="width:100%;border-collapse:collapse;'
                'font-size:13px;">{thead}<tbody>{rows}</tbody></table>'
                '</div>'
            ).format(date=consul_str, thead=thead, rows=rows)

    @api.multi
    def action_retour_actuel(self):
        """Effacer la date de consultation pour revenir à l'état en temps réel."""
        self.ensure_one()
        self.with_context(_skip_maj=True).write({'date_consultation': False})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.smi_global_plan',
            'res_id': self.id,
            'views': [[False, 'form']],
            'target': 'current',
        }

    @api.multi
    def write(self, vals):
        res = super(SmiGlobalPlan, self).write(vals)
        # Mettre à jour date_derniere_maj à chaque modification significative
        if 'date_derniere_maj' not in vals and not self.env.context.get('_skip_maj'):
            self.with_context(_skip_maj=True).write(
                {'date_derniere_maj': fields.Datetime.now()})
        return res
