# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class ConsulterVersionImprovementWizard(models.TransientModel):
    _name = 'nc_management.consulter_version_improvement_wizard'
    _description = "Consulter une version passée du plan d'amélioration"

    improvement_plan_id = fields.Many2one(
        'nc_management.smi_improvement_plan', readonly=True, required=True,
        ondelete='cascade')
    date_consultation = fields.Date(
        string='Date à consulter')

    @api.multi
    def action_consulter(self):
        self.ensure_one()
        date_str = str(self.date_consultation)

        # Trouver le plan de l'utilisateur existant à cette date
        historical_plan = self.env['nc_management.smi_improvement_plan'].search([
            ('create_uid', '=', self.env.uid),
            ('date_ouverture', '<=', date_str),
        ], order='date_ouverture desc', limit=1)

        if not historical_plan:
            d = fields.Date.from_string(date_str).strftime('%d/%m/%Y')
            raise UserError(
                "Aucun plan d'amélioration n'existait le %s." % d)

        # Effacer date_consultation sur le plan courant si différent
        if self.improvement_plan_id and self.improvement_plan_id.id != historical_plan.id:
            self.improvement_plan_id.write({'date_consultation': False})

        historical_plan.write({'date_consultation': self.date_consultation})

        inner_action = {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.smi_improvement_plan',
            'res_id': historical_plan.id,
            'views': [[False, 'form']],
            'target': 'current',
        }
        return {
            'type': 'ir.actions.client',
            'tag': 'nc_management.clear_and_navigate',
            'params': {'inner_action': inner_action},
        }
