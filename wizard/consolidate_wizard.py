from odoo import models, fields, api
from odoo.exceptions import UserError


class ConsolidateWizardLine(models.TransientModel):
    _name = 'nc_management.consolidate_wizard.line'
    _description = 'Ligne de sélection — consolidation'

    wizard_id           = fields.Many2one('nc_management.consolidate_wizard', ondelete='cascade')
    improvement_plan_id = fields.Many2one('nc_management.smi_improvement_plan', string='Référence', readonly=True)
    selected            = fields.Boolean(string='Sélectionner', default=False)

    direction_id     = fields.Many2one(related='improvement_plan_id.direction_id',     string='Direction',             readonly=True)
    date_ouverture   = fields.Date(related='improvement_plan_id.date_ouverture',       string='Date création',         readonly=True)
    nb_plans         = fields.Integer(related='improvement_plan_id.nb_plans',          string='Nb Plans',               readonly=True)
    taux_avancement  = fields.Integer(related='improvement_plan_id.taux_avancement',   string='Avancement Global %',    readonly=True)
    taux_realisation = fields.Integer(related='improvement_plan_id.taux_realisation',  string='Taux de réalisation %',  readonly=True)
    taux_efficacite  = fields.Integer(related='improvement_plan_id.taux_efficacite',   string="Taux d'efficacité %",    readonly=True)
    state            = fields.Selection(related='improvement_plan_id.state',           string='État',                   readonly=True)


class ConsolidateWizard(models.TransientModel):
    _name = 'nc_management.consolidate_wizard'
    _description = 'Assistant de consolidation des plans'

    global_plan_id = fields.Many2one(
        'nc_management.plan_action_smi',
        string="Plan d'Amélioration",
        readonly=True,
        required=True,
        ondelete='cascade',
    )
    line_ids = fields.One2many(
        'nc_management.consolidate_wizard.line',
        'wizard_id',
        string='Plans disponibles',
    )

    @api.multi
    def action_consolidate(self):
        self.ensure_one()
        if not self.global_plan_id:
            raise UserError("Le Plan d'Amélioration n'est pas défini. Veuillez réessayer.")
        selected_paas = self.line_ids.filtered(lambda l: l.selected).mapped('improvement_plan_id')
        if not selected_paas:
            raise UserError("Aucun plan sélectionné. Cochez au moins un Plan Reçu à consolider.")
        selected_paas.mapped('plan_ids').with_context(_skip_date_maj=True).write({
            'global_plan_id': self.global_plan_id.id,
            'submission_state': 'integre',
        })
        self.global_plan_id.with_context(_skip_date_maj=True).write({
            'date_maj': fields.Datetime.now(),
        })
        return {
            'type': 'ir.actions.act_window',
            'name': "Plan d'Action d'Amélioration SMI",
            'res_model': 'nc_management.plan_action_smi',
            'res_id': self.global_plan_id.id,
            'view_mode': 'form',
            'view_id': self.env.ref('nc_management.view_plan_smi_form_global').id,
            'target': 'current',
            'context': {'default_is_global': True},
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
                'default_global_plan_id': self.global_plan_id.id,
            },
        }
