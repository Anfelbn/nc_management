# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class ConsulterVersionImprovementWizard(models.TransientModel):
    _name = 'nc_management.consulter_version_improvement_wizard'
    _description = "Consulter une version passée du plan d'amélioration"

    improvement_plan_id = fields.Many2one(
        'nc_management.smi_improvement_plan', readonly=True, required=True)
    date_consultation = fields.Date(
        string='Date à consulter')

    @api.multi
    def action_consulter(self):
        self.ensure_one()
        plan = self.improvement_plan_id
        date_sel = fields.Date.from_string(str(self.date_consultation))
        raw = plan.date_ouverture or str(plan.create_date)[:10]
        date_creation = fields.Date.from_string(str(raw))
        if date_sel < date_creation:
            raise UserError(
                "Ce plan n'existait pas le %s.\n"
                "Il a été créé le %s." % (
                    date_sel.strftime('%d/%m/%Y'),
                    date_creation.strftime('%d/%m/%Y'),
                ))
        plan.write({'date_consultation': self.date_consultation})
        inner_action = {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.smi_improvement_plan',
            'res_id': self.improvement_plan_id.id,
            'views': [[False, 'form']],
            'target': 'current',
        }
        return {
            'type': 'ir.actions.client',
            'tag': 'nc_management.clear_and_navigate',
            'params': {'inner_action': inner_action},
        }
