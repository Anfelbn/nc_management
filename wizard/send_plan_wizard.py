from odoo import models, fields, api
from odoo.exceptions import UserError


class SendPlanWizard(models.TransientModel):
    _name = 'nc_management.send_plan_wizard'
    _description = 'Envoyer le Plan SMI à la Responsable Qualité'

    plan_id = fields.Many2one(
        'nc_management.plan_action_smi',
        string='Plan',
        readonly=True)

    recipient_id = fields.Many2one(
        'hr.employee',
        string='Envoyer à',
        required=True,
        context={'no_create': True, 'no_create_edit': True})

    note = fields.Text(string='Message (optionnel)')

    @api.multi
    def action_send(self):
        self.ensure_one()
        plan = self.plan_id
        recipient = self.recipient_id

        if not plan:
            raise UserError('Aucun plan trouvé.')
        if not plan.nature:
            raise UserError("Veuillez renseigner la Nature avant d'envoyer le plan.")
        if plan.name == 'New':
            raise UserError("Veuillez d'abord générer le numéro du plan.")

        note_part = '<br/>Message : %s' % self.note if self.note else ''

        plan.write({
            'sent_to_rmqse':    True,
            'submission_state': 'soumis',
            'date_envoi':       fields.Datetime.now(),
            'sent_by':          self.env.uid,
            'mois_reception':   fields.Date.today(),
        })

        plan.message_post(
            body='Plan soumis par <b>%s</b> à <b>%s</b>.%s' % (
                self.env.user.name, recipient.name, note_part))

        partner_ids = [recipient.user_id.partner_id.id] if recipient.user_id else []
        if partner_ids:
            plan.message_post(
                body='Vous avez reçu le plan <b>%s</b> — action requise.' % plan.name,
                partner_ids=partner_ids,
                subtype='mail.mt_comment',
                message_type='comment')

        return {'type': 'ir.actions.act_window_close'}
