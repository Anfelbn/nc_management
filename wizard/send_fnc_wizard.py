from odoo import models, fields, api
from odoo.exceptions import UserError


class SendFncWizard(models.TransientModel):
    _name = 'nc_management.send_fnc_wizard'
    _description = 'Envoyer la FNC'

    fnc_id = fields.Many2one(
        'nc_management.nonconformity',
        string='FNC',
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
        fnc = self.fnc_id
        recipient = self.recipient_id

        if not fnc:
            raise UserError('Aucune FNC trouvée.')

        if fnc.state == 'draft':
            if not fnc.description:
                raise UserError("Veuillez remplir la description avant d'envoyer.")
            if not fnc.fonction_visa:
                raise UserError("Veuillez remplir la fonction et visa avant d'envoyer.")
            new_state = 'submitted'
            msg = 'FNC soumise par <b>%s</b> et assignée à <b>%s</b>.' % (
                self.env.user.name, recipient.name)
            extra_vals = {
                'submitted_by_id': self.env.user.id,
                'assigned_to_id': recipient.id,
                'current_handler_uid': recipient.user_id.id if recipient.user_id else False,
            }

        elif fnc.state == 'submitted':
            new_state = 'submitted'
            msg = 'FNC transmise par <b>%s</b> à <b>%s</b> pour traitement de la NC.' % (
                self.env.user.name, recipient.name)
            extra_vals = {'current_handler_uid': recipient.user_id.id if recipient.user_id else False}

        elif fnc.state == 'in_progress':
            new_state = 'in_progress'
            msg = 'FNC transmise par <b>%s</b> à <b>%s</b>.' % (
                self.env.user.name, recipient.name)
            extra_vals = {'assigned_to_id': recipient.id}

        elif fnc.state == 'validated':
            note_part = '<br/>Message : %s' % self.note if self.note else ''
            fnc.message_post(body='Notification envoyée par <b>%s</b> à <b>%s</b>.%s' % (
                self.env.user.name, recipient.name, note_part))
            if recipient.user_id:
                fnc.message_post(
                    body='Vous avez reçu un message concernant la fiche <b>%s</b>.' % fnc.name,
                    partner_ids=[recipient.user_id.partner_id.id],
                    subtype='mail.mt_comment',
                    message_type='comment')
            return {'type': 'ir.actions.act_window_close'}

        else:
            raise UserError("Cette FNC ne peut pas être envoyée dans son état actuel.")

        vals = {'state': new_state, 'date_envoi': fields.Date.today(), 'sent_by_id': self.env.uid}
        vals.update(extra_vals)
        fnc.write(vals)

        note_part = '<br/>Message : %s' % self.note if self.note else ''
        fnc.message_post(body=msg + note_part)

        partner_ids = [recipient.user_id.partner_id.id] if recipient.user_id else []
        is_qm = bool(recipient.user_id and recipient.user_id.has_group(
            'nc_management.group_responsable_qualite'))

        if partner_ids:
            fnc.message_post(
                body='Vous avez reçu la fiche <b>%s</b> — action requise.' % fnc.name,
                partner_ids=partner_ids,
                subtype='mail.mt_comment',
                message_type='comment')

        for fac in fnc.sudo().fac_ids:
            if is_qm:
                # QM reçoit la FAC liée → date_envoi = aujourd'hui pour apparaître dans le dashboard QM
                fac.sudo().write({
                    'responsable_id': recipient.user_id.id if recipient.user_id else False,
                    'date_envoi': fields.Date.today(),
                    'sent_by_id': self.env.uid,
                })
                fac.sudo().message_post(
                    body='FAC liée à <b>%s</b> — transmise à <b>%s</b>.%s' % (
                        fnc.name, recipient.name, note_part))
                if partner_ids:
                    fac.sudo().message_post(
                        body='Vous avez reçu la fiche <b>%s</b> (liée à la FNC <b>%s</b>) — action requise.' % (
                            fac.name, fnc.name),
                        partner_ids=partner_ids,
                        subtype='mail.mt_comment',
                        message_type='comment')
            else:
                # NC user ne reçoit pas la FAC via le routing FNC → effacer date_envoi
                # pour qu'elle n'apparaisse pas dans la section "Fiches reçues" du NC user
                fac.sudo().write({
                    'responsable_id': recipient.user_id.id if recipient.user_id else False,
                    'date_envoi': False,
                })

        return {'type': 'ir.actions.act_window_close'}
