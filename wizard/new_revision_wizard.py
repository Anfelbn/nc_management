from odoo import models, fields, api
from odoo.exceptions import UserError


class NewRevisionWizard(models.TransientModel):
    _name = 'smi_management.new_revision_wizard'
    _description = 'Assistant Nouvelle Révision de Document'

    source_template_id = fields.Many2one(
        'smi_management.form_template', string='Gabarit source', readonly=True)
    doc_type = fields.Selection(
        related='source_template_id.doc_type', readonly=True, string='Type')

    revision_number   = fields.Integer(string='N° de révision', required=True)
    revision_date     = fields.Date(
        string='Date de révision', required=True, default=fields.Date.today)
    reference         = fields.Char(string='Référence du document', required=True)
    description_changes = fields.Text(string='Modifications apportées')

    @api.model
    def default_get(self, fields_list):
        res = super(NewRevisionWizard, self).default_get(fields_list)
        source_id = self.env.context.get('default_source_template_id')
        if source_id:
            source = self.env['smi_management.form_template'].browse(source_id)
            last_rev = self.env['smi_management.document_revision'].search(
                [('doc_type', '=', source.doc_type)],
                order='revision_number desc', limit=1)
            res['revision_number'] = (last_rev.revision_number + 1) if last_rev else 1
            if last_rev and last_rev.reference:
                res['reference'] = last_rev.reference
        return res

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        source = self.source_template_id
        if not source:
            raise UserError("Aucun gabarit source sélectionné.")

        label    = 'FNC' if source.doc_type == 'fnc' else 'FAC'
        new_name = '%s — Révision %02d (%s)' % (
            label, self.revision_number, str(self.revision_date))

        # 1. Dupliquer le gabarit (inactif pour l'instant)
        new_tpl = source.copy({
            'name': new_name,
            'is_active': False,
            'revision_id': False,
        })

        # 2. Créer la révision (auto-obsolescence des autres)
        new_rev = self.env['smi_management.document_revision'].create({
            'doc_type':         source.doc_type,
            'revision_number':  self.revision_number,
            'revision_date':    self.revision_date,
            'reference':        self.reference,
            'description':      self.description_changes or '',
            'etat':             'valable',
        })

        # 3. Lier gabarit ↔ révision
        new_tpl.write({'revision_id': new_rev.id})

        # 4. Ouvrir le nouveau gabarit pour édition
        view_id = self.env.ref('smi_management.view_form_template_form').id
        return {
            'type':      'ir.actions.act_window',
            'name':      'Nouveau gabarit — %s' % new_name,
            'res_model': 'smi_management.form_template',
            'res_id':    new_tpl.id,
            'view_mode': 'form',
            'view_id':   view_id,
            'target':    'current',
        }
