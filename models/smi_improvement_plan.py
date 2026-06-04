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
    nb_clotures = fields.Integer(
        string='Clôturés', compute='_compute_stats', store=True)
    taux_avancement = fields.Integer(
        string='Avancement global (%)', compute='_compute_stats', store=True)
    taux_efficacite = fields.Integer(
        string="Taux d'efficacité (%)", compute='_compute_stats', store=True)

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
            rec.nb_en_cours = sum(
                1 for p in plans if p.state in ('en_cours', 'draft'))
            rec.nb_realises = sum(
                1 for p in plans if p.state == 'realise')
            rec.nb_clotures = sum(
                1 for p in plans if p.state in ('cloture', 'done'))
            rec.taux_avancement = int(
                sum(p.avancement for p in plans) / nb) if nb else 0
            efficaces = sum(1 for p in plans if p.efficacite == 'oui')
            rec.taux_efficacite = int(efficaces / nb * 100) if nb else 0

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'nc_management.smi_improvement_plan') or 'New'
        return super(SmiImprovementPlan, self).create(vals)

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
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': plan.id,
            'views': [[False, 'form']],
            'view_mode': 'form',
            'target': 'current',
            'flags': {'initial_mode': 'edit'},
        }

    @api.onchange('direction_id')
    def _onchange_direction_id(self):
        self.department_id = False
        self.service_id = False

    @api.onchange('department_id')
    def _onchange_department_id(self):
        self.service_id = False
