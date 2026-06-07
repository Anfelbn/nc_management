from odoo import models, fields, api
from odoo.exceptions import UserError


class ConsolidateWizardLine(models.TransientModel):
    _name = 'nc_management.consolidate_wizard.line'
    _description = 'Ligne de sélection — consolidation'

    wizard_id     = fields.Many2one('nc_management.consolidate_wizard', ondelete='cascade')
    plan_id       = fields.Many2one('nc_management.plan_action_smi', string='Référence', readonly=True)
    selected      = fields.Boolean(string='Sélectionner', default=False)

    direction_id   = fields.Many2one(related='plan_id.direction_id',    string='Direction',    readonly=True)
    department_id  = fields.Many2one(related='plan_id.department_id',  string='Département',  readonly=True)
    nature         = fields.Selection(related='plan_id.nature',         string='Nature',       readonly=True)
    responsable_id = fields.Many2one(related='plan_id.responsable_id', string='Responsable',  readonly=True)
    date_realisation = fields.Date(related='plan_id.date_realisation', string='Date de réalisation', readonly=True)
    avancement     = fields.Integer(related='plan_id.avancement',       string='Avancement %', readonly=True)
    efficacite     = fields.Selection(related='plan_id.efficacite',     string='Efficacité',   readonly=True)
    etat_avancement= fields.Selection(related='plan_id.etat_avancement',string='État',         readonly=True)
    sent_to_rmqse  = fields.Boolean(related='plan_id.sent_to_rmqse',   string='Plan reçu',    readonly=True)


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
        selected_plans = self.line_ids.filtered(lambda l: l.selected).mapped('plan_id')
        if not selected_plans:
            raise UserError("Aucun plan sélectionné. Cochez au moins un plan à consolider.")
        selected_plans.with_context(_skip_date_maj=True).write({
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
