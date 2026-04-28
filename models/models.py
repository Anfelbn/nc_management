from datetime import date, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError

class Nonconformity(models.Model):
    _name = 'nc_management.nonconformity'
    _description = 'Fiche de Non-Conformité'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ── En-tête ──────────────────────────────────────────────
    name = fields.Char(
        string='N° FNC', required=True, copy=False,
        readonly=True, default='New')
    direction_id  = fields.Many2one('hr.department', string='Direction / Emetteur')
    service_dpt   = fields.Char(string='Sce / DPT')
    date          = fields.Date(string='Date', default=fields.Date.today)

    # ── Type de Non-Conformité ────────────────────────────────
    type_nc_produit        = fields.Boolean(string='NC Produit')
    type_audit             = fields.Boolean(string='Audit interne/Externe')
    type_reclamation       = fields.Boolean(string='Réclamation clients / PI')
    type_achat             = fields.Boolean(string='Achat')
    type_sst               = fields.Boolean(string='SST Accident')
    type_reception         = fields.Boolean(string='Réception')
    type_environnement     = fields.Boolean(string='Environnement')
    type_dysfonctionnement = fields.Boolean(string='Dysfonctionnement')
    type_travaux           = fields.Boolean(string='Travaux')
    type_autre             = fields.Boolean(string='Autre')
    type_autre_preciser    = fields.Char(string='Préciser')

    # ── Section 1 — Description ───────────────────────────────
    description        = fields.Text(string='1- Description de la non-conformité')
    signale_par_id     = fields.Many2one('hr.employee', string='Nom de la personne qui signale')
    date_signalement   = fields.Date(string='Date de signalement')
    fonction_visa      = fields.Char(string='Fonction et visa')

    # ── Traitement ────────────────────────────────────────────
    trait_reprise          = fields.Boolean(string='Reprise pour mise en conformité')
    trait_declassement     = fields.Boolean(string='Déclassement pour autre utilisation')
    trait_retour_fourn     = fields.Boolean(string='Retour au fournisseur')
    trait_recyclage        = fields.Boolean(string='Recyclage')
    trait_reparation       = fields.Boolean(string='Réparation')
    trait_autre            = fields.Boolean(string='Autre')
    trait_autre_preciser   = fields.Char(string='Préciser (Traitement)')

    # ── Section 2 — Action immédiate ─────────────────────────
    action_immediate = fields.Text(string='2- Action immédiate')
    realise_par_id   = fields.Many2one('hr.employee', string='Réalisé par')
    date_realisation = fields.Date(string='Date de réalisation')

    # ── Section 3 — Analyse des causes ───────────────────────
    analyse_causes = fields.Text(string='3- Analyse des causes')
    impact         = fields.Text(string='Impact : coût, incidence, risque')

    # ── Références FAC ───────────────────────────────────────
    fac_ids               = fields.One2many('nc_management.corrective_action', 'fnc_id', string="Fiches d'action liées")
    fac_reference         = fields.Char(string="N° Fiche d'action")
    responsable_action_id = fields.Many2one('hr.employee', string="Responsable de l'action(s)")

    # ── Validation hiérarchique ───────────────────────────────
    superieur_id    = fields.Many2one('hr.employee', string='Le supérieur hiérarchique')
    date_validation = fields.Date(string='Date validation')
    signature       = fields.Char(string='Signature')

    # ── Statut ────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',       'Brouillon'),
        ('submitted',   'Soumise'),
        ('in_progress', 'En cours'),
        ('closed',      'Clôturée'),
    ], string='Statut', default='draft', track_visibility='onchange')

    # ── Numérotation automatique et création FAC ──────────────
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'nc_management.nonconformity') or 'New'
        
        res = super(Nonconformity, self).create(vals)
        
        # Création automatique de la première FAC liée
        self.env['nc_management.corrective_action'].create({
            'fnc_id': res.id,
            'direction_id': res.direction_id.id,
            'rappel_nc': res.description,
            'analyse_causes': res.analyse_causes,
            'date_fnc': res.date,
        })
        return res

    @api.multi
    def write(self, vals):
        # On mémorise les valeurs actuelles pour la comparaison "smart sync"
        records_data = {}
        if any(field in vals for field in ['description', 'analyse_causes', 'direction_id']):
            for rec in self:
                records_data[rec.id] = {
                    'description': rec.description,
                    'analyse_causes': rec.analyse_causes,
                    'direction_id': rec.direction_id.id,
                }

        res = super(Nonconformity, self).write(vals)

        # Mise à jour intelligente de TOUTES les FAC liées
        if records_data:
            for rec in self:
                for fac in rec.fac_ids:
                    updates = {}
                    old_data = records_data.get(rec.id, {})
                    
                    # Sync Description -> Rappel NC
                    if 'description' in vals:
                        if not fac.rappel_nc or fac.rappel_nc == old_data.get('description'):
                            updates['rappel_nc'] = vals['description']
                    
                    # Sync Analyse Causes
                    if 'analyse_causes' in vals:
                        if not fac.analyse_causes or fac.analyse_causes == old_data.get('analyse_causes'):
                            updates['analyse_causes'] = vals['analyse_causes']

                    # Sync Direction
                    if 'direction_id' in vals:
                        if not fac.direction_id or fac.direction_id.id == old_data.get('direction_id'):
                            updates['direction_id'] = vals['direction_id']
                    
                    if updates:
                        fac.write(updates)
        return res

    # ── Boutons workflow ──────────────────────────────────────
    @api.multi
    def action_submit(self):
        for rec in self:
            if not rec.description:
                raise UserError('Veuillez remplir la description de la non-conformité.')
            rec.state = 'submitted'
            rec.message_post(body='Fiche FNC soumise.')

    @api.multi
    def action_progress(self):
        for rec in self:
            rec.state = 'in_progress'
            rec.message_post(body='Fiche FNC prise en charge.')

    @api.multi
    def action_close(self):
        for rec in self:
            rec.state = 'closed'
            rec.message_post(body='Fiche FNC clôturée par la Responsable Qualité.')


class CorrectiveAction(models.Model):
    _name = 'nc_management.corrective_action'
    _description = "Fiche d'Action Corrective"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ── En-tête ───────────────────────────────────────────────
    name         = fields.Char(
        string='N° FAC', required=True, copy=False,
        readonly=True, default='New')
    direction_id = fields.Many2one('hr.department', string='Direction')
    date         = fields.Date(string='Date', default=fields.Date.today)
    fnc_id       = fields.Many2one(
        'nc_management.nonconformity',
        string='N° FNC ou autre document',
        ondelete='restrict',
        index=True
    )
    date_fnc     = fields.Date(string='Date FNC')

    # ── Section 1 — Rappel NC ─────────────────────────────────
    rappel_nc = fields.Text(string='1- Rappel de la Non-Conformité')

    # ── Section 2 — Analyse des causes ───────────────────────
    analyse_causes         = fields.Text(string='2- Analyse des causes de la non-conformité')
    responsable_analyse_id = fields.Many2one('hr.employee', string='Responsable analyse')
    date_analyse           = fields.Date(string='Date analyse')
    visa_analyse           = fields.Char(string='Visa analyse')

    # ── Section 3 — Actions décidées ─────────────────────────
    action_line_ids        = fields.One2many('nc_management.action_line', 'fac_id', string='Actions décidées')
    responsable_actions_id = fields.Many2one('hr.employee', string='Responsable actions')
    date_actions           = fields.Date(string='Date actions')
    visa_actions           = fields.Char(string='Visa actions')

    # ── Efficacité ────────────────────────────────────────────
    actions_efficaces         = fields.Selection([
        ('oui', 'Oui'), ('non', 'Non'),
    ], string='Action(s) efficace(s)')
    responsable_efficacite_id = fields.Many2one('hr.employee', string='Responsable efficacité')

    # ── Section 4 — Approbation QSE ──────────────────────────
    qse_nom_id = fields.Many2one('hr.employee', string='Nom Responsable QSE')
    qse_date   = fields.Date(string='Date approbation QSE')
    qse_visa   = fields.Char(string='Visa QSE')

    # ── Section 5 — Vérification ─────────────────────────────
    verification_efficacite = fields.Text(string="Vérification de l'efficacité de l'action")
    extension_possible      = fields.Selection([
        ('non', 'Non'), ('oui', 'Oui'),
    ], string="Extension possible de l'action")

    # ── Clôture ───────────────────────────────────────────────
    cloture_par_id = fields.Many2one('hr.employee', string='Clôturée par')
    date_cloture   = fields.Date(string='Date clôture')
    visa_cloture   = fields.Char(string='Visa clôture')

    # ── Statut ────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',    'Brouillon'),
        ('open',     'Ouverte'),
        ('verified', 'Vérifiée'),
        ('closed',   'Clôturée'),
    ], string='Statut', default='draft', track_visibility='onchange')

    # ── Remplissage auto via FNC ──────────────────────────────
    @api.onchange('fnc_id')
    def _onchange_fnc_id(self):
        if self.fnc_id:
            self.rappel_nc = self.fnc_id.description
            self.analyse_causes = self.fnc_id.analyse_causes
            self.direction_id = self.fnc_id.direction_id
            self.date_fnc = self.fnc_id.date

    # ── Numérotation automatique ──────────────────────────────
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'nc_management.corrective_action') or 'New'
        return super(CorrectiveAction, self).create(vals)

    # ── Boutons workflow ──────────────────────────────────────
    @api.multi
    def action_open(self):
        for rec in self:
            rec.state = 'open'
            rec.message_post(body='Fiche FAC ouverte.')

    @api.multi
    def action_verify(self):
        for rec in self:
            if not rec.action_line_ids:
                raise UserError('Veuillez ajouter au moins une action corrective.')
            rec.state = 'verified'
            rec.message_post(body='Actions vérifiées.')

    @api.multi
    def action_close(self):
        for rec in self:
            if not rec.actions_efficaces:
                raise UserError('Veuillez indiquer si les actions sont efficaces.')
            rec.state = 'closed'
            rec.cloture_par_id = self.env['hr.employee'].search(
                [('user_id', '=', self.env.uid)], limit=1).id
            rec.date_cloture = fields.Date.today()
            rec.message_post(body='Fiche FAC clôturée par la Responsable Qualité.')


class ActionLine(models.Model):
    _name = 'nc_management.action_line'
    _description = "Ligne d'action corrective"

    fac_id             = fields.Many2one(
        'nc_management.corrective_action',
        string='FAC',
        required=True,
        ondelete='cascade',
        index=True
    )
    direction_id       = fields.Many2one(
        'hr.department',
        string='Direction',
        related='fac_id.direction_id',
        store=True,
        readonly=True
    )
    action_description = fields.Char(string='Action(s)')
    date_prevue        = fields.Date(string='Date prévue')
    date_realisation   = fields.Date(string='Date de réalisation')
    responsable_id     = fields.Many2one('hr.employee', string="Responsable de l'action")


class NcDashboard(models.Model):
    _name = 'nc_management.dashboard'
    _description = 'Dashboard'

    @api.model
    def get_stats(self):
        from dateutil.relativedelta import relativedelta
        fnc = self.env['nc_management.nonconformity']
        fac = self.env['nc_management.corrective_action']
        total_fnc = fnc.search_count([])
        closed_fnc = fnc.search_count([('state', '=', 'closed')])
        taux = round((closed_fnc / total_fnc * 100) if total_fnc else 0, 1)

        limit = str(date.today() - timedelta(days=7))
        urgent = fnc.search_read(
            [('state', '=', 'in_progress'), ('date', '<=', limit)],
            ['name', 'direction_id', 'date', 'service_dpt'], limit=10)

        months = []
        for i in range(5, -1, -1):
            d = date.today() - relativedelta(months=i)
            m_start = d.replace(day=1)
            if i > 0:
                m_end = (d + relativedelta(months=1)).replace(day=1)
            else:
                m_end = date.today()
            count = fnc.search_count([
                ('date', '>=', str(m_start)),
                ('date', '<', str(m_end)),
            ])
            months.append({'month': m_start.strftime('%b %Y'), 'count': count})

        return {
            'fnc_draft':       fnc.search_count([('state', '=', 'draft')]),
            'fnc_submitted':   fnc.search_count([('state', '=', 'submitted')]),
            'fnc_in_progress': fnc.search_count([('state', '=', 'in_progress')]),
            'fnc_closed':      closed_fnc,
            'fnc_total':       total_fnc,
            'fac_draft':       fac.search_count([('state', '=', 'draft')]),
            'fac_open':        fac.search_count([('state', '=', 'open')]),
            'fac_verified':    fac.search_count([('state', '=', 'verified')]),
            'fac_closed':      fac.search_count([('state', '=', 'closed')]),
            'taux_cloture':    taux,
            'urgent':          urgent,
            'monthly':         months,
        }
