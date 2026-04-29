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
            new_state = 'submitted'
            msg = 'FNC soumise par <b>%s</b> et assignée à <b>%s</b>.' % (
                self.env.user.name, recipient.name)
            extra_vals = {'submitted_by_id': self.env.user.id}

        elif fnc.state == 'submitted':
            if not fnc.action_immediate:
                raise UserError("Veuillez remplir l'action immédiate.")
            if not fnc.analyse_causes:
                raise UserError("Veuillez remplir l'analyse des causes.")
            new_state = 'in_progress'
            msg = 'Traitement complété par <b>%s</b> — envoyé à <b>%s</b> pour validation.' % (
                self.env.user.name, recipient.name)
            extra_vals = {}

        elif fnc.state == 'in_progress':
            if not fnc.superieur_id:
                raise UserError('Veuillez signer en tant que supérieur hiérarchique.')
            new_state = 'validated'
            msg = 'FNC validée par <b>%s</b> — envoyée à <b>%s</b> pour clôture.' % (
                fnc.superieur_id.name, recipient.name)
            extra_vals = {}

        else:
            raise UserError("Cette FNC ne peut pas être envoyée dans son état actuel.")

        vals = {'state': new_state, 'assigned_to_id': recipient.id}
        vals.update(extra_vals)
        fnc.write(vals)

        note_part = '<br/>Message : %s' % self.note if self.note else ''
        fnc.message_post(body=msg + note_part)

        if recipient.user_id:
            fnc.message_post(
                body='Vous avez reçu la fiche <b>%s</b> — action requise.' % fnc.name,
                partner_ids=[recipient.user_id.partner_id.id],
                subtype='mail.mt_comment',
                message_type='comment')

        return {'type': 'ir.actions.act_window_close'}
