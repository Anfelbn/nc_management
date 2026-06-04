from odoo import models, fields, api


class ConsulterVersionWizard(models.TransientModel):
    _name = 'nc_management.consulter_version_wizard'
    _description = 'Consulter une version passée du plan'

    plan_id = fields.Many2one(
        'nc_management.plan_action_smi', readonly=True, required=True)
    date_consultation = fields.Date(
        string='Date à consulter', required=True)

    @api.multi
    def action_consulter(self):
        self.ensure_one()
        self.plan_id.with_context(_skip_date_maj=True).write({
            'date_consultation': self.date_consultation,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.plan_action_smi',
            'res_id': self.plan_id.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'nc_management.view_plan_smi_form_global').id,
            'target': 'current',
        }
