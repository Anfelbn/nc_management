# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class ConsolidateImprovementLine(models.TransientModel):
    _name = 'nc_management.consolidate_improvement_wizard.line'
    _description = "Ligne — Consolidation Plan d'Amélioration"

    wizard_id     = fields.Many2one(
        'nc_management.consolidate_improvement_wizard',
        ondelete='cascade')
    plan_id       = fields.Many2one(
        'nc_management.plan_action_smi',
        string='Référence', readonly=True)
    selected      = fields.Boolean(string='Sélectionner', default=False)

    # Champs affichés en lecture seule pour faciliter le choix
    nature        = fields.Selection(
        related='plan_id.nature',   string='Nature',        readonly=True)
    description   = fields.Text(
        related='plan_id.description', string='Description', readonly=True)
    responsable_id = fields.Many2one(
        related='plan_id.responsable_id', string='Responsable', readonly=True)
    date_prevue   = fields.Date(
        related='plan_id.date_prevue', string='Date prévue', readonly=True)
    avancement    = fields.Integer(
        related='plan_id.avancement', string='Avancement %', readonly=True)
    state         = fields.Selection(
        related='plan_id.state',    string='État',          readonly=True)


class ConsolidateImprovementWizard(models.TransientModel):
    """Wizard permettant à un NC Utilisateur d'intégrer ses plans d'action
    (niveau 1) dans son Plan d'Amélioration (niveau 2)."""

    _name = 'nc_management.consolidate_improvement_wizard'
    _description = "Consolider — Plan d'Action d'Amélioration"

    improvement_plan_id = fields.Many2one(
        'nc_management.smi_improvement_plan',
        string="Plan d'Amélioration",
        readonly=True,
        required=True,
        ondelete='cascade')

    line_ids = fields.One2many(
        'nc_management.consolidate_improvement_wizard.line',
        'wizard_id',
        string='Plans disponibles')

    @api.model
    def default_get(self, fields_list):
        res = super(ConsolidateImprovementWizard, self).default_get(fields_list)
        imp_plan_id = self.env.context.get('default_improvement_plan_id')
        if not imp_plan_id:
            return res

        # Plans créés par l'utilisateur courant sans Plan d'Amélioration parent
        plans_dispo = self.env['nc_management.plan_action_smi'].search([
            ('create_uid',         '=', self.env.uid),
            ('improvement_plan_id', '=', False),
            ('is_global',          '=', False),
        ])

        lines = []
        for plan in plans_dispo:
            lines.append((0, 0, {
                'plan_id':  plan.id,
                'selected': False,
            }))

        res['improvement_plan_id'] = imp_plan_id
        res['line_ids'] = lines
        return res

    @api.multi
    def action_consolidate(self):
        self.ensure_one()
        if not self.improvement_plan_id:
            raise UserError("Le Plan d'Amélioration n'est pas défini.")

        selected_plans = self.line_ids.filtered(
            lambda l: l.selected).mapped('plan_id')

        if not selected_plans:
            raise UserError(
                "Aucun plan sélectionné. "
                "Cochez au moins un plan à intégrer.")

        selected_plans.write({
            'improvement_plan_id': self.improvement_plan_id.id,
        })

        return {
            'type':      'ir.actions.act_window',
            'res_model': 'nc_management.smi_improvement_plan',
            'res_id':    self.improvement_plan_id.id,
            'view_mode': 'form',
            'target':    'current',
            'context':   {'form_view_initial_mode': 'edit'},
        }

    @api.multi
    def action_open_new_plan(self):
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
                'default_improvement_plan_id': self.improvement_plan_id.id,
            },
        }
