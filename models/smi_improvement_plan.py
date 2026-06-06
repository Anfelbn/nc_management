# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class SmiImprovementPlan(models.Model):
    """Niveau 2 — Plan d'Action d'Amélioration SMI (par direction).
    Regroupe les plans d'action (niveau 1) d'une direction
    avant soumission à la Responsable Qualité."""

    _name = 'nc_management.smi_improvement_plan'
    _description = "Plan d'Action d'Amélioration SMI"
    _order = 'name asc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ── En-tête ───────────────────────────────────────────────────
    name = fields.Char(
        string='Référence', required=True, copy=False,
        readonly=True, default='New')

    direction_id = fields.Many2one(
        'hr.department', string='Direction',
        domain=[('scaek_level', '=', 'direction')],
        context={'no_create': True, 'no_create_edit': True},
        track_visibility='onchange')

    department_id = fields.Many2one(
        'hr.department', string='Département',
        domain=[('scaek_level', '=', 'departement')],
        context={'no_create': True, 'no_create_edit': True})

    service_id = fields.Many2one(
        'hr.department', string='Service',
        domain=[('scaek_level', '=', 'service')],
        context={'no_create': True, 'no_create_edit': True})

    description = fields.Text(
        string='Objet / Périmètre du plan',
        track_visibility='onchange')

    # ── Plans d'action niveau 1 ───────────────────────────────────
    plan_ids = fields.One2many(
        'nc_management.plan_action_smi', 'improvement_plan_id',
        string="Plans d'Action")

    # ── Statistiques calculées ────────────────────────────────────
    nb_plans = fields.Integer(
        string='Nb plans', compute='_compute_stats', store=True)
    nb_en_cours = fields.Integer(
        string='En cours', compute='_compute_stats', store=True)
    nb_realises = fields.Integer(
        string='Réalisés', compute='_compute_stats', store=True)
    nb_non_realises = fields.Integer(
        string='Non réalisés', compute='_compute_stats', store=True)
    nb_clotures = fields.Integer(
        string='Clôturés', compute='_compute_stats', store=True)
    taux_avancement = fields.Integer(
        string='Avancement global (%)', compute='_compute_stats', store=True)
    taux_realisation = fields.Integer(
        string='Taux de réalisation (%)', compute='_compute_stats', store=True)
    taux_efficacite = fields.Integer(
        string="Taux d'efficacité (%)", compute='_compute_stats', store=True)

    # ── Date de création (automatique, non modifiable) ───────────
    date_ouverture = fields.Date(
        string='Date de création')

    # ── Consultation historique ───────────────────────────────────
    date_consultation = fields.Date(
        string="Voir l'état à la date")

    historique_html = fields.Html(
        string='État historique',
        compute='_compute_historique_html',
        sanitize=False,
        store=False)

    # ── Cycle de vie ──────────────────────────────────────────────
    state = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('soumis',    'Soumis à la Qualité'),
    ], string='État', default='brouillon',
       track_visibility='onchange')

    date_soumission = fields.Datetime(
        string='Date de soumission', readonly=True)
    submitted_by_id = fields.Many2one(
        'res.users', string='Soumis par', readonly=True)

    # ── Lien vers le Plan Global (niveau 3) ──────────────────────
    global_plan_id = fields.Many2one(
        'nc_management.smi_global_plan',
        string='Plan Global',
        readonly=True,
        ondelete='set null',
        index=True)

    # ── Valeurs par défaut : préremplir la direction de l'employé connecté
    @api.model
    def default_get(self, fields_list):
        defaults = super(SmiImprovementPlan, self).default_get(fields_list)
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        if employee and employee.department_id:
            dept = employee.department_id
            while dept:
                if dept.scaek_level == 'direction' and 'direction_id' in fields_list:
                    defaults['direction_id'] = dept.id
                    break
                dept = dept.parent_id
        return defaults

    @api.depends(
        'plan_ids.state', 'plan_ids.avancement', 'plan_ids.efficacite')
    def _compute_stats(self):
        for rec in self:
            plans = rec.plan_ids
            nb = len(plans)
            rec.nb_plans = nb
            rec.nb_realises = sum(
                1 for p in plans if p.avancement >= 100)
            rec.nb_en_cours = sum(
                1 for p in plans if 0 < p.avancement < 100)
            rec.nb_non_realises = sum(
                1 for p in plans if p.avancement == 0)
            rec.nb_clotures = sum(
                1 for p in plans if p.state in ('cloture', 'done'))
            rec.taux_avancement = int(
                sum(p.avancement for p in plans) / nb) if nb else 0
            rec.taux_realisation = int(
                rec.nb_realises / nb * 100) if nb else 0
            efficaces = sum(1 for p in plans if p.efficacite == 'oui')
            rec.taux_efficacite = int(efficaces / nb * 100) if nb else 0

    @api.multi
    def unlink(self):
        is_rmqse = self.env.user.has_group('nc_management.group_responsable_qualite')
        for rec in self:
            if not is_rmqse:
                if rec.create_uid.id != self.env.uid:
                    raise UserError("Vous ne pouvez supprimer que vos propres plans.")
                if rec.state != 'brouillon':
                    raise UserError("Impossible de supprimer un plan déjà soumis.")
        return super(SmiImprovementPlan, self).unlink()

    @api.multi
    def copy(self, default=None):
        raise UserError("La duplication d'un plan d'amélioration n'est pas autorisée.")

    @api.multi
    def action_print_plan(self):
        self.ensure_one()
        return self.env.ref(
            'nc_management.action_report_smi_improvement_plan'
        ).report_action(self)

    @api.multi
    def action_supprimer_plan(self):
        self.ensure_one()
        if self.state != 'brouillon':
            raise UserError("Impossible de supprimer un plan déjà soumis.")
        self.unlink()
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'nc_management.paa_user_improvement_plan') or 'New'
        return super(SmiImprovementPlan, self).create(vals)

    @api.depends('date_consultation', 'plan_ids')
    def _compute_historique_html(self):
        from datetime import datetime as _dt

        th  = ('padding:8px 12px;text-align:left;white-space:nowrap;'
               'border-bottom:2px solid #dee2e6;color:white;')
        td  = 'padding:7px 12px;border-bottom:1px solid #eee;'
        tdc = td + 'text-align:center;'
        EFF_LABELS = {
            'oui': 'OUI', 'non': 'NON',
            False: '-', None: '-', '': '-',
        }

        for rec in self:
            if not rec.date_consultation:
                rec.historique_html = ''
                continue

            date_limit = fields.Datetime.to_string(
                _dt.combine(
                    fields.Date.from_string(str(rec.date_consultation)),
                    _dt.max.time()))

            def _val(res_id, field_name, default):
                tracking = self.env['mail.tracking.value'].sudo().search([
                    ('mail_message_id.res_id',  '=', res_id),
                    ('mail_message_id.model',   '=', 'nc_management.plan_action_smi'),
                    ('field',                   '=', field_name),
                    ('mail_message_id.date',    '<=', date_limit),
                ], order='id desc', limit=1)
                if not tracking:
                    return default
                if field_name == 'avancement':
                    return tracking.new_value_integer
                return tracking.new_value_char or default

            plans = rec.env['nc_management.plan_action_smi'].browse()
            for p in rec.plan_ids:
                if p.create_date and p.create_date <= date_limit:
                    plans |= p

            if not plans:
                rec.historique_html = (
                    '<p style="color:#888;padding:16px;">'
                    "Aucun plan n'était intégré à cette date.</p>")
                continue

            plan_model = self.env['nc_management.plan_action_smi']
            nature_sel = plan_model._fields['nature'].selection
            nature_labels = dict(
                nature_sel if not callable(nature_sel)
                else nature_sel(plan_model))

            rows = ''
            for i, plan in enumerate(plans):
                hist_av  = _val(plan.id, 'avancement', plan.avancement)
                hist_eff = _val(plan.id, 'efficacite', plan.efficacite or '')
                av_int = hist_av if hist_av is not None else 0
                if av_int >= 100:
                    state_lbl, sc = 'Réalisé',     '#1fa255'
                elif av_int > 0:
                    state_lbl, sc = 'En cours',    '#cc8800'
                else:
                    state_lbl, sc = 'Non réalisé', '#d44535'
                eff_lbl = EFF_LABELS.get(hist_eff, '-')
                bg = '#fff' if i % 2 == 0 else '#f8f9fa'
                rows += (
                    '<tr style="background:{bg};">'
                    '<td style="{td}">{nature}</td>'
                    '<td style="{td}"><b>{ref}</b></td>'
                    '<td style="{td}">{responsable}</td>'
                    '<td style="{tdc}">{av}%</td>'
                    '<td style="{tdc}"><span style="color:{sc};font-weight:bold;">'
                    '{state}</span></td>'
                    '<td style="{tdc}">{eff}</td>'
                    '</tr>'
                ).format(
                    bg=bg, td=td, tdc=tdc,
                    nature=nature_labels.get(plan.nature, plan.nature or '-'),
                    ref=plan.name,
                    responsable=plan.responsable_id.name if plan.responsable_id else '-',
                    av=av_int,
                    state=state_lbl, sc=sc, eff=eff_lbl,
                )

            consul_str = fields.Date.from_string(
                str(rec.date_consultation)).strftime('%d/%m/%Y')
            thead = (
                '<thead><tr style="background:#1a2e5a;">'
                '<th style="{th}">Nature</th>'
                '<th style="{th}">Référence</th>'
                '<th style="{th}">Responsable</th>'
                '<th style="{th}">Avancement %</th>'
                '<th style="{th}">État</th>'
                '<th style="{th}">Efficacité</th>'
                '</tr></thead>'
            ).format(th=th)

            rec.historique_html = (
                '<div style="font-family:Arial,sans-serif;">'
                '<div style="background:#fff3cd;border:1px solid #ffc107;'
                'border-radius:4px;padding:12px 16px;margin-bottom:12px;">'
                '<b>&#9888; Vue historique au {date}</b> — '
                "Voici l'état du plan à cette date.</div>"
                '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
                '{thead}<tbody>{rows}</tbody></table>'
                '</div>'
            ).format(date=consul_str, thead=thead, rows=rows)

    @api.multi
    def action_open_consulter_version_wizard(self):
        self.ensure_one()
        wizard = self.env[
            'nc_management.consulter_version_improvement_wizard'].create({
                'improvement_plan_id': self.id,
            })
        view_id = self.env.ref(
            'nc_management.view_consulter_version_improvement_wizard_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': "Consulter une version passée",
            'res_model': 'nc_management.consulter_version_improvement_wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'target': 'new',
        }

    @api.multi
    def action_open_new_plan_form(self):
        self.ensure_one()
        view_id = self.env.ref('nc_management.view_plan_smi_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': "Nouveau plan d'action",
            'res_model': 'nc_management.plan_action_smi',
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'target': 'new',
            'context': {
                'default_improvement_plan_id': self.id,
            },
        }

    @api.multi
    def action_retour_actuel(self):
        self.ensure_one()
        self.write({'date_consultation': False})
        inner_action = {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'views': [[False, 'form']],
            'target': 'current',
        }
        return {
            'type': 'ir.actions.client',
            'tag': 'nc_management.clear_and_navigate',
            'params': {'inner_action': inner_action},
        }

    @api.multi
    def action_consolider(self):
        """Ouvre le wizard de consolidation pour intégrer des plans individuels."""
        self.ensure_one()
        if self.state != 'brouillon':
            raise UserError(
                "Impossible de consolider un plan déjà soumis.")

        plans_dispo = self.env['nc_management.plan_action_smi'].search([
            ('create_uid',          '=', self.env.uid),
            ('improvement_plan_id', '=', False),
            ('is_global',           '=', False),
        ])
        wizard = self.env['nc_management.consolidate_improvement_wizard'].create({
            'improvement_plan_id': self.id,
        })
        for plan in plans_dispo:
            self.env['nc_management.consolidate_improvement_wizard.line'].create({
                'wizard_id': wizard.id,
                'plan_id':   plan.id,
            })
        return {
            'type':      'ir.actions.act_window',
            'name':      "Consolider des plans d'action",
            'res_model': 'nc_management.consolidate_improvement_wizard',
            'res_id':    wizard.id,
            'view_mode': 'form',
            'target':    'new',
        }

    @api.multi
    def action_soumettre(self):
        """Soumettre le plan à la Responsable Qualité."""
        self.ensure_one()
        if self.state != 'brouillon':
            raise UserError(
                "Ce plan a déjà été soumis à la Responsable Qualité.")
        if not self.plan_ids:
            raise UserError(
                "Ajoutez au moins un plan d'action avant de soumettre.")
        if not self.date_ouverture:
            raise UserError(
                "La Date de création est obligatoire avant d'envoyer.")
        if not self.direction_id:
            raise UserError(
                "La Direction est obligatoire avant de soumettre.")

        self.write({
            'state':           'soumis',
            'date_soumission': fields.Datetime.now(),
            'submitted_by_id': self.env.uid,
        })

        # Rattacher au plan global unique (créer si inexistant)
        global_plan = self.env['nc_management.smi_global_plan'].search(
            [], limit=1)
        if not global_plan:
            global_plan = self.env['nc_management.smi_global_plan'].sudo().create({
                'name': "Plan d'Action Global SMI",
            })
        self.write({'global_plan_id': global_plan.id})

        # Auto-consolider les plans dans le plan RMQSE (is_global=True) en cours
        rmqse_plan = self.env['nc_management.plan_action_smi'].sudo().search([
            ('is_global', '=', True),
            ('submission_state', '!=', 'cloture'),
        ], order='create_date desc', limit=1)
        if not rmqse_plan:
            rmqse_plan = self.env['nc_management.plan_action_smi'].sudo().create({
                'is_global': True,
                'submission_state': 'brouillon',
                'mois_reception': fields.Date.today(),
            })
        if self.plan_ids:
            self.plan_ids.with_context(_skip_date_maj=True).write({
                'global_plan_id': rmqse_plan.id,
                'submission_state': 'integre',
            })
            rmqse_plan.with_context(_skip_date_maj=True).write({
                'date_maj': fields.Datetime.now(),
            })

        # Notifier la Responsable Qualité par mail interne
        rmqse_group = self.env.ref(
            'nc_management.group_responsable_qualite',
            raise_if_not_found=False)
        partner_ids = []
        if rmqse_group:
            partner_ids = rmqse_group.users.mapped('partner_id').ids

        self.message_post(
            body=(
                "<p>Plan d'Action d'Amélioration <strong>%s</strong> soumis "
                "par <strong>%s</strong> — Direction : <strong>%s</strong>.</p>"
                "<p>%d plan(s) d'action inclus.</p>"
            ) % (
                self.name,
                self.env.user.name,
                self.direction_id.name if self.direction_id else '-',
                len(self.plan_ids),
            ),
            partner_ids=partner_ids,
            message_type='notification',
            subtype='mail.mt_comment',
        )

        # Tracer l'événement dans le chatter du plan global
        if global_plan:
            global_plan.message_post(
                body=(
                    "<p>Nouveau Plan d'Amélioration reçu : "
                    "<strong>%s</strong><br/>"
                    "Direction : <strong>%s</strong><br/>"
                    "Soumis par : <strong>%s</strong><br/>"
                    "Plans d'action : <strong>%d</strong></p>"
                ) % (
                    self.name,
                    self.direction_id.name if self.direction_id else '-',
                    self.env.user.name,
                    len(self.plan_ids),
                ),
                message_type='notification',
                subtype='mail.mt_comment',
            )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.smi_improvement_plan',
            'res_id': self.id,
            'views': [[False, 'form']],
            'target': 'current',
        }

    @api.model
    def action_open_my_plan(self):
        """Ouvre (ou crée) l'unique plan d'amélioration du NC utilisateur connecté."""
        plan = self.search([('create_uid', '=', self.env.uid)], limit=1)
        if not plan:
            plan = self.create({})
        inner_action = {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': plan.id,
            'views': [[False, 'form']],
            'view_mode': 'form',
            'target': 'current',
            'flags': {'initial_mode': 'edit'},
        }
        return {
            'type': 'ir.actions.client',
            'tag': 'nc_management.clear_and_navigate',
            'params': {'inner_action': inner_action},
        }

    @api.onchange('direction_id')
    def _onchange_direction_id(self):
        self.department_id = False
        self.service_id = False

    @api.onchange('department_id')
    def _onchange_department_id(self):
        self.service_id = False
