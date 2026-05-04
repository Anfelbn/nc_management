from datetime import date, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError

class NcType(models.Model):
    _name = 'nc_management.nc_type'
    _description = 'Type de Non-Conformité (Abréviation)'

    name = fields.Char(string='Produit/Abréviation', required=True)
    code = fields.Char(string='Code (Abréviation)', required=True)
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
    ], string='Catégorie', required=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Le code de l\'abréviation doit être unique !'),
    ]

class Nonconformity(models.Model):
    _name = 'nc_management.nonconformity'
    _description = 'Fiche de Non-Conformité'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ── En-tête ──────────────────────────────────────────────
    name = fields.Char(
        string='N° FNC', required=True, copy=False,
        default='New')
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
    def action_open_number_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Générer Numéro',
            'res_model': 'nc_management.number_generator_wizard',
            'view_mode': 'form',
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


class DocumentRevision(models.Model):
    _name = 'nc_management.document_revision'
    _description = 'Révision de Document'
    _order = 'revision_date desc, revision_number desc'

    doc_type = fields.Selection([
        ('fnc', 'Fiche de Non-Conformité (FNC)'),
        ('fac', 'Fiche d\'Action Corrective (FAC)'),
    ], string='Type de Document', required=True)
    revision_number = fields.Integer(string='N° Révision', required=True)
    revision_date = fields.Date(string='Date de Révision', required=True, default=fields.Date.today)
    description = fields.Text(string='Modification apportée')

    name = fields.Char(string='Révision', compute='_compute_name', store=True)

    @api.depends('doc_type', 'revision_number')
    def _compute_name(self):
        for rec in self:
            type_str = 'FNC' if rec.doc_type == 'fnc' else 'FAC'
            rec.name = "%s - Rev %02d" % (type_str, rec.revision_number)


class NcDashboard(models.Model):
    _name = 'nc_management.dashboard'
    _description = 'Dashboard'

    @api.model
    def get_plan_smi_stats(self):
        fnc = self.env['nc_management.nonconformity']
        fac = self.env['nc_management.corrective_action']

        def get_categorie(field_name):
            fnc_ids = fnc.search([(field_name, '=', True)]).ids
            total = len(fnc_ids)
            if total == 0:
                return {
                    'total': 0, 'efficace': 0, 'non_efficace': 0,
                    'realise_100': 0, 'realise_50plus': 0,
                    'realise_50moins': 0, 'taux': 0
                }
            fac_recs = fac.search([('fnc_id', 'in', fnc_ids)])
            efficace = len(fac_recs.filtered(
                lambda f: f.actions_efficaces == 'oui'))
            non_efficace = len(fac_recs.filtered(
                lambda f: f.actions_efficaces == 'non'))
            realise_100 = len(fac_recs.filtered(
                lambda f: f.state == 'closed'))
            realise_50plus = len(fac_recs.filtered(
                lambda f: f.state in ['verified', 'open']))
            realise_50moins = len(fac_recs.filtered(
                lambda f: f.state == 'draft'))
            taux = round((efficace / total * 100), 1) if total > 0 else 0
            return {
                'total': total,
                'efficace': efficace,
                'non_efficace': non_efficace,
                'realise_100': realise_100,
                'realise_50plus': realise_50plus,
                'realise_50moins': realise_50moins,
                'taux': taux
            }

        categories = [
            {'label': 'Réclamation PI',
             'data': get_categorie('type_reclamation')},
            {'label': 'NC produit',
             'data': get_categorie('type_nc_produit')},
            {'label': 'Environnement',
             'data': get_categorie('type_environnement')},
            {'label': 'SST',
             'data': get_categorie('type_sst')},
        ]

        total_fac = fac.search_count([]) or 1
        closed_fac = fac.search_count([('state', '=', 'closed')])

        def taux_proc(field_name):
            t = fnc.search_count([(field_name, '=', True)]) or 1
            c = fnc.search_count([
                (field_name, '=', True),
                ('state', '=', 'closed')])
            return round(c / t * 100, 0)

        def taux_multi(fields_list):
            domain = ['|'] * (len(fields_list) - 1)
            for f in fields_list:
                domain.append((f, '=', True))
            t = fnc.search_count(domain) or 1
            d2 = domain + [('state', '=', 'closed')]
            c = fnc.search_count(d2)
            return round(c / t * 100, 0)

        processus = [
            {'label': 'Analyse et amélioration',
             'taux': round(closed_fac / total_fac * 100, 0)},
            {'label': 'Process contrôle qualité',
             'taux': taux_proc('type_nc_produit')},
            {'label': 'Santé sécurité environnement',
             'taux': taux_multi(['type_sst', 'type_environnement'])},
            {'label': 'Commercialisation / Réclamation',
             'taux': taux_proc('type_reclamation')},
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
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta

        fnc = self.env['nc_management.nonconformity']
        fac = self.env['nc_management.corrective_action']

        # ── FNC counters ──
        total_fnc    = fnc.search_count([])
        fnc_cours    = fnc.search_count([('state','=','in_progress')])
        fnc_envoyes  = fnc.search_count([('state','=','submitted')])
        fnc_closed   = fnc.search_count([('state','=','closed')])
        taux_cloture = round(fnc_closed / total_fnc * 100, 1) if total_fnc else 0

        # FNC en retard > 7 jours
        limit7 = str(date.today() - timedelta(days=7))
        fnc_retard_recs = fnc.search_read(
            [('state','=','in_progress'), ('date','<=',limit7)],
            ['name','direction_id','service_dpt','date'], limit=10)
        fnc_retard = len(fnc_retard_recs)

        # FNC reçues des autres services (submitted_by != current user dept)
        fnc_recues = fnc.search_count([('state','not in',['draft'])])

        # FNC par département
        dept_counts = {}
        fnc_all = fnc.search([('state','not in',['draft'])])
        for rec in fnc_all:
            dept = rec.direction_id.name if rec.direction_id else 'Autres'
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        dept_list = sorted(dept_counts.items(), key=lambda x: x[1], reverse=True)[:6]

        # FNC par type
        type_counts = {
            'NC Produit':   fnc.search_count([('type_nc_produit','=',True)]),
            'Réclamation':  fnc.search_count([('type_reclamation','=',True)]),
            'SST':          fnc.search_count([('type_sst','=',True)]),
            'Environnement':fnc.search_count([('type_environnement','=',True)]),
            'Audit':        fnc.search_count([('type_audit','=',True)]),
            'Autres':       fnc.search_count([('type_autre','=',True)]),
        }

        # ── FAC counters ──
        total_fac   = fac.search_count([])
        fac_open    = fac.search_count([('state','=','open')])
        fac_verif   = fac.search_count([('state','=','verified')])
        fac_closed  = fac.search_count([('state','=','closed')])
        fac_efficace = fac.search_count([('actions_efficaces','=','oui')])
        taux_eff    = round(fac_efficace / total_fac * 100, 1) if total_fac else 0

        # FAC en retard (open > 7 jours)
        fac_retard_recs = fac.search_read(
            [('state','in',['open','verified']),
             ('date','<=',limit7)],
            ['name','direction_id','date_cloture','state'], limit=10)
        fac_retard = len(fac_retard_recs)

        # FAC à clôturer avec urgence
        fac_a_cloturer = []
        for f in fac.search([('state','in',['open','verified'])],
                            order='date asc', limit=8):
            if f.date:
                from datetime import datetime as dt
                f_date = dt.strptime(str(f.date), '%Y-%m-%d').date()
                days_open = (date.today() - f_date).days
            else:
                days_open = 0
            if days_open > 7:
                badge = 'red'
                label = 'Retard %dj' % days_open
            elif days_open > 3:
                badge = 'orange'
                label = 'Echeance proche'
            else:
                badge = 'green'
                label = 'Dans %dj' % (7 - days_open)
            fac_a_cloturer.append({
                'name': f.name,
                'dept': f.direction_id.name if f.direction_id else '',
                'date': str(f.date) if f.date else '',
                'days': days_open,
                'badge': badge,
                'label': label,
            })

        # FAC à approuver reçues
        fac_recues_count = fac.search_count([('state','=','verified')])

        # ── Evolution mensuelle 6 mois ──
        monthly_fnc = []
        monthly_fac = []
        for i in range(5, -1, -1):
            d = date.today() - relativedelta(months=i)
            m_start = d.replace(day=1)
            m_end = (d + relativedelta(months=1)).replace(day=1)
            count_fnc = fnc.search_count([
                ('date','>=',str(m_start)),
                ('date','<',str(m_end))])
            count_fac = fac.search_count([
                ('date','>=',str(m_start)),
                ('date','<',str(m_end))])
            monthly_fnc.append({
                'month': m_start.strftime('%b %Y'),
                'short': m_start.strftime('%b'),
                'count': count_fnc})
            monthly_fac.append({
                'month': m_start.strftime('%b %Y'),
                'short': m_start.strftime('%b'),
                'count': count_fac})

        # ── Etat global pourcentages ──
        pct_fnc_closed  = taux_cloture
        pct_fnc_cours   = round(fnc_cours / total_fnc * 100, 1) if total_fnc else 0
        pct_fac_eff     = taux_eff
        pct_fac_retard  = round(fac_retard / total_fac * 100, 1) if total_fac else 0
        pct_fnc_retard  = round(fnc_retard / total_fnc * 100, 1) if total_fnc else 0

        return {
            'fnc_total':      total_fnc,
            'fnc_cours':      fnc_cours,
            'fnc_envoyes':    fnc_envoyes,
            'fnc_closed':     fnc_closed,
            'fnc_retard':     fnc_retard,
            'fnc_retard_list': fnc_retard_recs,
            'fnc_recues':     fnc_recues,
            'taux_cloture':   taux_cloture,
            'dept_list':      dept_list,
            'type_counts':    type_counts,
            'fac_total':      total_fac,
            'fac_open':       fac_open,
            'fac_verif':      fac_verif,
            'fac_closed':     fac_closed,
            'fac_retard':     fac_retard,
            'fac_recues':     fac_recues_count,
            'taux_efficacite': taux_eff,
            'fac_a_cloturer': fac_a_cloturer,
            'monthly_fnc':    monthly_fnc,
            'monthly_fac':    monthly_fac,
            'pct_fnc_closed': pct_fnc_closed,
            'pct_fnc_cours':  pct_fnc_cours,
            'pct_fac_eff':    pct_fac_eff,
            'pct_fac_retard': pct_fac_retard,
            'pct_fnc_retard': pct_fnc_retard,
        }
