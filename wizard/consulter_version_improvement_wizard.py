# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ConsulterVersionImprovementWizard(models.TransientModel):
    _name = 'nc_management.consulter_version_improvement_wizard'
    _description = "Consulter une version passée du plan d'amélioration"

    improvement_plan_id = fields.Many2one(
        'nc_management.smi_improvement_plan', readonly=True, required=True)
    date_consultation = fields.Date(
        string='Date à consulter', required=True)

    @api.multi
    def action_consulter(self):
        self.ensure_one()
        self.improvement_plan_id.write(
            {'date_consultation': self.date_consultation})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.smi_improvement_plan',
            'res_id': self.improvement_plan_id.id,
            'views': [[False, 'form']],
            'target': 'current',
        }
