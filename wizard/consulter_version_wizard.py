from odoo import models, fields, api


class ConsulterVersionWizard(models.TransientModel):
    _name = 'nc_management.consulter_version_wizard'
    _description = 'Consulter une version passée du plan'

    plan_id = fields.Many2one(
        'nc_management.plan_action_smi', readonly=True, required=True)
    date_consultation = fields.Date(
        string='Date à consulter', required=True)
    return_view_ref = fields.Char(
        default='nc_management.view_plan_smi_form_global')

    @api.multi
    def action_consulter(self):
        self.ensure_one()
        date_str = str(self.date_consultation)

        # Trouver le plan global actif à la date sélectionnée :
        # le plus récent dont mois_reception <= date choisie
        historical_plan = self.env['nc_management.plan_action_smi'].search([
            ('is_global', '=', True),
            ('mois_reception', '<=', date_str),
        ], order='mois_reception desc', limit=1)

        if not historical_plan:
            from odoo.exceptions import UserError as _UE
            d = fields.Date.from_string(date_str).strftime('%d/%m/%Y')
            raise _UE("Aucun plan d'amélioration n'existait le %s." % d)

        # Effacer date_consultation sur le plan courant si différent
        if self.plan_id and self.plan_id.id != historical_plan.id:
            self.plan_id.with_context(_skip_date_maj=True).write(
                {'date_consultation': False})

        historical_plan.with_context(_skip_date_maj=True).write({
            'date_consultation': self.date_consultation,
        })

        view_ref = self.return_view_ref or 'nc_management.view_plan_smi_form_global'
        flags = {'create': False} if view_ref == 'nc_management.view_plan_smi_form_analyse' else {}
        view_id = self.env.ref(view_ref).id
        inner_action = {
            'type': 'ir.actions.act_window',
            'name': "Plan d'Action d'Amélioration SMI",
            'res_model': 'nc_management.plan_action_smi',
            'res_id': historical_plan.id,
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'view_id': view_id,
            'target': 'current',
            'flags': flags,
            'context': {'default_is_global': True},
        }
        return {
            'type': 'ir.actions.client',
            'tag': 'nc_management.clear_and_navigate',
            'params': {'inner_action': inner_action},
        }
