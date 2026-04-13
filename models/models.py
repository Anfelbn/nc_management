from odoo import models, fields

class Nonconformity(models.Model):
    _name = 'nc_management.nonconformity'
    _description = 'Fiche Non-Conformité'

    name = fields.Char(string='Référence', required=True)
    description = fields.Text(string='Description')


class CorrectiveAction(models.Model):
    _name = 'nc_management.corrective_action'
    _description = 'Action Corrective'

    name = fields.Char(string='Référence', required=True)
    description = fields.Text(string='Description')
