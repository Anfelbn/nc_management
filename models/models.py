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
    direction_id  = fields.Many2one('hr.department', string='Direction / Emetteur',
                      context={'no_create': True, 'no_create_edit': True})
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
    signale_par_id     = fields.Many2one('hr.employee', string='Nom de la personne qui signale',
                           context={'no_create': True, 'no_create_edit': True})
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
    realise_par_id   = fields.Many2one('hr.employee', string='Réalisé par',
                         context={'no_create': True, 'no_create_edit': True})
    date_realisation = fields.Date(string='Date de réalisation')

    # ── Section 3 — Analyse des causes ───────────────────────
    analyse_causes = fields.Text(string='3- Analyse des causes')
    impact         = fields.Text(string='Impact : coût, incidence, risque')

    # ── Références FAC ───────────────────────────────────────
    fac_ids               = fields.One2many('nc_management.corrective_action', 'fnc_id', string="Fiches d'action liées")
    fac_reference         = fields.Char(string="N° Fiche d'action")
    responsable_action_id = fields.Many2one('hr.employee', string="Responsable de l'action(s)",
                              context={'no_create': True, 'no_create_edit': True})

    # ── Validation hiérarchique ───────────────────────────────
    superieur_id    = fields.Many2one('hr.employee', string='Le supérieur hiérarchique',
                      context={'no_create': True, 'no_create_edit': True})
    date_validation = fields.Date(string='Date validation')
    signature       = fields.Char(string='Signature')

    # ── Routing ───────────────────────────────────────────────
    assigned_to_id  = fields.Many2one(
        'hr.employee', string="Responsable de l'action",
        context={'no_create': True, 'no_create_edit': True},
        track_visibility='onchange')
    submitted_by_id = fields.Many2one(
        'res.users', string='Soumis par',
        readonly=True)
    validated_by_id = fields.Many2one(
        'hr.employee', string='Validé par (Sup. Hiérarchique)',
        context={'no_create': True, 'no_create_edit': True})

    # ── Statut ────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',       'Brouillon'),
        ('submitted',   'Soumise — En attente traitement'),
        ('in_progress', 'En cours — En attente validation'),
        ('validated',   'Validée — En attente clôture'),
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
    def action_open_send_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Envoyer la FNC',
            'res_model': 'nc_management.send_fnc_wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('nc_management.view_send_fnc_wizard').id,
            'target': 'new',
            'context': {'default_fnc_id': self.id},
        }

    @api.multi
    def action_close(self):
        for rec in self:
            rec.write({'state': 'closed'})
            rec.message_post(
                body='FNC clôturée par la Responsable Qualité.')

    def _is_creator(self):
        return self.submitted_by_id == self.env.user

    def _is_assigned(self):
        emp = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        return emp and emp.id == self.assigned_to_id.id


class CorrectiveAction(models.Model):
    _name = 'nc_management.corrective_action'
    _description = "Fiche d'Action Corrective"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ── En-tête ───────────────────────────────────────────────
    name         = fields.Char(
        string='N° FAC', required=True, copy=False,
        readonly=True, default='New')
    direction_id = fields.Many2one('hr.department', string='Direction',
                     context={'no_create': True, 'no_create_edit': True})
    date         = fields.Date(string='Date', default=fields.Date.today)
    fnc_id       = fields.Many2one(
        'nc_management.nonconformity',
        string='N° FNC ou autre document',
        ondelete='set null',
        index=True
    )
    date_fnc     = fields.Date(string='Date FNC')

    # ── Section 1 — Rappel NC ─────────────────────────────────
    rappel_nc = fields.Text(string='1- Rappel de la Non-Conformité')

    # ── Section 2 — Analyse des causes ───────────────────────
    analyse_causes         = fields.Text(string='2- Analyse des causes de la non-conformité')
    responsable_analyse_id = fields.Many2one('hr.employee', string='Responsable analyse',
                               context={'no_create': True, 'no_create_edit': True})
    date_analyse           = fields.Date(string='Date analyse')
    visa_analyse           = fields.Char(string='Visa analyse')

    # ── Section 3 — Actions décidées ─────────────────────────
    action_line_ids        = fields.One2many('nc_management.action_line', 'fac_id', string='Actions décidées')
    responsable_actions_id = fields.Many2one('hr.employee', string='Responsable actions',
                               context={'no_create': True, 'no_create_edit': True})
    date_actions           = fields.Date(string='Date actions')
    visa_actions           = fields.Char(string='Visa actions')

    # ── Efficacité ────────────────────────────────────────────
    actions_efficaces         = fields.Selection([
        ('oui', 'Oui'), ('non', 'Non'),
    ], string='Action(s) efficace(s)')
    responsable_efficacite_id = fields.Many2one('hr.employee', string='Responsable efficacité',
                                  context={'no_create': True, 'no_create_edit': True})

    # ── Section 4 — Approbation QSE ──────────────────────────
    qse_nom_id = fields.Many2one('hr.employee', string='Nom Responsable QSE',
                   context={'no_create': True, 'no_create_edit': True})
    qse_date   = fields.Date(string='Date approbation QSE')
    qse_visa   = fields.Char(string='Visa QSE')

    # ── Section 5 — Vérification ─────────────────────────────
    verification_efficacite = fields.Text(string="Vérification de l'efficacité de l'action")
    extension_possible      = fields.Selection([
        ('non', 'Non'), ('oui', 'Oui'),
    ], string="Extension possible de l'action")

    # ── Clôture ───────────────────────────────────────────────
    cloture_par_id = fields.Many2one('hr.employee', string='Clôturée par',
                       context={'no_create': True, 'no_create_edit': True})
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
    responsable_id     = fields.Many2one('hr.employee', string="Responsable de l'action",
                           context={'no_create': True, 'no_create_edit': True})


class PlanActionSmi(models.Model):
    _name = 'nc_management.plan_action_smi'
    _description = 'Plan Action Amelioration SMI'
    _order = 'name asc'

    name = fields.Char(string='Référence', required=True, copy=False,
                       readonly=True, default='New')
    nature = fields.Selection([
        ('nc_produit',     'NC Produit'),
        ('reclamation_pi', 'Réclamation Client ou PI'),
        ('environnement',  'Environnement'),
        ('sst',            'SST'),
    ], string='Nature', required=True)
    fnc_id = fields.Many2one('nc_management.nonconformity', string='FNC Liée')
    description = fields.Text(string='Brève description / Objectif amélioration')
    causes = fields.Text(string='Causes')
    action = fields.Text(string='Action')
    responsable_id = fields.Many2one('hr.employee', string='Responsable',
                       context={'no_create': True, 'no_create_edit': True})
    moyens = fields.Char(string='Moyens Nécessaires (matériels, financiers, humains)')
    duree_estimee = fields.Char(string='Durée Estimée')
    date_prevue = fields.Date(string='Date Prévue')
    date_lancement = fields.Date(string='Date de Lancement')
    date_realisation = fields.Date(string='Date de Réalisation')
    avancement = fields.Integer(string='État Avancement (%)', default=0)
    duree_reelle = fields.Char(string='Durée Réelle')
    critere_efficacite = fields.Text(string="Critère d'Efficacité")
    efficacite = fields.Selection([
        ('oui', 'OUI'),
        ('non', 'NON'),
    ], string='Efficacité')
    remarque = fields.Text(string='Remarque (si non efficace)')
    state = fields.Selection([
        ('draft',    'En cours'),
        ('done',     'Réalisé'),
        ('verified', 'Vérifié'),
    ], string='État', default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'nc_management.plan_action_smi') or 'New'
        return super(PlanActionSmi, self).create(vals)

    @api.onchange('nature')
    def _onchange_nature(self):
        self.fnc_id = False

    @api.multi
    def action_done(self):
        self.state = 'done'

    @api.multi
    def action_verify(self):
        self.state = 'verified'


class NcDashboard(models.Model):
    _name = 'nc_management.dashboard'
    _description = 'Dashboard'

    @api.model
    def get_plan_smi_stats(self):
        plan = self.env['nc_management.plan_action_smi']

        def get_cat(nature_val):
            recs = plan.search([('nature', '=', nature_val)])
            total = len(recs)
            if total == 0:
                return {'total': 0, 'efficace': 0, 'non_efficace': 0,
                        'realise_100': 0, 'realise_50plus': 0,
                        'realise_50moins': 0, 'taux': 0}
            efficace        = len(recs.filtered(lambda r: r.efficacite == 'oui'))
            non_efficace    = len(recs.filtered(lambda r: r.efficacite == 'non'))
            realise_100     = len(recs.filtered(lambda r: r.avancement == 100))
            realise_50plus  = len(recs.filtered(lambda r: 50 <= r.avancement < 100))
            realise_50moins = len(recs.filtered(lambda r: r.avancement < 50))
            taux = round(efficace / total * 100, 1)
            return {
                'total': total,
                'efficace': efficace,
                'non_efficace': non_efficace,
                'realise_100': realise_100,
                'realise_50plus': realise_50plus,
                'realise_50moins': realise_50moins,
                'taux': taux,
            }

        categories = [
            {'key': 'nc_produit',     'label': 'NC Produit',
             'data': get_cat('nc_produit')},
            {'key': 'reclamation_pi', 'label': 'Réclamation Client ou PI',
             'data': get_cat('reclamation_pi')},
            {'key': 'environnement',  'label': 'Environnement',
             'data': get_cat('environnement')},
            {'key': 'sst',            'label': 'SST',
             'data': get_cat('sst')},
        ]

        all_recs = plan.search([])
        total_all = len(all_recs)

        def proc_taux(nature_val):
            recs = plan.search([('nature', '=', nature_val)])
            if not recs:
                return 0
            return round(sum(r.avancement for r in recs) / len(recs), 1)

        processus = [
            {'label': 'Analyse et amélioration',
             'taux': round(sum(r.avancement for r in all_recs) / max(total_all, 1), 1)},
            {'label': 'Santé Sécurité Environnement',
             'taux': proc_taux('sst')},
            {'label': 'Process contrôle qualité',
             'taux': proc_taux('nc_produit')},
            {'label': 'Commercialisation / Réclamation',
             'taux': proc_taux('reclamation_pi')},
        ]

        return {
            'categories': categories,
            'processus': processus,
        }

    @api.model
    def get_efficacite_categorie(self, field_name):
        fnc = self.env['nc_management.nonconformity']
        fac = self.env['nc_management.corrective_action']

        fnc_ids = fnc.search([(field_name, '=', True)]).ids
        total = len(fnc_ids)

        if total == 0:
            return {'total': 0, 'efficace': 0, 'non_efficace': 0, 'taux': 0}

        efficace = fac.search_count([
            ('fnc_id', 'in', fnc_ids),
            ('actions_efficaces', '=', 'oui')
        ])
        non_efficace = fac.search_count([
            ('fnc_id', 'in', fnc_ids),
            ('actions_efficaces', '=', 'non')
        ])
        taux = round((efficace / total * 100), 1) if total > 0 else 0

        return {
            'total': total,
            'efficace': efficace,
            'non_efficace': non_efficace,
            'taux': taux,
        }

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
            'analyse_efficacite': {
                'reclamation_pi': self.get_efficacite_categorie('type_reclamation'),
                'nc_produit':     self.get_efficacite_categorie('type_nc_produit'),
                'environnement':  self.get_efficacite_categorie('type_environnement'),
                'sst':            self.get_efficacite_categorie('type_sst'),
            },
        }
