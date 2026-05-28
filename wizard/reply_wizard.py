from odoo import models, fields, api
from odoo.exceptions import UserError


class ReplyWizard(models.TransientModel):
    _name = 'nc_management.reply_wizard'
    _description = 'Répondre à une fiche reçue'

    record_model = fields.Char(string='Modèle', required=True)
    record_id    = fields.Integer(string='ID de la fiche', required=True)

    recipient_id = fields.Many2one(
        'hr.employee',
        string='Destinataire',
        required=True,
        context={'no_create': True, 'no_create_edit': True})

    note = fields.Text(string='Message (optionnel)')

    @api.multi
    def action_reply(self):
        self.ensure_one()

        if not self.record_id or not self.record_model:
            raise UserError('Aucune fiche trouvée.')

        record = self.env[self.record_model].browse(self.record_id)
        if not record.exists():
            raise UserError('La fiche est introuvable.')

        recipient = self.recipient_id
        sender    = self.env.user.name

        note_part = '<br/>Message : %s' % self.note if self.note else ''
        body = (
            'Réponse de <b>%s</b> transmise à <b>%s</b>.%s'
            % (sender, recipient.name, note_part)
        )

        record.message_post(
            body=body,
            subtype='mail.mt_comment',
            message_type='comment')

        if recipient.user_id:
            record.message_post(
                body='Vous avez reçu une réponse concernant la fiche <b>%s</b>.'
                     % record.name,
                partner_ids=[recipient.user_id.partner_id.id],
                subtype='mail.mt_comment',
                message_type='comment')

        return {'type': 'ir.actions.act_window_close'}
