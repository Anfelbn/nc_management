from odoo import models, fields, api
from datetime import datetime

class NumberGeneratorWizard(models.TransientModel):
    _name = 'nc_management.number_generator_wizard'
    _description = 'Générateur de Numéro FNC'

    fnc_id = fields.Many2one('nc_management.nonconformity', string='FNC', required=True)
    
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

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        abr = self.nc_type_id.code
        year = datetime.now().year
        
        # Utilisation d'une séquence basée sur l'abréviation
        seq_code = 'nc_management.fnc.%s' % abr.lower()
        sequence = self.env['ir.sequence'].search([('code', '=', seq_code)], limit=1)
        
        if not sequence:
            sequence = self.env['ir.sequence'].create({
                'name': 'Séquence FNC %s' % abr,
                'code': seq_code,
                'prefix': '',
                'padding': 3,
                'number_next': 1,
                'number_increment': 1,
            })
            
        seq_number = sequence.next_by_id()
        generated_name = "%s-%s %s" % (abr, seq_number, year)
        
        # Mise à jour de la FNC parente
        vals = {
            'name': generated_name,
            self.category: True,
        }
        self.fnc_id.write(vals)
        
        return {'type': 'ir.actions.act_window_close'}
