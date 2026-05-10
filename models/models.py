from datetime import date, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError


class HrDepartmentScaek(models.Model):
    _inherit = 'hr.department'

    scaek_level = fields.Selection([
        ('pdg',         'P-DG'),
        ('direction',   'Direction'),
        ('departement', 'Département'),
        ('service',     'Service'),
        ('section',     'Section'),
        ('equipe',      'Équipe'),
    ], string='Niveau hiérarchique')
    scaek_code = fields.Char(string='Code')


class HrJobScaek(models.Model):
    _inherit = 'hr.job'

    is_linked_to_pdg = fields.Boolean(
        string='Lié au P-DG',
        default=False,
        help='Ce poste reporte directement au P-DG '
             '(ex : Assistant, Secrétaire Général, Médecin…)',
    )



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
    direction_id  = fields.Many2one(
        'hr.department', string='Direction / Emetteur',
        domain=[('scaek_level', '=', 'direction')],
        context={'no_create': True, 'no_create_edit': True})
    department_id = fields.Many2one(
        'hr.department', string='Département',
        domain=[('scaek_level', '=', 'departement')],
        context={'no_create': True, 'no_create_edit': True})
    service_id    = fields.Many2one(
        'hr.department', string='Service',
        domain=[('scaek_level', '=', 'service')],
        context={'no_create': True, 'no_create_edit': True})
    section_id    = fields.Many2one(
        'hr.department', string='Section',
        domain=[('scaek_level', '=', 'section')],
        context={'no_create': True, 'no_create_edit': True})
    equipe_id     = fields.Many2one(
        'hr.department', string='Équipe',
        domain=[('scaek_level', '=', 'equipe')],
        context={'no_create': True, 'no_create_edit': True})
    service_dpt   = fields.Char(string='Sce / DPT')
    date          = fields.Date(string='Date', default=fields.Date.today)

    # ── Type de Non-Conformité ────────────────────────────────
    type_nc_produit        = fields.Boolean(string='NC Produit')
    type_audit             = fields.Boolean(string='Audit interne/Externe')
    type_audit_interne     = fields.Boolean(string='Audit interne')
    type_audit_externe     = fields.Boolean(string='Audit externe')
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

    @api.onchange('direction_id')
    def _onchange_direction_id(self):
        self.department_id = False
        self.service_id = False
        self.section_id = False
        self.equipe_id = False

    @api.onchange('department_id')
    def _onchange_department_id(self):
        self.service_id = False
        self.section_id = False
        self.equipe_id = False

    @api.onchange('service_id')
    def _onchange_service_id(self):
        self.section_id = False
        self.equipe_id = False

    @api.onchange('section_id')
    def _onchange_section_id(self):
        self.equipe_id = False


class CorrectiveAction(models.Model):
    _name = 'nc_management.corrective_action'
    _description = "Fiche d'Action Corrective"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ── En-tête ───────────────────────────────────────────────
    name         = fields.Char(
        string='N° FAC', required=True, copy=False,
        readonly=True, default='New')
    direction_id = fields.Many2one(
        'hr.department', string='Direction',
        domain=[('scaek_level', '=', 'direction')],
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

    @api.multi
    def action_next_stage(self):
        self.ensure_one()
        if self.state == 'draft':
            self.action_open()
        elif self.state == 'open':
            self.action_verify()
        elif self.state == 'verified':
            self.action_close()
        return True


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
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Référence', required=True, copy=False,
                       readonly=True, default='New')
    nature = fields.Selection([
        ('nc_produit',     'NC Produit'),
        ('reclamation_pi', 'Réclamation Client ou PI'),
        ('environnement',  'Environnement'),
        ('sst',            'SST'),
    ], string='Nature')
    fnc_id = fields.Many2one('nc_management.nonconformity', string='FNC Liée')
    direction_id = fields.Many2one(
        'hr.department',
        domain=[('scaek_level', '=', 'direction')],
        string='Direction',
        context={'no_create': True, 'no_create_edit': True}
    )
    department_id = fields.Many2one(
        'hr.department',
        domain=[('scaek_level', '=', 'departement')],
        string='Département',
        context={'no_create': True, 'no_create_edit': True}
    )
    service_id = fields.Many2one(
        'hr.department',
        domain=[('scaek_level', '=', 'service')],
        string='Service',
        context={'no_create': True, 'no_create_edit': True}
    )
    is_late = fields.Boolean(
        string='En retard',
        compute='_compute_is_late',
        store=True
    )
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
    ], string='Avancement', default='draft', track_visibility='onchange')

    # ── Cycle de vie RMQSE ────────────────────────────────────────
    submission_state = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('soumis',    'Soumis à la Responsable Qualité'),
        ('integre',   "Intégré au Plan d'Amélioration"),
        ('cloture',   'Plan clôturé'),
    ], string='État', default='brouillon', track_visibility='onchange')

    sent_to_rmqse = fields.Boolean('Envoyé à la Responsable Qualité',
                                   default=False, readonly=True)
    date_envoi    = fields.Datetime("Date d'envoi", readonly=True)
    sent_by       = fields.Many2one('res.users', 'Envoyé par', readonly=True)

    # ── Plan d'Action d'Amélioration SMI ─────────────────────────
    is_global      = fields.Boolean("Est un Plan d'Amélioration", default=False)
    global_plan_id = fields.Many2one(
        'nc_management.plan_action_smi',
        string="Plan d'Amélioration parent",
        domain=[('is_global', '=', True)],
        ondelete='set null',
        index=True,
    )
    mois_reception = fields.Date('Date de création')
    date_maj       = fields.Datetime("Dernière mise à jour", readonly=True)
    child_plan_ids = fields.One2many(
        'nc_management.plan_action_smi',
        'global_plan_id',
        string='Plans intégrés',
    )

    # ── Statistiques plan global (calculées) ──────────────────────
    nb_plans_integres = fields.Integer(
        'Nb plans intégrés', compute='_compute_global_stats')
    avancement_global = fields.Integer(
        'Avancement global (%)', compute='_compute_global_stats')
    nb_realises   = fields.Integer('Réalisés',   compute='_compute_global_stats')
    nb_en_cours   = fields.Integer('En cours',   compute='_compute_global_stats')
    nb_en_retard  = fields.Integer('En retard',  compute='_compute_global_stats')

    @api.depends('child_plan_ids.avancement', 'child_plan_ids.state',
                 'child_plan_ids.is_late')
    def _compute_global_stats(self):
        for rec in self:
            children = rec.child_plan_ids
            nb = len(children)
            rec.nb_plans_integres = nb
            rec.avancement_global = int(sum(c.avancement for c in children) / nb) if nb else 0
            rec.nb_realises  = sum(1 for c in children if c.state == 'done')
            rec.nb_en_cours  = sum(1 for c in children if c.state == 'draft')
            rec.nb_en_retard = sum(1 for c in children if c.is_late)

    @api.depends('date_prevue', 'state')
    def _compute_is_late(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_late = bool(
                rec.date_prevue and
                rec.date_prevue < today and
                rec.state != 'verified'
            )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            if vals.get('is_global'):
                from datetime import date as _date
                today = _date.today()
                vals['name'] = 'AMELIORATION-%02d-%04d' % (today.month, today.year)
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'nc_management.plan_action_smi') or 'New'
        return super(PlanActionSmi, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(PlanActionSmi, self).write(vals)
        if not self.env.context.get('_skip_date_maj') and 'date_maj' not in vals:
            plans_amelioration = self.filtered('is_global')
            if plans_amelioration:
                plans_amelioration.with_context(_skip_date_maj=True).write(
                    {'date_maj': fields.Datetime.now()})
        return res

    @api.onchange('nature')
    def _onchange_nature(self):
        self.fnc_id = False

    @api.onchange('direction_id')
    def _onchange_smi_direction_id(self):
        self.department_id = False
        self.service_id = False

    @api.onchange('department_id')
    def _onchange_smi_department_id(self):
        self.service_id = False

    @api.multi
    def action_done(self):
        self.state = 'done'

    @api.multi
    def action_verify(self):
        self.state = 'verified'

    @api.multi
    def action_envoyer_rmqse(self):
        self.ensure_one()
        if self.submission_state != 'brouillon':
            raise UserError("Ce plan a déjà été soumis à la Responsable Qualité.")
        if self.env.uid != self.create_uid.id:
            raise UserError("Seul le créateur peut soumettre ce plan.")

        self.write({
            'submission_state': 'soumis',
            'sent_to_rmqse': True,
            'date_envoi': fields.Datetime.now(),
            'sent_by': self.env.uid,
            'mois_reception': fields.Date.today(),
        })

        rmqse_group = self.env.ref(
            'nc_management.group_responsable_qualite', raise_if_not_found=False)
        if rmqse_group:
            partner_ids = rmqse_group.users.mapped('partner_id').ids
            self.message_post(
                body=(
                    "<p>Le plan d'action <strong>%s</strong> a été soumis à "
                    "la Responsable Qualité par <strong>%s</strong>.</p>"
                    "<p>Direction : %s</p>"
                ) % (
                    self.name,
                    self.env.user.name,
                    self.direction_id.name if self.direction_id else '-',
                ),
                partner_ids=partner_ids,
                message_type='notification',
                subtype='mail.mt_comment',
            )
        return True

    @api.multi
    def action_analyse_efficacite(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Analyse d'Efficacité — %s" % self.name,
            'res_model': 'nc_management.plan_action_smi',
            'view_mode': 'pivot,graph',
            'domain': [('global_plan_id', '=', self.id)],
            'context': {'search_default_group_state': 1},
        }

    @api.multi
    def action_consolider_tous(self):
        """Intègre TOUS les plans non encore rattachés à ce Plan d'Amélioration."""
        self.ensure_one()
        unlinked = self.search([
            ('is_global', '=', False),
            ('global_plan_id', '=', False),
            '|',
            ('create_uid', '=', self.env.uid),
            ('sent_to_rmqse', '=', True),
        ])
        unlinked.with_context(_skip_date_maj=True).write({
            'global_plan_id': self.id,
            'submission_state': 'integre',
        })

    @api.multi
    def action_cloturer_plan(self):
        """Clôture le plan actuel et crée automatiquement le suivant
        en y intégrant tous les plans créés/reçus après la date_maj courante."""
        self.ensure_one()
        if self.submission_state == 'cloture':
            raise UserError("Ce Plan d'Amélioration est déjà clôturé.")

        cutoff = self.date_maj or self.create_date

        # 1. Clôturer le plan actuel
        self.with_context(_skip_date_maj=True).write(
            {'submission_state': 'cloture'})

        # 2. Créer le nouveau Plan d'Amélioration
        new_plan = self.with_context(_skip_date_maj=True).create({
            'name': 'New',
            'is_global': True,
            'submission_state': 'brouillon',
            'mois_reception': fields.Date.today(),
            'description': "Plan d'Action d'Amélioration SMI",
        })

        # 3. Plans de la Responsable Qualité créés après cutoff
        mes_plans = self.search([
            ('is_global', '=', False),
            ('create_uid', '=', self.env.uid),
            ('create_date', '>', str(cutoff)),
            ('global_plan_id', '=', False),
        ])

        # 4. Plans reçus après cutoff
        plans_recus = self.search([
            ('is_global', '=', False),
            ('sent_to_rmqse', '=', True),
            ('date_envoi', '>', str(cutoff)),
            ('global_plan_id', '=', False),
        ])

        (mes_plans | plans_recus).with_context(_skip_date_maj=True).write({
            'global_plan_id': new_plan.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.plan_action_smi',
            'res_id': new_plan.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'nc_management.view_plan_smi_form_global').id,
            'target': 'current',
        }

    @api.model
    def _auto_create_global_plan(self):
        from datetime import date as _date
        from dateutil.relativedelta import relativedelta

        today = _date.today()
        first_of_current = today.replace(day=1)
        first_of_last = first_of_current - relativedelta(months=1)
        ref = 'GLOBAL-%02d-%04d' % (first_of_last.month, first_of_last.year)

        if self.search([('is_global', '=', True), ('name', '=', ref)], limit=1):
            return True

        submitted = self.search([
            ('submission_state', '=', 'soumis'),
            ('is_global', '=', False),
            ('mois_reception', '>=', first_of_last.strftime('%Y-%m-%d')),
            ('mois_reception', '<',  first_of_current.strftime('%Y-%m-%d')),
        ])
        if not submitted:
            return True

        global_plan = self.create({
            'name': ref,
            'is_global': True,
            'mois_reception': first_of_last.strftime('%Y-%m-%d'),
            'submission_state': 'brouillon',
            'description': 'Plan Global consolidé — %02d/%04d' % (
                first_of_last.month, first_of_last.year),
        })
        submitted.write({
            'global_plan_id': global_plan.id,
            'submission_state': 'integre',
        })
        return True


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

    revision_number_link = fields.Html(string='N° Révision', compute='_compute_revision_number_link')

    @api.depends('revision_number', 'doc_type')
    def _compute_revision_number_link(self):
        for rec in self:
            # Génère un lien HTML vers le rapport PDF d'Odoo
            url = '/report/pdf/nc_management.report_revision_template/%s' % rec.id
            rec.revision_number_link = '<a href="%s" target="_blank" style="font-weight:bold; color:#00A09D;">%s</a>' % (url, rec.revision_number)

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
    def get_stats(self, period=None):
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        import calendar as cal_mod

        fnc = self.env['nc_management.nonconformity']
        fac = self.env['nc_management.corrective_action']
        plan = self.env['nc_management.plan_action_smi']
        today = date.today()
        period_months = {
            '1m': 1,
            '6m': 6,
            '1y': 12,
        }.get(period or '1m', 1)
        period_end = (today.replace(day=1) + relativedelta(months=1))
        period_start = today.replace(day=1) - relativedelta(months=period_months - 1)

        fnc_period_domain = [
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
        ]
        fac_period_domain = [
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
        ]
        received_fnc_period_domain = fnc_period_domain + [
            ('state', '!=', 'draft'),
            '|', ('submitted_by_id', '=', False),
                 ('submitted_by_id', '!=', self.env.uid),
        ]
        received_fnc_ids = fnc.search(received_fnc_period_domain).ids
        fac_received_period_domain = fac_period_domain + [
            ('fnc_id', 'in', received_fnc_ids),
        ]

        # Domaine FNC créées par RMQSE (espace RMQSE — section Évolution)
        own_fnc_domain = [
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
            ('create_uid', '=', self.env.uid),
        ]
        # Domaine combiné : RMQSE créé + audits internes/externes (pour Total FNC/FAC)
        combined_fnc_domain = [
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
            '|', '|', ('create_uid', '=', self.env.uid),
                      ('type_audit_interne', '=', True),
                 ('type_audit_externe', '=', True),
        ]
        combined_fnc_ids = fnc.search(combined_fnc_domain).ids
        combined_fac_domain = [
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
            ('fnc_id', 'in', combined_fnc_ids),
        ]

        # ── FNC counters (combiné : RMQSE créé + audits) ──
        total_fnc     = len(combined_fnc_ids)
        fnc_cours     = fnc.search_count(combined_fnc_domain + [('state','=','in_progress')])
        fnc_envoyes   = fnc.search_count(combined_fnc_domain + [('state','=','submitted')])
        fnc_closed    = fnc.search_count(combined_fnc_domain + [('state','=','closed')])
        fnc_validated = fnc.search_count(combined_fnc_domain + [('state','=','validated')])
        taux_cloture  = round(fnc_validated / total_fnc * 100, 1) if total_fnc else 0
        fnc_brouillon = fnc.search_count(combined_fnc_domain + [('state','=','draft')])
        # Audit split interne / externe
        fnc_audit_interne = fnc.search_count(combined_fnc_domain + [('type_audit_interne','=',True)])
        fnc_audit_externe = fnc.search_count(combined_fnc_domain + [('type_audit_externe','=',True)])

        # FNC en retard > 7 jours (créées par RMQSE, in_progress)
        limit7 = str(today - timedelta(days=7))
        fnc_retard_recs = fnc.search_read([
            ('state', '=', 'in_progress'),
            ('date', '<=', limit7),
            ('create_uid', '=', self.env.uid),
        ], ['name', 'direction_id', 'service_dpt', 'date'], limit=10)
        fnc_retard = len(fnc_retard_recs)

        # FNC reçues des autres services (submitted_by != current user dept)
        fnc_recues = total_fnc

        # FNC par département
        dept_counts = {}
        dept_fac_counts = {}
        fnc_all = fnc.search(received_fnc_period_domain)
        for rec in fnc_all:
            dept = rec.direction_id.name if rec.direction_id else 'Autres'
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        for rec in fac.search(fac_received_period_domain):
            dept = rec.direction_id.name if rec.direction_id else 'Autres'
            dept_fac_counts[dept] = dept_fac_counts.get(dept, 0) + 1
        dept_names = set(dept_counts.keys()) | set(dept_fac_counts.keys())
        dept_list = []
        for dept_name in dept_names:
            dept_list.append({
                'name': dept_name,
                'fnc_count': dept_counts.get(dept_name, 0),
                'fac_count': dept_fac_counts.get(dept_name, 0),
            })
        dept_list = sorted(
            dept_list, key=lambda x: x['fnc_count'] + x['fac_count'],
            reverse=True)[:6]
        max_fnc = max([d['fnc_count'] for d in dept_list] or [1]) or 1
        max_fac = max([d['fac_count'] for d in dept_list] or [1]) or 1
        for d in dept_list:
            d['pct_fnc'] = round(d['fnc_count'] / max_fnc * 100)
            d['pct_fac'] = round(d['fac_count'] / max_fac * 100)

        # FNC par type
        raw_type_counts = {
            'nc_produit': fnc.search_count(received_fnc_period_domain + [('type_nc_produit','=',True)]),
            'reclamation': fnc.search_count(received_fnc_period_domain + [('type_reclamation','=',True)]),
            'sst': fnc.search_count(received_fnc_period_domain + [('type_sst','=',True)]),
            'environnement': fnc.search_count(received_fnc_period_domain + [('type_environnement','=',True)]),
            'audit': fnc.search_count(received_fnc_period_domain + [('type_audit','=',True)]),
            'autres': fnc.search_count(received_fnc_period_domain + [('type_autre','=',True)]),
        }
        total_type = sum(raw_type_counts.values()) or 1
        type_counts = dict(
            (k, int(round(v / total_type * 100)))
            for k, v in raw_type_counts.items())

        def _type_percentages(records):
            counts = {
                'nc_produit': 0,
                'reclamation': 0,
                'sst': 0,
                'environnement': 0,
                'audit': 0,
                'autres': 0,
            }
            for rec in records:
                if rec.type_nc_produit:
                    counts['nc_produit'] += 1
                if rec.type_reclamation:
                    counts['reclamation'] += 1
                if rec.type_sst:
                    counts['sst'] += 1
                if rec.type_environnement:
                    counts['environnement'] += 1
                if rec.type_audit:
                    counts['audit'] += 1
                if rec.type_autre:
                    counts['autres'] += 1
            total = sum(counts.values()) or 1
            return dict((k, int(round(v / total * 100))) for k, v in counts.items())

        direction_recs = self.env['hr.department'].search(
            [('scaek_level', '=', 'direction')], order='name asc')
        direction_stats = []
        max_dir_fnc = 1
        max_dir_fac = 1
        for direction in direction_recs:
            dir_fnc = fnc.search(received_fnc_period_domain + [
                ('direction_id', '=', direction.id),
            ])
            dir_fac = fac.search(fac_received_period_domain + [
                ('direction_id', '=', direction.id),
            ])
            dir_fac_fnc = dir_fac.mapped('fnc_id')
            fnc_count = len(dir_fnc)
            fac_count = len(dir_fac)
            max_dir_fnc = max(max_dir_fnc, fnc_count)
            max_dir_fac = max(max_dir_fac, fac_count)
            direction_stats.append({
                'id': direction.id,
                'name': direction.name,
                'fnc_count': fnc_count,
                'fac_count': fac_count,
                'fnc_types': _type_percentages(dir_fnc),
                'fac_types': _type_percentages(dir_fac_fnc),
            })
        for d in direction_stats:
            d['pct_fnc'] = round(d['fnc_count'] / max_dir_fnc * 100)
            d['pct_fac'] = round(d['fac_count'] / max_dir_fac * 100)

        # ── FAC counters (combinées : liées aux FNC RMQSE + audits) ──
        total_fac          = fac.search_count(combined_fac_domain)
        fac_open           = fac.search_count(combined_fac_domain + [('state','=','open')])
        fac_verif          = fac.search_count(combined_fac_domain + [('state','=','verified')])
        fac_closed         = fac.search_count(combined_fac_domain + [('state','=','closed')])
        fac_brouillon      = fac.search_count(combined_fac_domain + [('state','=','draft')])
        fac_efficace       = fac.search_count(combined_fac_domain + [('actions_efficaces','=','oui')])
        taux_eff           = round(fac_efficace / total_fac * 100, 1) if total_fac else 0
        taux_validation_fac = round(fac_verif  / total_fac * 100, 1) if total_fac else 0
        taux_cloture_fac   = round(fac_closed  / total_fac * 100, 1) if total_fac else 0
        # FAC audit split
        fac_audit_interne  = fac.search_count(combined_fac_domain + [('fnc_id.type_audit_interne','=',True)])
        fac_audit_externe  = fac.search_count(combined_fac_domain + [('fnc_id.type_audit_externe','=',True)])
        audit_interne_total = fnc_audit_interne + fac_audit_interne
        audit_externe_total = fnc_audit_externe + fac_audit_externe
        fac_submitted = fac.search_count(combined_fac_domain + [
            ('state', '=', 'draft'),
            ('fnc_id.state', 'in', ['submitted', 'in_progress']),
        ])

        # FAC en retard (ouvertes > 7 jours — tout le système)
        fac_retard_recs = fac.search_read(
            [('state', 'in', ['open', 'verified']),
             ('date', '<=', limit7)],
            ['name', 'direction_id', 'date_cloture', 'state'], limit=10)
        fac_retard = len(fac_retard_recs)

        # FAC à clôturer avec urgence (toutes FAC du système — RMQSE clôture tout)
        fac_a_cloturer = []
        for f in fac.search([('state', 'in', ['open', 'verified'])],
                            order='date asc', limit=8):
            if f.date:
                from datetime import datetime as dt
                f_date = dt.strptime(str(f.date), '%Y-%m-%d').date()
                days_open = (today - f_date).days
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
        fac_recues_count = fac.search_count(fac_received_period_domain + [('state','=','verified')])

        # ── Evolution mensuelle 6 mois — FNC/FAC créées par RMQSE uniquement ──
        monthly_fnc = []
        monthly_fac = []
        fr_months = ['Jan','Fév','Mar','Avr','Mai','Jui','Jul','Aoû','Sep','Oct','Nov','Déc']
        monthly_labels = []
        for i in range(5, -1, -1):
            d = today - relativedelta(months=i)
            m_start = d.replace(day=1)
            m_end = (d + relativedelta(months=1)).replace(day=1)
            m_fnc_recs = fnc.search([
                ('date', '>=', str(m_start)),
                ('date', '<', str(m_end)),
                ('create_uid', '=', self.env.uid),
            ])
            m_fnc_ids = m_fnc_recs.ids
            count_fac = fac.search_count([
                ('date', '>=', str(m_start)),
                ('date', '<', str(m_end)),
                ('fnc_id', 'in', m_fnc_ids),
            ])
            monthly_labels.append(fr_months[m_start.month - 1])
            monthly_fnc.append(len(m_fnc_recs))
            monthly_fac.append(count_fac)

        # ── Etat global pourcentages ──
        pct_fnc_closed  = taux_cloture
        pct_fnc_cours   = round(fnc_cours / total_fnc * 100, 1) if total_fnc else 0
        pct_fac_eff     = taux_eff
        pct_fac_retard  = round(fac_retard / total_fac * 100, 1) if total_fac else 0
        pct_fnc_retard  = round(fnc_retard / total_fnc * 100, 1) if total_fnc else 0

        result = {
            'fnc_total':          total_fnc,
            'fnc_cours':          fnc_cours,
            'fnc_envoyes':        fnc_envoyes,
            'fnc_closed':         fnc_closed,
            'fnc_validated':      fnc_validated,
            'fnc_brouillon':      fnc_brouillon,
            'fnc_audit_interne':  fnc_audit_interne,
            'fnc_audit_externe':  fnc_audit_externe,
            'fnc_retard':         fnc_retard,
            'fnc_retard_list':    fnc_retard_recs,
            'fnc_recues':         fnc_recues,
            'taux_cloture':       taux_cloture,
            'dept_list':          dept_list,
            'type_counts':        type_counts,
            'fac_total':          total_fac,
            'fac_open':           fac_open,
            'fac_verif':          fac_verif,
            'fac_closed':         fac_closed,
            'fac_brouillon':      fac_brouillon,
            'fac_audit_interne':   fac_audit_interne,
            'fac_audit_externe':   fac_audit_externe,
            'audit_interne_total': audit_interne_total,
            'audit_externe_total': audit_externe_total,
            'fac_submitted':       fac_submitted,
            'fac_retard':         fac_retard,
            'fac_recues':         fac_recues_count,
            'taux_efficacite':    taux_eff,
            'taux_validation_fac': taux_validation_fac,
            'taux_cloture_fac':   taux_cloture_fac,
            'fac_a_cloturer':     fac_a_cloturer,
            'monthly_fnc':        monthly_fnc,
            'monthly_fac':        monthly_fac,
            'pct_fnc_closed':     pct_fnc_closed,
            'pct_fnc_cours':      pct_fnc_cours,
            'pct_fac_eff':        pct_fac_eff,
            'pct_fac_retard':     pct_fac_retard,
            'pct_fnc_retard':     pct_fnc_retard,
        }

        # ── Additional dashboard data ──
        result['today'] = today.strftime('%d/%m/%Y')
        result['period'] = period or '1m'
        result['period_start'] = period_start.strftime('%Y-%m-%d')
        result['period_end'] = (period_end - timedelta(days=1)).strftime('%Y-%m-%d')
        result['direction_stats'] = direction_stats
        result['scope_totals'] = {
            'direction': {
                'fnc': sum([d['fnc_count'] for d in direction_stats]),
                'fac': sum([d['fac_count'] for d in direction_stats]),
            },
            'department': {
                'fnc': sum([d['fnc_count'] for d in dept_list]),
                'fac': sum([d['fac_count'] for d in dept_list]),
            },
            'service': {
                'fnc': fnc.search_count(received_fnc_period_domain + [('service_dpt', '!=', False)]),
                'fac': fac.search_count(fac_received_period_domain + [('fnc_id.service_dpt', '!=', False)]),
            },
        }
        result['calendar_year'] = today.year
        result['calendar_month'] = today.month
        result['monthly_labels'] = monthly_labels

        result['fnc_audit'] = fnc.search_count(combined_fnc_domain + [('type_audit', '=', True)])
        result['fac_audit'] = fac.search_count(combined_fac_domain + [('fnc_id.type_audit', '=', True)])

        # Totaux globaux (tout le système) pour l'en-tête du graphique direction
        result['global_fnc_total'] = fnc.search_count([
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
        ])
        result['global_fac_total'] = fac.search_count([
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
        ])

        # Diagramme global : toutes FNC/FAC du système (tous espaces/modules)
        monthly_fnc_global = []
        monthly_fac_global = []
        for i in range(5, -1, -1):
            d = today - relativedelta(months=i)
            d_start = d.replace(day=1)
            d_end = (d + relativedelta(months=1)).replace(day=1)
            monthly_fnc_global.append(fnc.search_count([
                ('date', '>=', d_start.strftime('%Y-%m-%d')),
                ('date', '<', d_end.strftime('%Y-%m-%d')),
            ]))
            monthly_fac_global.append(fac.search_count([
                ('date', '>=', d_start.strftime('%Y-%m-%d')),
                ('date', '<', d_end.strftime('%Y-%m-%d')),
            ]))
        result['monthly_fnc_global'] = monthly_fnc_global
        result['monthly_fac_global'] = monthly_fac_global

        calendar_events = {}
        received_by_date = {}
        fnc_this_month = fnc.search(received_fnc_period_domain)
        fac_this_month = fac.search(fac_received_period_domain)
        for fnc_rec in fnc_this_month:
            k = str(fnc_rec.date)[:10]
            if k not in calendar_events:
                calendar_events[k] = {'fnc': False, 'fac': False, 'plan': False}
            calendar_events[k]['fnc'] = True
        for fac_rec in fac_this_month:
            k = str(fac_rec.date)[:10]
            if k not in calendar_events:
                calendar_events[k] = {'fnc': False, 'fac': False, 'plan': False}
            calendar_events[k]['fac'] = True
        plan_domain = [('fnc_id', 'in', received_fnc_ids), '|',
            '&', ('date_lancement', '>=', period_start.strftime('%Y-%m-%d')),
                 ('date_lancement', '<', period_end.strftime('%Y-%m-%d')),
            '&', ('date_lancement', '=', False),
                 '&', ('date_prevue', '>=', period_start.strftime('%Y-%m-%d')),
                      ('date_prevue', '<', period_end.strftime('%Y-%m-%d'))]
        plan_this_period = plan.search(plan_domain)
        for plan_rec in plan_this_period:
            plan_date = plan_rec.date_lancement or plan_rec.date_prevue
            if not plan_date:
                continue
            k = str(plan_date)[:10]
            if k not in calendar_events:
                calendar_events[k] = {'fnc': False, 'fac': False, 'plan': False}
            calendar_events[k]['plan'] = True
        result['calendar_events'] = calendar_events

        fac_a_cloturer_list = []
        for fac_rec in fac.search([('state', 'in', ['open', 'verified'])],
                                  order='date asc', limit=8):
            delta = 0
            if fac_rec.date:
                delta = (today - fields.Date.from_string(fac_rec.date)).days
            fac_a_cloturer_list.append({
                'id': fac_rec.id,
                'name': fac_rec.name,
                'department': fac_rec.direction_id.name if fac_rec.direction_id else '',
                'days': delta,
                'state': fac_rec.state,
            })
        result['fac_a_cloturer'] = fac_a_cloturer_list

        def _fnc_type_label(fnc_rec):
            labels = []
            if fnc_rec.type_nc_produit:
                labels.append('NC Produit')
            if fnc_rec.type_reclamation:
                labels.append('Réclamation')
            if fnc_rec.type_sst:
                labels.append('SST')
            if fnc_rec.type_environnement:
                labels.append('Environnement')
            if fnc_rec.type_audit:
                labels.append('Audit')
            if fnc_rec.type_autre:
                labels.append('Autre')
            return ', '.join(labels) or 'NC'

        def _initials(employee):
            name = employee.name if employee else 'XX'
            return ''.join([w[0].upper() for w in name.split()[:2]]) or 'XX'

        # FNC en retard alertes : créées par RMQSE, in_progress > 7 jours
        fnc_retard_list = []
        for fnc_rec in fnc.search([
            ('state', '=', 'in_progress'),
            ('date', '<=', limit7),
            ('create_uid', '=', self.env.uid),
        ], limit=10):
            delta = 0
            if fnc_rec.date:
                delta = (today - fields.Date.from_string(fnc_rec.date)).days
            fnc_retard_list.append({
                'id': fnc_rec.id,
                'name': fnc_rec.name,
                'department': fnc_rec.direction_id.name if fnc_rec.direction_id else '',
                'days': delta,
                'type': _fnc_type_label(fnc_rec),
            })
        result['fnc_retard_list'] = fnc_retard_list

        def _date_label(value):
            return fields.Date.from_string(value).strftime('%d/%m/%Y') if value else ''

        def _append_received(day_key, item):
            if day_key not in received_by_date:
                received_by_date[day_key] = []
            received_by_date[day_key].append(item)

        received_docs = []
        for fnc_rec in fnc.search(received_fnc_period_domain,
                                  order='date desc, id desc', limit=20):
            responsible = fnc_rec.assigned_to_id or fnc_rec.responsable_action_id
            submitter = fnc_rec.submitted_by_id
            item = {
                'id': fnc_rec.id,
                'name': fnc_rec.name,
                'type': _fnc_type_label(fnc_rec),
                'kind': 'FNC',
                'badge': 'blue',
                'model': 'nc_management.nonconformity',
                'department': fnc_rec.direction_id.name if fnc_rec.direction_id else '',
                'responsible': responsible.name if responsible else '',
                'date': _date_label(fnc_rec.date),
                'initials': _initials(responsible),
                'submitted_by_partner_id': submitter.partner_id.id if submitter else None,
                'submitted_by_name': submitter.name if submitter else '',
            }
            received_docs.append(item)
            if fnc_rec.date:
                _append_received(str(fnc_rec.date)[:10], item)

        for fac_rec in fac.search(fac_received_period_domain, order='date desc, id desc', limit=20):
            responsible = fac_rec.responsable_actions_id
            fnc_submitter = fac_rec.fnc_id.submitted_by_id if fac_rec.fnc_id else None
            item = {
                'id': fac_rec.id,
                'name': fac_rec.name,
                'type': 'Action corrective',
                'kind': 'FAC',
                'badge': 'red',
                'model': 'nc_management.corrective_action',
                'department': fac_rec.direction_id.name if fac_rec.direction_id else '',
                'responsible': responsible.name if responsible else '',
                'date': _date_label(fac_rec.date),
                'initials': _initials(responsible),
                'fnc_id': fac_rec.fnc_id.id if fac_rec.fnc_id else None,
                'state': fac_rec.state,
                'submitted_by_partner_id': fnc_submitter.partner_id.id if fnc_submitter else None,
                'submitted_by_name': fnc_submitter.name if fnc_submitter else '',
            }
            received_docs.append(item)
            if fac_rec.date:
                _append_received(str(fac_rec.date)[:10], item)

        for plan_rec in plan_this_period:
            plan_date = plan_rec.date_lancement or plan_rec.date_prevue
            responsible = plan_rec.responsable_id
            item = {
                'id': plan_rec.id,
                'name': plan_rec.name,
                'type': dict(plan_rec._fields['nature'].selection).get(plan_rec.nature, 'Plan action'),
                'kind': 'Plan',
                'badge': 'purple',
                'model': 'nc_management.plan_action_smi',
                'department': plan_rec.fnc_id.direction_id.name if plan_rec.fnc_id and plan_rec.fnc_id.direction_id else '',
                'responsible': responsible.name if responsible else '',
                'date': _date_label(plan_date),
                'initials': _initials(responsible),
            }
            received_docs.append(item)
            if plan_date:
                _append_received(str(plan_date)[:10], item)

        received_docs = sorted(
            received_docs,
            key=lambda x: fields.Date.from_string(x['date'].split('/')[2] + '-' + x['date'].split('/')[1] + '-' + x['date'].split('/')[0]) if x.get('date') else date.min,
            reverse=True)[:10]
        result['received_docs'] = received_docs
        result['received_by_date'] = received_by_date
        result['fnc_recues'] = [d for d in received_docs if d['kind'] == 'FNC']
        result['fac_recues'] = [d for d in received_docs if d['kind'] == 'FAC']

        return result

    @api.model
    def get_direction_details(self, direction_id, period=None):
        from dateutil.relativedelta import relativedelta

        fnc = self.env['nc_management.nonconformity']
        fac = self.env['nc_management.corrective_action']
        today = date.today()
        period_months = {'1m': 1, '6m': 6, '1y': 12}.get(period or '1m', 1)
        period_end = today.replace(day=1) + relativedelta(months=1)
        period_start = today.replace(day=1) - relativedelta(months=period_months - 1)

        base_fnc = [
            ('date', '>=', str(period_start)),
            ('date', '<', str(period_end)),
            ('state', '!=', 'draft'),
            '|', ('submitted_by_id', '=', False),
                 ('submitted_by_id', '!=', self.env.uid),
            ('direction_id', '=', direction_id),
        ]
        base_fac = [
            ('date', '>=', str(period_start)),
            ('date', '<', str(period_end)),
        ]

        def _pct(recs):
            counts = {k: 0 for k in ['nc_produit','reclamation','sst','environnement','audit','autres']}
            for r in recs:
                if r.type_nc_produit: counts['nc_produit'] += 1
                if r.type_reclamation: counts['reclamation'] += 1
                if r.type_sst: counts['sst'] += 1
                if r.type_environnement: counts['environnement'] += 1
                if r.type_audit: counts['audit'] += 1
                if r.type_autre: counts['autres'] += 1
            total = sum(counts.values()) or 1
            return {k: int(round(v / total * 100)) for k, v in counts.items()}

        dir_fnc_recs = fnc.search(base_fnc)
        dir_fnc_ids = dir_fnc_recs.ids
        dir_fac_recs = fac.search(base_fac + [('fnc_id', 'in', dir_fnc_ids)])

        departments = self.env['hr.department'].search([
            ('scaek_level', '=', 'departement'),
            ('parent_id', '=', direction_id),
        ], order='name asc')

        dept_data = []
        for dept in departments:
            d_fnc = fnc.search(base_fnc + [('department_id', '=', dept.id)])
            d_fnc_ids = d_fnc.ids
            d_fac = fac.search(base_fac + [('fnc_id', 'in', d_fnc_ids)])

            services = self.env['hr.department'].search([
                ('scaek_level', '=', 'service'),
                ('parent_id', '=', dept.id),
            ], order='name asc')

            svc_data = []
            for svc in services:
                s_fnc = fnc.search(base_fnc + [('service_id', '=', svc.id)])
                s_fnc_ids = s_fnc.ids
                s_fac = fac.search(base_fac + [('fnc_id', 'in', s_fnc_ids)])
                svc_data.append({
                    'id': svc.id,
                    'name': svc.name,
                    'fnc_count': len(s_fnc),
                    'fac_count': len(s_fac),
                    'fnc_types': _pct(s_fnc),
                    'fac_types': _pct(s_fac.mapped('fnc_id')),
                })

            dept_data.append({
                'id': dept.id,
                'name': dept.name,
                'fnc_count': len(d_fnc),
                'fac_count': len(d_fac),
                'fnc_types': _pct(d_fnc),
                'fac_types': _pct(d_fac.mapped('fnc_id')),
                'services': svc_data,
            })

        return {
            'direction_id': direction_id,
            'fnc_count': len(dir_fnc_recs),
            'fac_count': len(dir_fac_recs),
            'fnc_types': _pct(dir_fnc_recs),
            'fac_types': _pct(dir_fac_recs.mapped('fnc_id')),
            'departments': dept_data,
        }
