from odoo import models, fields, api
from odoo.exceptions import UserError


class SendFacWizard(models.TransientModel):
    _name = 'nc_management.send_fac_wizard'
    _description = 'Envoyer la FAC'

    fac_id = fields.Many2one(
        'nc_management.corrective_action',
        string='FAC',
        readonly=True)

    recipient_id = fields.Many2one(
        'hr.employee',
        string='Envoyer à',
        required=True,
        domain=[],
        context={'no_create': True, 'no_create_edit': True})

    note = fields.Text(string='Message (optionnel)')

    @api.multi
    def action_send(self):
        self.ensure_one()
        fac = self.fac_id
        recipient = self.recipient_id

        if not fac:
            raise UserError('Aucune FAC trouvée.')

        note_part = '<br/>Message : %s' % self.note if self.note else ''
        partner_ids = [recipient.user_id.partner_id.id] if recipient.user_id else []
        is_qm = bool(recipient.user_id and recipient.user_id.has_group(
            'nc_management.group_responsable_qualite'))

        fac.write({
            'date_envoi':     fields.Date.today(),
            'responsable_id': recipient.user_id.id if recipient.user_id else False,
            'sent_by_id':     self.env.uid,
        })

        # Notification sur la FAC
        fac.message_post(
            body='FAC envoyée par <b>%s</b> à <b>%s</b>.%s' % (
                self.env.user.name, recipient.name, note_part))
        if partner_ids:
            fac.message_post(
                body='Vous avez reçu la fiche <b>%s</b> — action requise.' % fac.name,
                partner_ids=partner_ids,
                subtype='mail.mt_comment',
                message_type='comment')

        # Si destinataire est QM → inclure aussi la FNC liée dans son dashboard
        if is_qm and fac.fnc_id:
            fnc = fac.fnc_id
            fnc.write({'date_envoi': fields.Date.today()})
            fnc.message_post(
                body='FNC liée — FAC <b>%s</b> envoyée à <b>%s</b> par <b>%s</b>.%s' % (
                    fac.name, recipient.name, self.env.user.name, note_part))
            if partner_ids:
                fnc.message_post(
                    body='Vous avez reçu la fiche <b>%s</b> (FNC liée à la FAC <b>%s</b>) — action requise.' % (
                        fnc.name, fac.name),
                    partner_ids=partner_ids,
                    subtype='mail.mt_comment',
                    message_type='comment')

        return {'type': 'ir.actions.act_window_close'}
