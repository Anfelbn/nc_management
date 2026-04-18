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
    trait_reprise      = fields.Boolean(string='Reprise pour mise en conformité')
    trait_declassement = fields.Boolean(string='Déclassement pour autre utilisation')
    trait_retour_fourn = fields.Boolean(string='Retour au fournisseur')
    trait_recyclage    = fields.Boolean(string='Recyclage')
    trait_reparation   = fields.Boolean(string='Réparation')
    trait_autre        = fields.Boolean(string='Autre')

    # ── Section 2 — Action immédiate ─────────────────────────
    action_immediate = fields.Text(string='2- Action immédiate')
    realise_par_id   = fields.Many2one('hr.employee', string='Réalisé par')
    date_realisation = fields.Date(string='Date de réalisation')

    # ── Section 3 — Analyse des causes ───────────────────────
    analyse_causes = fields.Text(string='3- Analyse des causes')
    impact         = fields.Text(string='Impact : coût, incidence, risque')

    # ── Liaison FAC ───────────────────────────────────────────
    fac_ids               = fields.One2many(
        'nc_management.corrective_action',
        'fnc_id',
        string='Fiches d\'Action Corrective'
    )
    responsable_action_id = fields.Many2one('hr.employee', string='Responsable de l\'action(s)')

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

    # ── Numérotation automatique ──────────────────────────────
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'nc_management.nonconformity') or 'New'
        return super(Nonconformity, self).create(vals)

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
            if not rec.fac_ids:
                raise UserError('Veuillez associer au moins une Fiche d\'Action Corrective avant de clôturer.')
            if any(fac.state != 'closed' for fac in rec.fac_ids):
                raise UserError('Toutes les Fiches d\'Action Corrective liées doivent être clôturées avant de clôturer la FNC.')
            rec.state = 'closed'
            rec.message_post(body='Fiche FNC clôturée par la Responsable Qualité.')


class CorrectiveAction(models.Model):
    _name = 'nc_management.corrective_action'
    _description = 'Fiche d\'Action Corrective'
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
    verification_efficacite = fields.Text(string='Vérification de l\'efficacité de l\'action')
    extension_possible      = fields.Selection([
        ('non', 'Non'), ('oui', 'Oui'),
    ], string='Extension possible de l\'action')

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

class NcDashboard(models.Model):
    _name = 'nc_management.dashboard'
    _description = 'Dashboard Responsable Qualité'

    @api.model
    def get_dashboard_data(self):
        fnc = self.env['nc_management.nonconformity']
        fac = self.env['nc_management.corrective_action']
        return {
            'fnc_draft':       fnc.search_count([('state', '=', 'draft')]),
            'fnc_submitted':   fnc.search_count([('state', '=', 'submitted')]),
            'fnc_in_progress': fnc.search_count([('state', '=', 'in_progress')]),
            'fnc_closed':      fnc.search_count([('state', '=', 'closed')]),
            'fac_draft':       fac.search_count([('state', '=', 'draft')]),
            'fac_open':        fac.search_count([('state', '=', 'open')]),
            'fac_verified':    fac.search_count([('state', '=', 'verified')]),
            'fac_closed':      fac.search_count([('state', '=', 'closed')]),
        }
class ActionLine(models.Model):
    _name = 'nc_management.action_line'
    _description = 'Ligne d\'action corrective'

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
    responsable_id     = fields.Many2one('hr.employee', string='Responsable de l\'action')   
