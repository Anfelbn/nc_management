from odoo import models, fields, api
from odoo.exceptions import UserError


class PlanNumberWizard(models.TransientModel):
    _name = 'nc_management.plan_number_wizard'
    _description = 'Saisie du numéro de référence du plan'

    plan_id = fields.Many2one(
        'nc_management.plan_action_smi',
        string='Plan',
        required=True,
        ondelete='cascade',
    )
    reference = fields.Char(string='Numéro de référence', required=True)

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        if not self.reference or not self.reference.strip():
            raise UserError("Veuillez saisir un numéro de référence.")
        plan = self.plan_id
        if plan.name != 'New':
            raise UserError(
                "La référence '%s' a déjà été assignée." % plan.name
            )
        plan.write({'name': self.reference.strip()})
        return {'type': 'ir.actions.act_window_close'}
