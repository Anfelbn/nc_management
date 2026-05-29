from odoo import models, fields, api


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
    plan_ids = fields.Many2many(
        'nc_management.plan_action_smi',
        'nc_consolidate_wizard_plan_rel',
        'wizard_id',
        'plan_id',
        string='Plans à consolider',
        domain=[
            ('is_global', '=', False),
            ('global_plan_id', '=', False),
        ],
    )

    @api.model
    def default_get(self, fields_list):
        res = super(ConsolidateWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            res['global_plan_id'] = active_id
        return res

    @api.multi
    def action_consolidate(self):
        self.ensure_one()
        if self.plan_ids:
            self.plan_ids.with_context(_skip_date_maj=True).write({
                'global_plan_id': self.global_plan_id.id,
                'submission_state': 'integre',
            })
            self.global_plan_id.with_context(_skip_date_maj=True).write({
                'date_maj': fields.Datetime.now(),
            })
        return {'type': 'ir.actions.act_window_close'}
