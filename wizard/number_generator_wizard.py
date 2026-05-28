from odoo import models, fields, api
from datetime import datetime

class NumberGeneratorWizard(models.TransientModel):
    _name = 'nc_management.number_generator_wizard'
    _description = 'Générateur de Numéro FNC'

    fnc_id = fields.Many2one(
        'nc_management.nonconformity',
        string='FNC',
        required=False,
        ondelete='cascade')

    category = fields.Selection([
        ('type_nc_produit', 'NC Produit'),
        ('type_reclamation', 'Réclamation clients / PI'),
        ('type_sst', 'SST Accident'),
        ('type_environnement', 'Environnement'),
        ('type_audit', 'Audit interne/Externe'),
        ('type_achat', 'Achat'),
        ('type_reception', 'Réception'),
        ('type_dysfonctionnement', 'Dysfonctionnement'),
        ('type_travaux', 'Travaux'),
        ('type_autre', 'Autre'),
    ], string='Type de NC', required=True)

    nc_type_id = fields.Many2one('nc_management.nc_type', string='Produit/Abréviation', required=True)

    @api.onchange('category')
    def _onchange_category(self):
        self.nc_type_id = False
        if self.category:
            return {'domain': {'nc_type_id': [('category', '=', self.category)]}}
        else:
            return {'domain': {'nc_type_id': []}}

    def _generate_name(self, abr):
        year = datetime.now().year
        seq_code = 'nc_management.fnc.%s' % abr.lower()
        seq_env = self.env['ir.sequence'].sudo()
        sequence = seq_env.search([('code', '=', seq_code)], limit=1)
        if not sequence:
            sequence = seq_env.create({
                'name': 'Séquence FNC %s' % abr,
                'code': seq_code,
                'prefix': '',
                'padding': 3,
                'number_next': 1,
                'number_increment': 1,
            })
        seq_number = sequence.next_by_id()
        return "%s-%s %s" % (abr, seq_number, year)

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        abr = self.nc_type_id.code
        generated_name = self._generate_name(abr)

        vals = {
            'name': generated_name,
            self.category: True,
        }

        if self.fnc_id:
            fnc = self.fnc_id
            if fnc.name != 'New':
                raise UserError(
                    "Le numéro FNC '%s' est définitif et ne peut pas être régénéré." % fnc.name
                )
            fnc.with_context(skip_fnc_validation=True).write(vals)
            return {'type': 'ir.actions.act_window_close'}

        # Créer une nouvelle FNC directement depuis le wizard
        fnc = self.env['nc_management.nonconformity'].with_context(skip_fnc_validation=True).create(vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.nonconformity',
            'res_id': fnc.id,
            'view_mode': 'form',
            'target': 'current',
        }
