from datetime import date, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


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
        ('type_audit_interne', 'Audit Interne'),
        ('type_audit_externe', 'Audit Externe'),
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
    service_dpt       = fields.Char(string='Sce / DPT')
    sce_dpt_computed  = fields.Char(
        string='Sce / DPT (calculé)',
        compute='_compute_sce_dpt', store=False)
    date          = fields.Date(string='Date', default=fields.Date.today)

    @api.depends('service_id', 'department_id')
    def _compute_sce_dpt(self):
        for rec in self:
            parts = []
            if rec.service_id:
                parts.append(rec.service_id.name)
            if rec.department_id:
                parts.append(rec.department_id.name)
            rec.sce_dpt_computed = ' / '.join(parts) if parts else ''

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
    fac_ids       = fields.One2many('nc_management.corrective_action', 'fnc_id', string="Fiches d'action liées")
    fac_reference = fields.Many2one(
        'nc_management.corrective_action',
        string="N° Fiche d'action",
        compute='_compute_fac_reference',
        store=True,
    )
    # Numéro FAC affiché en texte : visible par tous y compris le créateur FNC
    fac_number_display = fields.Char(
        string="N° FAC",
        compute='_compute_fac_number_display',
    )
    # True si l'utilisateur courant peut accéder à la FAC (lien cliquable)
    can_access_fac = fields.Boolean(
        compute='_compute_can_access_fac',
    )
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
    current_handler_uid = fields.Many2one(
        'res.users', string='Destinataire courant', copy=False)
    submitted_by_id = fields.Many2one(
        'res.users', string='Soumis par',
        readonly=True)
    validated_by_id = fields.Many2one(
        'hr.employee', string='Validé par (Sup. Hiérarchique)',
        context={'no_create': True, 'no_create_edit': True})

    # ── Statut ────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',       'Brouillon'),
        ('submitted',   'Soumise'),
        ('in_progress', 'En cours'),
        ('validated',   'Validée'),
    ], string='Statut', default='draft', track_visibility='onchange')
    date_in_progress = fields.Date(string='Date mise en cours')
    date_envoi       = fields.Date(string="Date d'envoi", readonly=True)
    sent_by_id       = fields.Many2one('res.users', string='Envoyé par', readonly=True)

    @api.depends('fac_ids')
    def _compute_fac_reference(self):
        for rec in self:
            fac = rec.sudo().fac_ids[:1]
            rec.fac_reference = fac.id if fac else False

    @api.depends('fac_ids')
    def _compute_fac_number_display(self):
        for rec in self:
            fac = rec.sudo().fac_ids[:1]
            rec.fac_number_display = fac.name if fac else False

    @api.depends('fac_ids', 'fac_ids.responsable_id', 'fac_ids.current_handler_uid')
    def _compute_can_access_fac(self):
        user = self.env.user
        is_rmqse = user.has_group('nc_management.group_responsable_qualite')
        for rec in self:
            if is_rmqse:
                rec.can_access_fac = True
            else:
                fac = rec.sudo().fac_ids[:1]
                rec.can_access_fac = bool(fac and (
                    fac.responsable_id.id == user.id
                    or fac.current_handler_uid.id == user.id
                ))

    # ── Validation obligatoire à la sauvegarde ────────────────
    # Déclenche sur ces champs uniquement ; le numéro FNC est géré
    # séparément via le bouton "Générer Numéro FNC".
    @api.constrains(
        'direction_id', 'description',
        'type_nc_produit', 'type_reclamation', 'type_sst', 'type_environnement',
        'type_travaux', 'type_audit', 'type_audit_interne', 'type_audit_externe',
        'type_achat', 'type_reception', 'type_dysfonctionnement', 'type_autre',
    )
    def _check_fnc_required(self):
        if self.env.context.get('skip_fnc_validation'):
            return
        for rec in self:
            # Sauvegarde intermédiaire avant ouverture du wizard : le type sera défini par le wizard
            if rec.name == 'New':
                continue
            if not rec.direction_id:
                raise ValidationError(
                    "La Direction / Emetteur est obligatoire."
                )
            has_type = any([
                rec.type_nc_produit, rec.type_reclamation, rec.type_sst,
                rec.type_environnement, rec.type_travaux, rec.type_audit,
                rec.type_audit_interne, rec.type_audit_externe, rec.type_achat,
                rec.type_reception, rec.type_dysfonctionnement, rec.type_autre,
            ])
            if not has_type:
                raise ValidationError(
                    "Veuillez sélectionner au moins un type de non-conformité."
                )
            if not (rec.description and rec.description.strip()):
                raise ValidationError(
                    "La description de la non-conformité est obligatoire."
                )

    @api.onchange('fonction_visa')
    def _onchange_fonction_visa(self):
        if not self.fonction_visa:
            return
        has_type = any([
            self.type_nc_produit, self.type_reclamation, self.type_sst,
            self.type_environnement, self.type_travaux, self.type_audit,
            self.type_audit_interne, self.type_audit_externe, self.type_achat,
            self.type_reception, self.type_dysfonctionnement, self.type_autre,
        ])
        if not has_type:
            self.fonction_visa = False
            return {'warning': {
                'title': 'Champ requis',
                'message': "Veuillez sélectionner au moins un type de non-conformité avant d'affecter la fonction et visa.",
            }}
        if not (self.description and self.description.strip()):
            self.fonction_visa = False
            return {'warning': {
                'title': 'Champ requis',
                'message': "Veuillez remplir la description de la non-conformité avant d'affecter la fonction et visa.",
            }}
        if not self.signale_par_id:
            self.fonction_visa = False
            return {'warning': {
                'title': 'Champ requis',
                'message': "Veuillez renseigner le signalement avant d'affecter la fonction et visa.",
            }}
        if not self.date_signalement:
            self.fonction_visa = False
            return {'warning': {
                'title': 'Champ requis',
                'message': "Veuillez renseigner la date de signalement avant d'affecter la fonction et visa.",
            }}
        if self.state == 'draft':
            self.state = 'submitted'

    @api.onchange(
        'type_nc_produit', 'type_reclamation', 'type_sst', 'type_environnement',
        'type_travaux', 'type_audit', 'type_audit_interne', 'type_audit_externe',
        'type_achat', 'type_reception', 'type_dysfonctionnement', 'type_autre',
        'description', 'signale_par_id', 'date_signalement',
    )
    def _onchange_autofill_fonction_visa(self):
        if self.fonction_visa:
            return
        has_type = any([
            self.type_nc_produit, self.type_reclamation, self.type_sst,
            self.type_environnement, self.type_travaux, self.type_audit,
            self.type_audit_interne, self.type_audit_externe, self.type_achat,
            self.type_reception, self.type_dysfonctionnement, self.type_autre,
        ])
        if not (has_type and self.description and self.description.strip()
                and self.signale_par_id and self.date_signalement):
            return
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        if employee:
            self.fonction_visa = employee.visa_no or employee.job_id.name or employee.name

    @api.constrains('fonction_visa')
    def _check_fonction_visa_requirements(self):
        for rec in self:
            if not rec.fonction_visa or rec.name == 'New':
                continue
            has_type = any([
                rec.type_nc_produit, rec.type_reclamation, rec.type_sst,
                rec.type_environnement, rec.type_travaux, rec.type_audit,
                rec.type_audit_interne, rec.type_audit_externe, rec.type_achat,
                rec.type_reception, rec.type_dysfonctionnement, rec.type_autre,
            ])
            if not has_type:
                raise ValidationError(
                    "Veuillez sélectionner au moins un type de non-conformité "
                    "avant d'affecter la fonction et visa."
                )
            if not (rec.description and rec.description.strip()):
                raise ValidationError(
                    "Veuillez remplir la description de la non-conformité "
                    "avant d'affecter la fonction et visa."
                )
            if not rec.signale_par_id:
                raise ValidationError(
                    "Veuillez renseigner le signalement avant d'affecter la fonction et visa."
                )
            if not rec.date_signalement:
                raise ValidationError(
                    "Veuillez renseigner la date de signalement avant d'affecter la fonction et visa."
                )

    @api.onchange('responsable_action_id')
    def _onchange_responsable_action_id(self):
        if not self.responsable_action_id:
            return
        if not self.realise_par_id:
            self.responsable_action_id = False
            return {'warning': {
                'title': 'Champ requis',
                'message': "Veuillez renseigner 'Réalisé par' avant d'affecter le responsable de l'action.",
            }}
        if not self.date_realisation:
            self.responsable_action_id = False
            return {'warning': {
                'title': 'Champ requis',
                'message': "Veuillez renseigner la date de réalisation avant d'affecter le responsable de l'action.",
            }}

    @api.onchange('realise_par_id', 'date_realisation')
    def _onchange_autofill_responsable_action(self):
        if self.responsable_action_id:
            return
        if not self.realise_par_id or not self.date_realisation:
            return
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        if employee:
            self.responsable_action_id = employee

    @api.onchange('superieur_id', 'date_validation', 'signature')
    def _onchange_autofill_signature(self):
        if self.state != 'in_progress':
            return
        employee = self.env['hr.employee'].sudo().search(
            [('user_id', '=', self.env.uid)], limit=1)
        if not employee:
            return
        if not self.superieur_id:
            self.superieur_id = employee
        if not self.date_validation:
            self.date_validation = fields.Date.today()
        if not self.signature:
            self.signature = employee.visa_no or employee.job_id.name or employee.name

    # ── Valeurs par défaut depuis le compte employé ───────────
    @api.model
    def default_get(self, fields_list):
        defaults = super(Nonconformity, self).default_get(fields_list)
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        if employee:
            if 'signale_par_id' in fields_list:
                defaults['signale_par_id'] = employee.id
            dept = employee.department_id
            while dept:
                level = dept.scaek_level
                if level == 'direction' and 'direction_id' in fields_list:
                    defaults['direction_id'] = dept.id
                elif level == 'departement' and 'department_id' in fields_list:
                    defaults['department_id'] = dept.id
                elif level == 'service' and 'service_id' in fields_list:
                    defaults['service_id'] = dept.id
                dept = dept.parent_id
        return defaults

    @api.model
    def create(self, vals):
        return super(Nonconformity, self).create(vals)

    @api.multi
    def write(self, vals):
        # Le numéro FNC est immuable une fois assigné
        if 'name' in vals:
            for rec in self:
                if rec.name != 'New':
                    raise ValidationError(
                        "Le numéro FNC '%s' est définitif et ne peut pas être modifié." % rec.name
                    )

        # ── Transitions d'état déclenchées après sauvegarde ──
        if 'state' not in vals:
            for rec in self:
                if vals.get('fonction_visa') and rec.state == 'draft':
                    vals = dict(vals, state='submitted')
                elif vals.get('signature') and rec.state == 'in_progress':
                    vals = dict(vals, state='validated')
                break  # formulaire = un seul record à la fois

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

        # Création automatique de FAC dès que le traitement est complet en base
        treatment_fields = [
            'impact', 'action_immediate', 'analyse_causes',
            'trait_reprise', 'trait_declassement', 'trait_retour_fourn',
            'trait_recyclage', 'trait_reparation', 'trait_autre',
            'assigned_to_id',
        ]
        if any(f in vals for f in treatment_fields):
            for rec in self:
                if rec.fac_ids:
                    continue
                if rec.state not in ('submitted', 'in_progress'):
                    continue
                if not rec.assigned_to_id:
                    continue
                has_trait = any([
                    rec.trait_reprise, rec.trait_declassement, rec.trait_retour_fourn,
                    rec.trait_recyclage, rec.trait_reparation, rec.trait_autre,
                ])
                if not (has_trait and rec.action_immediate and rec.analyse_causes and rec.impact):
                    continue
                # Traitement complet : créer la FAC
                if rec.state == 'submitted':
                    rec.write({'state': 'in_progress',
                               'date_in_progress': fields.Date.today()})
                employee = rec.assigned_to_id
                resp_user = employee.user_id if employee else self.env.user
                fac_vals = {
                    'fnc_id': rec.id,
                    'ref_document': rec.name,
                    'direction_id': rec.direction_id.id if rec.direction_id else False,
                    'rappel_nc': rec.description or '',
                    'analyse_causes': rec.analyse_causes or '',
                    'responsable_id': resp_user.id if resp_user else False,
                    'responsable_analyse_id': employee.id if employee else False,
                }
                self.env['nc_management.corrective_action'].sudo(
                    resp_user.id if resp_user else self.env.uid
                ).create(fac_vals)

        # Sync responsable_id + responsable_analyse_id sur les FAC quand assigned_to_id change
        if 'assigned_to_id' in vals:
            employee = self.env['hr.employee'].browse(vals['assigned_to_id'])
            user = employee.user_id if employee else False
            for rec in self:
                for fac in rec.sudo().fac_ids:
                    fac.sudo().write({
                        'responsable_id': user.id if user else False,
                        'responsable_analyse_id': employee.id if employee else False,
                    })

        return res

    @api.multi
    def unlink(self):
        if not self.env.user.has_group('nc_management.group_responsable_qualite'):
            if any(rec.create_uid.id != self.env.uid for rec in self):
                raise UserError("Vous ne pouvez supprimer que vos propres fiches FNC.")
        return super(Nonconformity, self).unlink()

    def _traitement_complet(self):
        has_traitement = any([
            self.trait_reprise, self.trait_declassement, self.trait_retour_fourn,
            self.trait_recyclage, self.trait_reparation, self.trait_autre,
        ])
        manquants = []
        if not has_traitement:
            manquants.append("un type de traitement")
        if not self.action_immediate:
            manquants.append("l'action immédiate")
        if not self.realise_par_id:
            manquants.append("Réalisé par")
        if not self.date_realisation:
            manquants.append("la date de réalisation")
        if not self.analyse_causes:
            manquants.append("l'analyse des causes")
        if not self.impact:
            manquants.append("l'impact")
        return manquants

    @api.onchange('impact', 'action_immediate', 'analyse_causes',
                  'realise_par_id', 'date_realisation',
                  'trait_reprise', 'trait_declassement', 'trait_retour_fourn',
                  'trait_recyclage', 'trait_reparation', 'trait_autre')
    def _onchange_traitement_complet(self):
        if self.state != 'submitted':
            return
        if not self._traitement_complet():
            employee = self.env['hr.employee'].search(
                [('user_id', '=', self.env.uid)], limit=1)
            if employee:
                self.assigned_to_id = employee

    @api.onchange('assigned_to_id')
    def _onchange_assigned_to_id(self):
        if not self.assigned_to_id or self.state not in ('submitted', 'in_progress'):
            return
        manquants = self._traitement_complet()
        if manquants:
            self.assigned_to_id = False
            return {'warning': {
                'title': 'Champ requis',
                'message': "Veuillez compléter tous les champs de traitement avant de continuer :\n— "
                           + "\n— ".join(manquants),
            }}

    @api.onchange('signature')
    def _onchange_signature(self):
        if self.signature and self.state == 'in_progress':
            self.state = 'validated'

    # ── Boutons workflow ──────────────────────────────────────
    @api.multi
    def action_valider_fnc(self):
        self.ensure_one()
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        vals = {'state': 'validated'}
        if employee and not self.superieur_id:
            vals['superieur_id'] = employee.id
        if not self.date_validation:
            vals['date_validation'] = fields.Date.today()
        if not self.signature and employee:
            vals['signature'] = employee.visa_no or employee.job_id.name or employee.name
        self.write(vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.nonconformity',
            'res_id': self.id,
            'views': [[False, 'form']],
            'target': 'current',
            'context': {'form_view_initial_mode': 'view'},
        }

    @api.multi
    def action_open_send_wizard(self):
        self.ensure_one()
        if self.name == 'New':
            raise UserError(
                "Le numéro FNC doit être généré via le bouton "
                "\"Générer Numéro FNC\" avant d'enregistrer la fiche."
            )
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
        if self.name != 'New':
            raise UserError(
                "Le numéro FNC '%s' a déjà été assigné et ne peut pas être régénéré." % self.name
            )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Générer Numéro',
            'res_model': 'nc_management.number_generator_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_fnc_id': self.id},
        }

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

    # ── Sélection exclusive du type de NC ────────────────────
    @api.onchange(
        'type_nc_produit', 'type_reclamation', 'type_sst', 'type_environnement',
        'type_travaux', 'type_audit', 'type_audit_interne', 'type_audit_externe',
        'type_achat', 'type_reception', 'type_dysfonctionnement', 'type_autre',
    )
    def _onchange_type_exclusive(self):
        _all = [
            'type_nc_produit', 'type_reclamation', 'type_sst', 'type_environnement',
            'type_travaux', 'type_audit', 'type_audit_interne', 'type_audit_externe',
            'type_achat', 'type_reception', 'type_dysfonctionnement', 'type_autre',
        ]
        for field in _all:
            if getattr(self, field) and not getattr(self._origin, field, False):
                if self.name == 'New':
                    setattr(self, field, False)
                    return {'warning': {
                        'title': 'Numéro FNC requis',
                        'message': "Veuillez d'abord générer le numéro FNC avant de sélectionner le type de non-conformité.",
                    }}
                for other in _all:
                    if other != field:
                        setattr(self, other, False)
                break



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
        string='FNC liée',
        ondelete='set null',
        index=True
    )
    ref_document = fields.Char(string='N° FNC ou autre document')
    fnc_ref_display = fields.Char(
        string='N° FNC ou autre document (affiché)',
        compute='_compute_fnc_ref_display',
        store=False,
    )
    date_fnc     = fields.Date(string='Date FNC')
    responsable_id = fields.Many2one(
        'res.users', string='Responsable de l\'action',
        index=True)

    # ── Section 1 — Rappel NC ─────────────────────────────────
    rappel_nc = fields.Text(string='1- Rappel de la Non-Conformité')

    # ── Section 2 — Analyse des causes ───────────────────────
    analyse_causes         = fields.Text(string='2- Analyse des causes de la non-conformité')
    responsable_analyse_id = fields.Many2one('hr.employee', string='Responsable analyse',
                               context={'no_create': True, 'no_create_edit': True})
    date_analyse           = fields.Date(string='Date analyse')
    visa_analyse           = fields.Char(string='Visa analyse')

    # ── Section 3 — Actions décidées ─────────────────────────
    description_actions    = fields.Text(string='Description des actions')
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
    date_envoi     = fields.Date(string="Date d'envoi", readonly=True)
    sent_by_id     = fields.Many2one('res.users', string='Envoyé par', readonly=True)
    current_handler_uid = fields.Many2one(
        'res.users', string='Destinataire courant', copy=False)

    # ── Statut ────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',      'Brouillon'),
        ('submitted',  'Soumise'),
        ('in_progress','En cours'),
        ('validated',  'Validée'),
        ('closed',     'Clôturée'),
    ], string='Statut', default='draft', track_visibility='onchange')
    date_validated = fields.Date(string='Date validation QSE')

    # ── Valeurs par défaut depuis le compte employé ───────────
    @api.model
    def default_get(self, fields_list):
        defaults = super(CorrectiveAction, self).default_get(fields_list)
        if 'responsable_id' in fields_list:
            defaults['responsable_id'] = self.env.uid
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        if employee:
            dept = employee.department_id
            while dept:
                if dept.scaek_level == 'direction' and 'direction_id' in fields_list:
                    defaults['direction_id'] = dept.id
                    break
                dept = dept.parent_id
        return defaults

    @api.depends('fnc_id', 'ref_document')
    def _compute_fnc_ref_display(self):
        for rec in self:
            if rec.fnc_id:
                rec.fnc_ref_display = rec.fnc_id.name
            else:
                rec.fnc_ref_display = rec.ref_document or ''

    # ── Remplissage auto via FNC ──────────────────────────────
    @api.onchange('fnc_id')
    def _onchange_fnc_id(self):
        if self.fnc_id:
            self.ref_document = self.fnc_id.name
            self.rappel_nc = self.fnc_id.description
            self.analyse_causes = self.fnc_id.analyse_causes
            self.direction_id = self.fnc_id.direction_id
            self.date_fnc = self.fnc_id.date
            self.responsable_analyse_id = self.fnc_id.assigned_to_id
            employee = self.fnc_id.assigned_to_id
            self.responsable_id = employee.user_id if employee else False

    # ── Numérotation automatique ──────────────────────────────
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'nc_management.corrective_action') or 'New'
        if not vals.get('responsable_id'):
            vals['responsable_id'] = self.env.uid
        new_state = self._state_from_visas(
            vals.get('visa_analyse'),
            vals.get('visa_actions'),
            vals.get('qse_visa'),
            vals.get('visa_cloture'),
        )
        vals['state'] = new_state
        return super(CorrectiveAction, self).create(vals)

    # ── Calcul d'état depuis les visas ───────────────────────
    def _state_from_visas(self, visa_analyse, visa_actions, qse_visa, visa_cloture):
        if visa_cloture:  return 'closed'
        if qse_visa:      return 'validated'
        if visa_actions:  return 'in_progress'
        if visa_analyse:  return 'submitted'
        return 'draft'

    # ── Validation des champs requis avant visa (onchange) ───
    @api.onchange('visa_analyse', 'visa_actions', 'qse_visa', 'visa_cloture')
    def _onchange_visa_state(self):
        warnings = []

        if self.visa_analyse:
            missing = []
            if not self.rappel_nc:
                missing.append("le rappel de la non-conformité")
            if not self.analyse_causes:
                missing.append("l'analyse des causes")
            if not self.responsable_analyse_id:
                missing.append("le responsable")
            if not self.date_analyse:
                missing.append("la date")
            if missing:
                self.visa_analyse = False
                warnings.append("Section 2 : veuillez saisir " + ", ".join(missing) + ".")

        if self.visa_actions:
            missing = []
            if not self.action_line_ids:
                missing.append("au moins une ligne d'action")
            if not self.responsable_actions_id:
                missing.append("le responsable")
            if not self.date_actions:
                missing.append("la date")
            if missing:
                self.visa_actions = False
                warnings.append("Section 3 : veuillez saisir " + ", ".join(missing) + ".")

        if self.qse_visa:
            missing = []
            if not self.qse_nom_id:
                missing.append("le nom")
            if not self.qse_date:
                missing.append("la date")
            if missing:
                self.qse_visa = False
                warnings.append("Section 4 : veuillez saisir " + ", ".join(missing) + ".")

        if self.visa_cloture:
            missing = []
            if not self.cloture_par_id:
                missing.append("le responsable de clôture")
            if not self.date_cloture:
                missing.append("la date")
            if missing:
                self.visa_cloture = False
                warnings.append("Clôture : veuillez saisir " + ", ".join(missing) + ".")

        if warnings:
            return {'warning': {'title': 'Saisie incomplète', 'message': '\n'.join(warnings)}}

        new_state = self._state_from_visas(
            self.visa_analyse, self.visa_actions, self.qse_visa, self.visa_cloture)
        self.state = new_state
        if new_state == 'validated' and not self.date_validated:
            self.date_validated = fields.Date.today()
        if new_state == 'closed':
            if not self.date_cloture:
                self.date_cloture = fields.Date.today()
            if not self.cloture_par_id:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', self.env.uid)], limit=1)
                if employee:
                    self.cloture_par_id = employee

    # ── Validation serveur (bloque la sauvegarde) ────────────
    @api.constrains('visa_analyse')
    def _check_visa_analyse(self):
        for rec in self:
            if rec.visa_analyse:
                missing = []
                if not rec.rappel_nc:
                    missing.append("le rappel de la non-conformité")
                if not rec.analyse_causes:
                    missing.append("l'analyse des causes")
                if not rec.responsable_analyse_id:
                    missing.append("le responsable")
                if not rec.date_analyse:
                    missing.append("la date")
                if missing:
                    raise ValidationError(
                        "Section 2 : veuillez saisir " + ", ".join(missing) + ".")

    @api.constrains('visa_actions')
    def _check_visa_actions(self):
        for rec in self:
            if rec.visa_actions:
                missing = []
                if not rec.action_line_ids:
                    missing.append("au moins une ligne d'action")
                if not rec.responsable_actions_id:
                    missing.append("le responsable")
                if not rec.date_actions:
                    missing.append("la date")
                if missing:
                    raise ValidationError(
                        "Section 3 : veuillez saisir " + ", ".join(missing) + ".")

    @api.constrains('qse_visa')
    def _check_qse_visa(self):
        for rec in self:
            if rec.qse_visa:
                missing = []
                if not rec.qse_nom_id:
                    missing.append("le nom")
                if not rec.qse_date:
                    missing.append("la date")
                if missing:
                    raise ValidationError(
                        "Section 4 : veuillez saisir " + ", ".join(missing) + ".")

    @api.constrains('visa_cloture')
    def _check_visa_cloture(self):
        for rec in self:
            if rec.visa_cloture:
                missing = []
                if not rec.cloture_par_id:
                    missing.append("le responsable de clôture")
                if not rec.date_cloture:
                    missing.append("la date")
                if missing:
                    raise ValidationError(
                        "Clôture : veuillez saisir " + ", ".join(missing) + ".")

    # ── Transitions d'état à la sauvegarde ───────────────────
    @api.multi
    def write(self, vals):
        for rec in self:
            new_va  = vals.get('visa_analyse', rec.visa_analyse)
            new_vac = vals.get('visa_actions', rec.visa_actions)
            new_qv  = vals.get('qse_visa',     rec.qse_visa)
            new_vc  = vals.get('visa_cloture', rec.visa_cloture)
            new_state = rec._state_from_visas(new_va, new_vac, new_qv, new_vc)
            # Toujours forcer l'état depuis les visas
            vals = dict(vals, state=new_state)
            if new_state == 'validated':
                if not vals.get('date_validated') and not rec.date_validated:
                    vals = dict(vals, date_validated=fields.Date.today())
            if new_state == 'closed':
                if not vals.get('cloture_par_id') and not rec.cloture_par_id:
                    emp = self.env['hr.employee'].search(
                        [('user_id', '=', self.env.uid)], limit=1)
                    vals = dict(vals, cloture_par_id=emp.id if emp else False)
                if not vals.get('date_cloture') and not rec.date_cloture:
                    vals = dict(vals, date_cloture=fields.Date.today())
            break
        return super(CorrectiveAction, self).write(vals)

    @api.multi
    def action_open_send_fac_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Envoyer la FAC',
            'res_model': 'nc_management.send_fac_wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('nc_management.view_send_fac_wizard').id,
            'target': 'new',
            'context': {'default_fac_id': self.id},
        }

    @api.multi
    def unlink(self):
        if not self.env.user.has_group('nc_management.group_responsable_qualite'):
            for rec in self:
                if rec.responsable_id.id != self.env.uid and rec.create_uid.id != self.env.uid:
                    raise UserError("Vous ne pouvez supprimer que les fiches FAC dont vous êtes responsable de l'action.")
        return super(CorrectiveAction, self).unlink()


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
                       readonly=True, default='New',
                       track_visibility='onchange')
    nature = fields.Selection([
        ('nc_produit',              'NC Produit'),
        ('reclamation_pi',          'Réclamation Client ou PI'),
        ('environnement',           'Environnement'),
        ('sst',                     'SST'),
        ('audit_externe',           'Audit Externe'),
        ('audit_interne',           'Audit Interne'),
        ('swot',                    'SWOT'),
        ('risque',                  'Risque'),
        ('objectif_non_atteint',    'Objectif non atteint'),
        ('decision_revue_direction','Décision revue direction'),
        ('amelioration',            'Amélioration'),
        ('nc_reglementaire',        'NC réglementaire'),
    ], string='Nature')
    fnc_id = fields.Many2one('nc_management.nonconformity', string='Référence FNC')
    reference = fields.Char(string='Référence')
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
    is_integrated = fields.Char(
        string="Intégré au plan d'amélioration",
        compute='_compute_is_integrated',
        store=True
    )

    @api.depends('global_plan_id', 'improvement_plan_id',
                 'improvement_plan_id.global_plan_id')
    def _compute_is_integrated(self):
        for rec in self:
            # Intégré via ancien système OU nouveau système
            is_old = bool(rec.global_plan_id)
            is_new = bool(
                rec.improvement_plan_id and
                rec.improvement_plan_id.global_plan_id)
            rec.is_integrated = 'Oui' if (is_old or is_new) else 'Non'
    description = fields.Text(
        string="Brève description de la non-conformité, remarque et/ou point sensible / ou Objectif d'amélioration",
        track_visibility='onchange')
    causes = fields.Text(string='Causes', track_visibility='onchange')
    action = fields.Text(string='Action', track_visibility='onchange')
    responsable_id = fields.Many2one(
        'hr.employee', string='Responsable',
        context={'no_create': True, 'no_create_edit': True},
        track_visibility='onchange')
    responsable_ids = fields.Many2many(
        'hr.employee',
        'plan_smi_responsable_rel',
        'plan_id',
        'employee_id',
        string='Responsable(s)',
        context={'no_create': True, 'no_create_edit': True})
    moyens = fields.Char(
        string='Moyens Nécessaires (matériels, financiers, humains)',
        track_visibility='onchange')
    duree_estimee = fields.Char(string='Durée Estimée')
    date_prevue = fields.Date(
        string='Date Prévue', track_visibility='onchange')
    date_lancement = fields.Date(string='Date de Lancement')
    date_realisation = fields.Date(
        string='Date de Réalisation', track_visibility='onchange')
    avancement = fields.Integer(
        string='État Avancement (%)', default=0,
        track_visibility='onchange')
    avancement_choice = fields.Selection([
        ('0',   '0%'),
        ('25',  '25%'),
        ('50',  '50%'),
        ('75',  '75%'),
        ('100', '100%'),
    ], string='État Avancement (%)',
       compute='_compute_avancement_choice',
       inverse='_set_avancement_choice')
    duree_reelle = fields.Char(string='Durée Réelle')
    critere_efficacite = fields.Text(string="Critère d'Efficacité")
    efficacite = fields.Selection([
        ('oui', 'OUI'),
        ('non', 'NON'),
    ], string='Efficacité', track_visibility='onchange')
    remarque = fields.Text(string='Remarque (si non efficace)')
    state = fields.Selection([
        ('draft',    'Brouillon'),
        ('done',     'Réalisé'),
        ('en_cours', 'En cours'),
        ('realise',  'Réalisé'),
        ('cloture',  'Clôturé'),
    ], string='Avancement', default='draft', track_visibility='onchange')

    etat_avancement = fields.Selection([
        ('non_realise', 'Non réalisé'),
        ('en_cours',    'En cours'),
        ('realise',     'Réalisé'),
    ], string='État', compute='_compute_etat_avancement', store=True)

    @api.depends('avancement')
    def _compute_etat_avancement(self):
        for rec in self:
            if rec.avancement >= 100:
                rec.etat_avancement = 'realise'
            elif rec.avancement > 0:
                rec.etat_avancement = 'en_cours'
            else:
                rec.etat_avancement = 'non_realise'

    @api.depends('avancement')
    def _compute_avancement_choice(self):
        for rec in self:
            rec.avancement_choice = (
                str(rec.avancement)
                if rec.avancement in (0, 25, 50, 75, 100)
                else '0'
            )

    def _set_avancement_choice(self):
        for rec in self:
            if rec.avancement_choice is not False:
                rec.avancement = int(rec.avancement_choice)

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
    mois_reception  = fields.Date('Date de création')
    date_maj        = fields.Datetime("Dernière mise à jour", readonly=True)
    version_number  = fields.Integer('Version', default=1)
    child_plan_ids  = fields.One2many(
        'nc_management.plan_action_smi',
        'global_plan_id',
        string='Plans intégrés',
    )

    # ── Filtres UI (ne déclenchent pas date_maj) ──────────────────
    filter_nature = fields.Selection([
        ('nc_produit',               'NC Produit'),
        ('reclamation_pi',           'Réclamation Client ou PI'),
        ('environnement',            'Environnement'),
        ('sst',                      'SST'),
        ('audit_externe',            'Audit Externe'),
        ('audit_interne',            'Audit Interne'),
        ('swot',                     'SWOT'),
        ('risque',                   'Risque'),
        ('objectif_non_atteint',     'Objectif non atteint'),
        ('decision_revue_direction', 'Décision revue direction'),
        ('amelioration',             'Amélioration'),
        ('nc_reglementaire',         'NC réglementaire'),
    ], string='Nature', default=False)

    filter_direction_id = fields.Many2one(
        'hr.department',
        domain=[('scaek_level', '=', 'direction')],
        string='Direction',
        default=False,
        context={'no_create': True, 'no_create_edit': True})

    # Plans affichés après application des filtres UI
    child_plan_ids_display = fields.Many2many(
        'nc_management.plan_action_smi',
        compute='_compute_child_display',
        string='Plans intégrés',
        store=False)

    @api.depends('child_plan_ids', 'filter_nature', 'filter_direction_id')
    def _compute_child_display(self):
        for rec in self:
            children = rec.child_plan_ids
            if rec.filter_nature:
                children = children.filtered(
                    lambda c: c.nature == rec.filter_nature)
            if rec.filter_direction_id:
                children = children.filtered(
                    lambda c: c.direction_id == rec.filter_direction_id)
            rec.child_plan_ids_display = children

    @api.multi
    def action_reset_filters(self):
        """Réinitialise les filtres Nature et Direction."""
        self.ensure_one()
        self.with_context(_skip_date_maj=True).write({
            'filter_nature': False,
            'filter_direction_id': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.plan_action_smi',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'nc_management.view_plan_smi_form_global').id,
            'target': 'current',
        }

    # ── Liens vers la nouvelle hiérarchie 3 niveaux ───────────────

    # Lien vers le Plan d'Amélioration de direction (niveau 2)
    improvement_plan_id = fields.Many2one(
        'nc_management.smi_improvement_plan',
        string="Plan d'Amélioration (direction)",
        ondelete='set null',
        index=True,
        track_visibility='onchange')

    # Lien direct vers le Plan Global — pour plans ajoutés par la RMQSE
    direct_global_plan_id = fields.Many2one(
        'nc_management.smi_global_plan',
        string='Plan Global (direct RMQSE)',
        ondelete='set null',
        index=True)

    # ── Référence affichée avec numéro de version ─────────────────
    name_display = fields.Char(
        string='Référence',
        compute='_compute_name_display',
        store=False)

    _BASE_SMI_RE = None  # lazy init

    @api.depends('name', 'is_global')
    def _compute_name_display(self):
        for rec in self:
            rec.name_display = rec.name or 'New'

    # ── Traçabilité historique (vue à une date donnée) ────────────
    date_consultation = fields.Date(
        string="Voir l'état à la date",
        help="Sélectionnez une date passée pour voir l'état du plan à ce moment précis.")

    historique_html = fields.Html(
        string='État historique',
        compute='_compute_plan_historique_html',
        sanitize=False,
        store=False)

    # ── Analyse HTML (tableau + graphique, catégories dynamiques) ──
    analyse_html = fields.Html(
        string='Analyse Efficacité',
        compute='_compute_analyse_html',
        sanitize=False,
    )

    # 4 couleurs en rotation pour les catégories (modérément sombres)
    _CAT_COLORS = ['#2575b8', '#d44535', '#1fa255', '#cc8800']

    @api.depends('date_consultation', 'child_plan_ids')
    def _compute_plan_historique_html(self):
        from datetime import datetime as _dt

        th  = ('padding:8px 12px;text-align:left;white-space:nowrap;'
               'border-bottom:2px solid #dee2e6;color:white;')
        td  = 'padding:7px 12px;border-bottom:1px solid #eee;'
        tdc = td + 'text-align:center;'

        EFF_LABELS = {
            'oui': 'OUI', 'non': 'NON',
            False: '-', None: '-', '': '-',
        }

        for rec in self:
            if not rec.is_global or not rec.date_consultation:
                rec.historique_html = ''
                continue

            date_limit = fields.Datetime.to_string(
                _dt.combine(
                    fields.Date.from_string(str(rec.date_consultation)),
                    _dt.max.time()))

            def _val(res_id, field_name, default):
                tracking = self.env['mail.tracking.value'].sudo().search([
                    ('mail_message_id.res_id',  '=', res_id),
                    ('mail_message_id.model',   '=', 'nc_management.plan_action_smi'),
                    ('field',                   '=', field_name),
                    ('mail_message_id.date',    '<=', date_limit),
                ], order='id desc', limit=1)
                if not tracking:
                    return default
                if field_name == 'avancement':
                    return tracking.new_value_integer
                return tracking.new_value_char or default

            # Inclure les plans intégrés à cette date :
            # on vérifie via le tracking si submission_state = 'integre'
            # était actif à date_limit. Si aucun tracking trouvé mais que
            # le plan est actuellement intégré, on l'inclut quand même
            # (cas où l'intégration n'a pas généré de tracking).
            plans = rec.env['nc_management.plan_action_smi'].browse()
            for p in rec.child_plan_ids:
                integre_tracking = rec.env['mail.tracking.value'].sudo().search([
                    ('mail_message_id.res_id', '=', p.id),
                    ('mail_message_id.model', '=', 'nc_management.plan_action_smi'),
                    ('field', '=', 'submission_state'),
                    ('new_value_char', '=', 'integre'),
                    ('mail_message_id.date', '<=', date_limit),
                ], order='id desc', limit=1)
                if integre_tracking:
                    plans |= p
                elif not rec.env['mail.tracking.value'].sudo().search([
                    ('mail_message_id.res_id', '=', p.id),
                    ('mail_message_id.model', '=', 'nc_management.plan_action_smi'),
                    ('field', '=', 'submission_state'),
                    ('mail_message_id.date', '<=', date_limit),
                ], order='id desc', limit=1):
                    # Aucun tracking du tout → intégré depuis la création
                    plans |= p

            if not plans:
                rec.historique_html = (
                    '<p style="color:#888;padding:16px;">'
                    "Aucun plan n'était intégré à cette date.</p>")
                continue

            nature_sel = rec._fields['nature'].selection
            nature_labels = dict(
                nature_sel if not callable(nature_sel) else nature_sel(rec))

            rows = ''
            for i, plan in enumerate(plans):
                hist_av  = _val(plan.id, 'avancement', plan.avancement)
                hist_eff = _val(plan.id, 'efficacite', plan.efficacite or '')

                # État calculé depuis l'avancement historique (cohérent avec etat_avancement)
                av_int = hist_av if hist_av is not None else 0
                if av_int >= 100:
                    state_lbl, sc = 'Réalisé',     '#1fa255'
                elif av_int > 0:
                    state_lbl, sc = 'En cours',    '#cc8800'
                else:
                    state_lbl, sc = 'Non réalisé', '#d44535'

                eff_lbl = EFF_LABELS.get(hist_eff, '-')
                bg = '#fff' if i % 2 == 0 else '#f8f9fa'

                rows += (
                    '<tr style="background:{bg};">'
                    '<td style="{td}">{nature}</td>'
                    '<td style="{td}"><b>{ref}</b></td>'
                    '<td style="{td}">{direction}</td>'
                    '<td style="{td}">{responsable}</td>'
                    '<td style="{tdc}">{av}%</td>'
                    '<td style="{tdc}"><span style="color:{sc};font-weight:bold;">'
                    '{state}</span></td>'
                    '<td style="{tdc}">{eff}</td>'
                    '</tr>'
                ).format(
                    bg=bg, td=td, tdc=tdc,
                    nature=nature_labels.get(plan.nature, plan.nature or '-'),
                    ref=plan.name,
                    direction=plan.direction_id.name if plan.direction_id else '-',
                    responsable=', '.join(plan.responsable_ids.mapped('name')) if plan.responsable_ids else (plan.responsable_id.name if plan.responsable_id else '-'),
                    av=hist_av if hist_av is not None else 0,
                    state=state_lbl, sc=sc, eff=eff_lbl,
                )

            consul_str = fields.Date.from_string(
                str(rec.date_consultation)).strftime('%d/%m/%Y')
            thead = (
                '<thead><tr style="background:#1a2e5a;">'
                '<th style="{th}">Nature</th>'
                '<th style="{th}">Référence</th>'
                '<th style="{th}">Direction</th>'
                '<th style="{th}">Responsable</th>'
                '<th style="{th}">Avancement %</th>'
                '<th style="{th}">État</th>'
                '<th style="{th}">Efficacité</th>'
                '</tr></thead>'
            ).format(th=th)

            rec.historique_html = (
                '<div style="font-family:Arial,sans-serif;">'
                '<div style="background:#fff3cd;border:1px solid #ffc107;'
                'border-radius:4px;padding:12px 16px;margin-bottom:12px;">'
                '<b>&#9888; Vue historique au {date}</b> — '
                "Voici l'état du plan à cette date.</div>"
                '<table class="smi_hist_tree" style="width:100%;border-collapse:collapse;font-size:13px;">'
                '{thead}<tbody>{rows}</tbody></table>'
                '</div>'
            ).format(date=consul_str, thead=thead, rows=rows)

    @api.depends('child_plan_ids.nature', 'child_plan_ids.efficacite',
                 'child_plan_ids.avancement', 'is_global', 'submission_state',
                 'date_consultation')
    def _compute_analyse_html(self):
        from datetime import datetime as _dt

        def badge(t):
            if t == 100: return '#1fa255'
            if t == 0:   return '#d44535'
            return '#cc8800'

        th  = 'padding:10px 14px;text-align:center;white-space:nowrap;'
        thl = 'padding:10px 14px;text-align:left;'
        tdc = 'padding:8px 14px;text-align:center;border-bottom:1px solid #ddd;'
        tdl = 'padding:8px 14px;text-align:left;border-bottom:1px solid #ddd;'

        for rec in self:
            children = rec.child_plan_ids
            if not rec.is_global or not children:
                rec.analyse_html = (
                    '<p style="color:#888;padding:16px;">'
                    'Aucune donnée disponible.</p>')
                continue

            # Reconstruction historique si une date est sélectionnée
            date_limit = None
            if rec.date_consultation:
                date_limit = fields.Datetime.to_string(
                    _dt.combine(
                        fields.Date.from_string(str(rec.date_consultation)),
                        _dt.max.time()))
                children = children.filtered(
                    lambda p: p.create_date and p.create_date <= date_limit)

            def _hist_val(plan_id, field_name, default, is_int=False):
                if not date_limit:
                    return default
                tracking = self.env['mail.tracking.value'].sudo().search([
                    ('mail_message_id.res_id', '=', plan_id),
                    ('mail_message_id.model', '=', 'nc_management.plan_action_smi'),
                    ('field', '=', field_name),
                    ('mail_message_id.date', '<=', date_limit),
                ], order='id desc', limit=1)
                if not tracking:
                    return default
                return tracking.new_value_integer if is_int else (tracking.new_value_char or default)

            # Toutes les natures de la sélection, même celles à zéro
            sel = rec._fields['nature'].selection
            nature_labels = dict(sel if not callable(sel) else sel(rec))
            all_natures = [code for code, _ in (sel if not callable(sel) else sel(rec))]

            rows = []
            for nat in all_natures:
                cat   = children.filtered(lambda p: p.nature == nat)
                total = len(cat)
                eff   = sum(1 for p in cat if _hist_val(p.id, 'efficacite', p.efficacite) == 'oui')
                neff  = sum(1 for p in cat if _hist_val(p.id, 'efficacite', p.efficacite) == 'non')
                r100  = sum(1 for p in cat if _hist_val(p.id, 'avancement', p.avancement, is_int=True) == 100)
                r50p  = sum(1 for p in cat if 50 < _hist_val(p.id, 'avancement', p.avancement, is_int=True) < 100)
                r50m  = sum(1 for p in cat if _hist_val(p.id, 'avancement', p.avancement, is_int=True) <= 50)
                taux  = round(eff / total * 100, 1) if total else 0.0
                rows.append(dict(nat=nat, label=nature_labels.get(nat, nat),
                                 total=total, eff=eff, neff=neff,
                                 r100=r100, r50p=r50p, r50m=r50m, taux=taux))

            # ── Tableau ────────────────────────────────────────────
            thead = (
                '<thead><tr style="background:#2c3e50;color:white;font-weight:bold;">'
                '<th style="{thl}">Catégorie</th>'
                '<th style="{th}">Efficace</th>'
                '<th style="{th}">Non Efficace</th>'
                '<th style="{th}">Réalisé 100%</th>'
                '<th style="{th}">Réalisé &gt;50%</th>'
                '<th style="{th}">Réalisé &lt;50%</th>'
                '<th style="{th}">Taux Efficacité%</th>'
                '<th style="{th}">Total</th>'
                '</tr></thead>'
            ).format(th=th, thl=thl)

            tbody = ''
            for i, r in enumerate(rows):
                bg  = '#ffffff' if i % 2 == 0 else '#f4f4f4'
                bc  = badge(r['taux'])
                cc  = '#1a2e5a'
                bdg = ('<span style="background:{bc};color:white;padding:3px 10px;'
                       'border-radius:12px;font-weight:bold;font-size:12px;">'
                       '{t:.1f}%</span>').format(bc=bc, t=r['taux'])
                tbody += (
                    '<tr style="background:{bg};">'
                    '<td style="{tdl}"><span style="color:{cc};font-weight:bold;">'
                    '{label}</span></td>'
                    '<td style="{tdc};color:#1fa255;font-weight:bold;">{eff}</td>'
                    '<td style="{tdc};color:#d44535;font-weight:bold;">{neff}</td>'
                    '<td style="{tdc}">{r100}</td>'
                    '<td style="{tdc}">{r50p}</td>'
                    '<td style="{tdc}">{r50m}</td>'
                    '<td style="{tdc}">{bdg}</td>'
                    '<td style="{tdc};font-weight:bold;">{total}</td>'
                    '</tr>'
                ).format(bg=bg, tdl=tdl, tdc=tdc, cc=cc,
                         label=r['label'], eff=r['eff'], neff=r['neff'],
                         r100=r['r100'], r50p=r['r50p'], r50m=r['r50m'],
                         bdg=bdg, total=r['total'])

            table = (
                '<table style="width:100%;border-collapse:collapse;font-size:13px;'
                'box-shadow:0 1px 3px rgba(0,0,0,.1);border-radius:6px;overflow:hidden;">'
                '{thead}<tbody>{tbody}</tbody></table>'
            ).format(thead=thead, tbody=tbody)

            # ── Graphique barres verticales ────────────────────────
            chart_h = 160  # hauteur max des barres (px)
            label_h = 80   # hauteur réservée aux étiquettes (px)

            cols = ''
            for i, r in enumerate(rows):
                cc    = rec._CAT_COLORS[i % 4]
                pct   = min(int(r['taux']), 100)
                bar_h = int(pct * chart_h / 100) if pct > 0 else 0
                cols += (
                    '<div style="display:flex;flex-direction:column;align-items:center;'
                    'flex:1;min-width:28px;">'
                    '<span style="font-size:9px;font-weight:bold;color:{cc};'
                    'min-height:14px;line-height:14px;">{taux:.0f}%</span>'
                    '<div style="width:70%;height:{bh}px;background:{cc};'
                    'border-radius:3px 3px 0 0;min-width:16px;"></div>'
                    '<div style="height:{lh}px;display:flex;justify-content:center;'
                    'align-items:flex-start;padding-top:4px;overflow:hidden;">'
                    '<span style="writing-mode:vertical-rl;transform:rotate(180deg);'
                    'font-size:9px;color:#444;font-weight:bold;">{label}</span>'
                    '</div>'
                    '</div>'
                ).format(cc=cc, taux=r['taux'], bh=bar_h, lh=label_h,
                         label=r['label'])

            chart = (
                '<div style="margin-top:24px;">'
                '<p style="font-weight:bold;font-size:14px;margin-bottom:10px;'
                'color:#2c3e50;">Taux d\'efficacité par catégorie (%)</p>'
                '<div style="display:flex;align-items:flex-end;gap:4px;'
                'padding:10px 10px 0 10px;background:white;'
                'border-radius:4px 4px 0 0;'
                'border-left:2px solid #dee2e6;border-top:1px solid #dee2e6;">'
                '{cols}</div>'
                '<div style="height:2px;background:#dee2e6;margin-left:2px;"></div>'
                '</div>'
            ).format(cols=cols)

            rec.analyse_html = (
                '<div style="font-family:Arial,sans-serif;padding:16px;">'
                '{table}{chart}</div>'
            ).format(table=table, chart=chart)

    @api.multi
    def _get_analyse_rows(self):
        """Retourne les données par catégorie pour le rapport PDF."""
        self.ensure_one()
        children = self.child_plan_ids
        sel = self._fields['nature'].selection
        nature_list = sel if not callable(sel) else sel(self)
        rows = []
        for i, (nat, label) in enumerate(nature_list):
            cat   = children.filtered(lambda p, n=nat: p.nature == n)
            total = len(cat)
            eff   = sum(1 for p in cat if p.efficacite == 'oui')
            neff  = sum(1 for p in cat if p.efficacite == 'non')
            r100  = sum(1 for p in cat if p.avancement == 100)
            r50p  = sum(1 for p in cat if 50 < p.avancement < 100)
            r50m  = sum(1 for p in cat if p.avancement <= 50)
            taux  = round(eff / total * 100, 1) if total else 0.0
            badge = '#1fa255' if taux > 80 else ('#cc8800' if taux >= 50 else '#d44535')
            bar_h = int(taux * 120 / 100) if taux > 0 else 0
            rows.append({
                'label': label, 'total': total,
                'eff': eff, 'neff': neff,
                'r100': r100, 'r50p': r50p, 'r50m': r50m,
                'taux': taux, 'badge': badge,
                'color': self._CAT_COLORS[i % 4],
                'bar_h': bar_h,
                'spacer_h': 120 - bar_h,
            })
        return rows

    # ── Statistiques plan global (calculées) ──────────────────────
    nb_plans_integres = fields.Integer(
        'Nb plans intégrés', compute='_compute_global_stats')
    avancement_global = fields.Integer(
        'Avancement global (%)', compute='_compute_global_stats')
    nb_realises       = fields.Integer('Plans réalisés',       compute='_compute_global_stats')
    nb_en_cours       = fields.Integer('Plans en cours',       compute='_compute_global_stats')
    nb_non_realises   = fields.Integer('Plans non réalisés',   compute='_compute_global_stats')
    nb_en_retard      = fields.Integer('En retard',            compute='_compute_global_stats')
    taux_realisation  = fields.Integer('Taux de réalisation (%)', compute='_compute_global_stats')
    taux_efficacite   = fields.Integer("Taux d'efficacité (%)",   compute='_compute_global_stats')
    etat_global      = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('en_cours',  'En cours'),
        ('cloture',   'Clôturé'),
    ], string='État', compute='_compute_etat_global')

    @api.depends('child_plan_ids', 'submission_state')
    def _compute_etat_global(self):
        for rec in self:
            if rec.submission_state == 'cloture':
                rec.etat_global = 'cloture'
            elif rec.child_plan_ids:
                rec.etat_global = 'en_cours'
            else:
                rec.etat_global = 'brouillon'

    @api.depends('child_plan_ids.avancement', 'child_plan_ids.state',
                 'child_plan_ids.is_late', 'child_plan_ids.efficacite',
                 'filter_nature', 'filter_direction_id')
    def _compute_global_stats(self):
        for rec in self:
            children = rec.child_plan_ids
            if rec.filter_nature:
                children = children.filtered(
                    lambda c: c.nature == rec.filter_nature)
            if rec.filter_direction_id:
                children = children.filtered(
                    lambda c: c.direction_id == rec.filter_direction_id)
            nb = len(children)
            rec.nb_plans_integres = nb
            rec.avancement_global = int(sum(c.avancement for c in children) / nb) if nb else 0
            rec.nb_realises      = sum(1 for c in children if c.avancement >= 100)
            rec.nb_en_cours      = sum(1 for c in children if 0 < c.avancement < 100)
            rec.nb_non_realises  = sum(1 for c in children if c.avancement == 0)
            rec.nb_en_retard     = sum(1 for c in children if c.is_late)
            nb_efficaces         = sum(1 for c in children if c.efficacite == 'oui')
            rec.taux_realisation = int(rec.nb_realises / nb * 100) if nb else 0
            rec.taux_efficacite  = int(nb_efficaces / nb * 100) if nb else 0

    @api.depends('date_prevue', 'state')
    def _compute_is_late(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_late = bool(
                rec.date_prevue and
                rec.date_prevue < today and
                rec.state != 'done'
            )

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        if self.is_global:
            raise UserError("La duplication du Plan d'Amélioration SMI n'est pas autorisée.")
        return super(PlanActionSmi, self).copy(default=default)

    @api.model
    def create(self, vals):
        is_global = vals.get('is_global') or self._context.get('default_is_global')
        if vals.get('name', 'New') == 'New' and is_global:
            import re as _re_create
            from datetime import date as _date
            if is_global and 'is_global' not in vals:
                vals['is_global'] = True
            date_ref = vals.get('mois_reception')
            if date_ref:
                if isinstance(date_ref, str):
                    date_ref = _date(*[int(x) for x in date_ref[:10].split('-')])
            else:
                date_ref = _date.today()
            year = date_ref.year
            # Trouver le plus grand numéro séquentiel existant pour cette année
            existing = self.search([('is_global', '=', True),
                                    ('name', 'like', '-%d' % year)])
            _re_seq = _re_create.compile(r'^SMI(\d+)-%d$' % year)
            max_seq = 0
            for p in existing:
                m = _re_seq.match(p.name or '')
                if m:
                    max_seq = max(max_seq, int(m.group(1)))
            vals['name'] = 'SMI%02d-%d' % (max_seq + 1, year)
        # Nouveau cycle de vie : plans liés à un Plan d'Amélioration (niveau 2)
        if (vals.get('improvement_plan_id') or
                vals.get('direct_global_plan_id')):
            if 'state' not in vals:
                vals['state'] = 'en_cours'
        # Numérotation SMI/PLAN/YYYY/NNNN uniquement pour les plans directs RMQSE
        if (vals.get('name', 'New') == 'New' and
                vals.get('direct_global_plan_id') and
                not vals.get('improvement_plan_id')):
            seq = self.env['ir.sequence'].next_by_code(
                'nc_management.smi_action_plan')
            if seq:
                vals['name'] = seq
        # Auto-numérotation Plan01-2026 pour tous les plans individuels
        if (vals.get('name', 'New') == 'New' and not is_global and
                not vals.get('direct_global_plan_id')):
            import re as _re_plan
            from datetime import date as _date_plan
            year = _date_plan.today().year
            existing = self.search([
                ('is_global', '=', False),
                ('direct_global_plan_id', '=', False),
                ('name', 'like', 'Plan%-' + str(year)),
            ])
            _re_p = _re_plan.compile(r'^Plan(\d+)-%d$' % year)
            max_seq = 0
            for p in existing:
                m = _re_p.match(p.name or '')
                if m:
                    max_seq = max(max_seq, int(m.group(1)))
            vals['name'] = 'Plan%02d-%d' % (max_seq + 1, year)

        # Si ce plan est ajouté à un Plan d'Amélioration déjà soumis,
        # le relier automatiquement au plan global RMQSE en cours.
        _notify_rmqse_plan = None
        if vals.get('improvement_plan_id') and not vals.get('global_plan_id'):
            improvement_plan = self.env[
                'nc_management.smi_improvement_plan'].sudo().browse(
                vals['improvement_plan_id'])
            if improvement_plan.state == 'soumis':
                rmqse_plan = self.sudo().search([
                    ('is_global', '=', True),
                    ('submission_state', '!=', 'cloture'),
                ], order='create_date desc', limit=1)
                if rmqse_plan:
                    vals['global_plan_id'] = rmqse_plan.id
                    vals.setdefault('submission_state', 'integre')
                    _notify_rmqse_plan = rmqse_plan

        record = super(PlanActionSmi, self).create(vals)

        # Notifier le plan RMQSE du nouvel ajout
        if _notify_rmqse_plan:
            from datetime import datetime as _dt_notify
            imp = record.sudo().improvement_plan_id
            direction = imp.direction_id.name if imp.direction_id else '-'
            now_str = _dt_notify.now().strftime('%d/%m/%Y à %H:%M')
            _notify_rmqse_plan.sudo().message_post(
                body=(
                    '<p>Nouveau plan d\'action ajouté après soumission — '
                    'Direction <b>%s</b> : <b>%s</b><br/>'
                    '<em>Ajouté par %s le %s</em></p>'
                ) % (direction, record.name, self.env.user.name, now_str),
                message_type='notification',
                subtype='mail.mt_comment',
            )

        return record

    @api.multi
    def action_generate_plan_number(self):
        self.ensure_one()
        if self.name != 'New':
            raise UserError(
                "La référence '%s' a déjà été assignée." % self.name
            )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Générer le numéro du plan',
            'res_model': 'nc_management.plan_number_wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'nc_management.view_plan_number_wizard_form').id,
            'target': 'new',
            'context': {'default_plan_id': self.id},
        }

    @api.onchange('efficacite')
    def _onchange_efficacite(self):
        if not self.efficacite:
            return
        # Nouveau cycle de vie (plans liés à un Plan d'Amélioration)
        if self.improvement_plan_id or self.direct_global_plan_id:
            if self.efficacite == 'oui':
                self.state = 'cloture'
            # 'non' → reste 'realise', direction va modifier le plan
        else:
            # Ancien comportement
            self.state = 'done'

    @api.onchange('avancement')
    def _onchange_avancement_smi(self):
        """Gestion du cycle de vie basé sur l'avancement (nouveau système)."""
        if not (self.improvement_plan_id or self.direct_global_plan_id):
            return
        if self.state == 'cloture':
            # Plan clôturé = définitif, aucune modification
            self.avancement = min(self.avancement, 100)
            return
        if self.avancement >= 100:
            self.avancement = 100
            if self.state != 'realise':
                self.state = 'realise'
        else:
            if self.state == 'realise':
                # La direction remet le plan en cours → reset efficacité
                self.state = 'en_cours'
                self.efficacite = False

    # ── Champs suivis pour notification dans le plan global ───────
    _GLOBAL_TRACKED_FIELDS = [
        'action', 'causes', 'description',
        'date_prevue', 'date_realisation',
        'avancement', 'efficacite',
        'responsable_id', 'state', 'moyens',
    ]
    _GLOBAL_FIELD_LABELS = {
        'action':           'Action',
        'causes':           'Causes',
        'description':      'Description',
        'date_prevue':      'Date prévue',
        'date_realisation': 'Date de réalisation',
        'avancement':       'Avancement (%)',
        'efficacite':       'Efficacité',
        'responsable_id':   'Responsable',
        'state':            'État',
        'moyens':           'Moyens',
    }

    @api.multi
    def write(self, vals):
        # ── Transitions d'état pour le nouveau cycle de vie ───────
        if not self.env.context.get('_skip_smi_state'):
            for rec in self:
                rec_s = rec.sudo()
                if not (rec_s.improvement_plan_id or rec_s.direct_global_plan_id):
                    break  # ancien système, géré après
                current_state = vals.get('state', rec_s.state)
                if current_state == 'cloture':
                    break  # plan clôturé = immuable
                av = vals.get('avancement', rec_s.avancement)
                if 'efficacite' in vals:
                    eff = vals['efficacite']
                    if eff == 'oui':
                        vals['state'] = 'cloture'
                    elif not eff and av < 100:
                        vals['state'] = 'en_cours'
                elif 'avancement' in vals:
                    if av >= 100:
                        if current_state not in ('cloture', 'realise'):
                            vals.setdefault('state', 'realise')
                        vals['avancement'] = 100
                    elif av < 100 and current_state == 'realise':
                        vals['state'] = 'en_cours'
                        if 'efficacite' not in vals:
                            vals['efficacite'] = False
                break  # formulaire = un seul record à la fois

        # Ancien comportement compatibilité
        if vals.get('efficacite') and 'state' not in vals:
            # Vérifier si c'est un ancien plan (sans improvement_plan_id)
            for rec in self:
                rec_s = rec.sudo()
                if not rec_s.improvement_plan_id and not rec_s.direct_global_plan_id:
                    vals['state'] = 'done'
                break

        # ── Sauvegarder les anciennes valeurs pour comparaison ────
        records_data = {}
        tracked = self._GLOBAL_TRACKED_FIELDS
        if any(f in vals for f in tracked):
            for rec in self:
                rec_s = rec.sudo()
                global_plan = None
                if rec_s.improvement_plan_id:
                    global_plan = rec_s.improvement_plan_id.global_plan_id
                elif rec_s.direct_global_plan_id:
                    global_plan = rec_s.direct_global_plan_id
                if not global_plan:
                    continue
                old_vals = {}
                for f in tracked:
                    v = getattr(rec_s, f)
                    if hasattr(v, 'id'):
                        old_vals[f] = (v.id, v.name)
                    else:
                        old_vals[f] = v
                records_data[rec.id] = {
                    'global_plan': global_plan,
                    'old': old_vals,
                    'direction': (
                        rec_s.improvement_plan_id.direction_id.name
                        if rec_s.improvement_plan_id and
                        rec_s.improvement_plan_id.direction_id
                        else '-'),
                    'ref': rec_s.name,
                }

        res = super(PlanActionSmi, self).write(vals)

        # ── Poster les modifications dans le chatter du plan global ──
        if records_data:
            from datetime import datetime as _dt
            now_str = _dt.now().strftime('%d/%m/%Y à %H:%M')
            user_name = self.env.user.name

            for rec in self:
                if rec.id not in records_data:
                    continue
                data = records_data[rec.id]
                global_plan = data['global_plan']
                old = data['old']
                changes = []
                labels = self._GLOBAL_FIELD_LABELS
                for f, new_val in vals.items():
                    if f not in tracked:
                        continue
                    old_raw = old.get(f)
                    if isinstance(old_raw, tuple):
                        old_id, old_name = old_raw
                        old_display = old_name or '-'
                    else:
                        old_display = old_raw if old_raw is not None else '-'
                    if isinstance(new_val, int) and f == 'responsable_id':
                        emp = self.env['hr.employee'].browse(new_val)
                        new_display = emp.name if emp.exists() else str(new_val)
                    elif new_val is None or new_val is False:
                        new_display = '-'
                    else:
                        new_display = str(new_val)
                    if str(old_display) != str(new_display):
                        label = labels.get(f, f)
                        changes.append(
                            '<li><b>%s</b> : %s &rarr; %s</li>' %
                            (label, old_display, new_display))
                if changes:
                    body = (
                        '<p>Direction <b>%s</b> a modifié le plan '
                        '<b>%s</b> :</p>'
                        '<ul>%s</ul>'
                        '<p><em>Modifié par %s le %s</em></p>'
                    ) % (
                        data['direction'], data['ref'],
                        ''.join(changes),
                        user_name, now_str,
                    )
                    global_plan.sudo().message_post(
                        body=body,
                        message_type='notification',
                        subtype='mail.mt_comment',
                    )

        # ── Ancien mécanisme date_maj (compat) ────────────────────
        if not self.env.context.get('_skip_date_maj') and 'date_maj' not in vals:
            # Ne pas toucher date_maj si seul date_consultation change
            if set(vals.keys()) - {'date_consultation', 'filter_nature', 'filter_direction_id'}:
                plans_amelioration = self.filtered('is_global')
                if plans_amelioration:
                    for plan in plans_amelioration:
                        plan.with_context(_skip_date_maj=True).write({
                            'date_maj': fields.Datetime.now(),
                        })
                parents = self.filtered(
                    lambda r: not r.is_global and r.global_plan_id
                ).mapped('global_plan_id')
                if parents:
                    parents.with_context(_skip_date_maj=True).write(
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
    def action_open_send_plan_wizard(self):
        self.ensure_one()
        qm_group = self.env.ref('nc_management.group_responsable_qualite', raise_if_not_found=False)
        qm_emp_ids = self.env['hr.employee'].search([
            ('user_id', 'in', qm_group.users.ids if qm_group else [])
        ]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Envoyer à la Responsable Qualité',
            'res_model': 'nc_management.send_plan_wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('nc_management.view_send_plan_wizard').id,
            'target': 'new',
            'context': {
                'default_plan_id': self.id,
                'qm_employee_ids': qm_emp_ids,
            },
        }

    @api.multi
    def action_envoyer_rmqse(self):
        self.ensure_one()
        if self.submission_state != 'brouillon':
            raise UserError("Ce plan a déjà été soumis à la Responsable Qualité.")
        if self.env.uid != self.create_uid.id:
            raise UserError("Seul le créateur peut soumettre ce plan.")
        if not self.is_global and not self.nature:
            raise UserError("Veuillez renseigner la Nature avant d'envoyer le plan.")

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
        """Ouvre le wizard Analyse Efficacité Globale pour ce plan clôturé."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Analyse Efficacité Globale",
            'res_model': 'nc_management.plan_efficacite_wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'nc_management.view_plan_efficacite_wizard_form').id,
            'target': 'new',
            'context': {'default_plan_id': self.id},
        }

    @api.multi
    def action_consolider_tous(self):
        """Pré-crée le wizard et ses lignes en base, puis ouvre le popup."""
        self.ensure_one()
        plans = self.env['nc_management.plan_action_smi'].search([
            ('is_global', '=', False),
            ('global_plan_id', '=', False),
            '|',
            ('create_uid', '=', self.env.uid),
            ('sent_to_rmqse', '=', True),
        ])
        wizard = self.env['nc_management.consolidate_wizard'].create({
            'global_plan_id': self.id,
        })
        for plan in plans:
            self.env['nc_management.consolidate_wizard.line'].create({
                'wizard_id': wizard.id,
                'plan_id': plan.id,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Consolider des plans',
            'res_model': 'nc_management.consolidate_wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @api.multi
    def action_open_consulter_version_wizard(self):
        """Ouvre le popup de sélection de date pour consulter une version passée."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Consulter une version passée',
            'res_model': 'nc_management.consulter_version_wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'nc_management.view_consulter_version_wizard_form').id,
            'target': 'new',
            'context': {'default_plan_id': self.id},
        }

    @api.multi
    def action_retour_actuel_plan(self):
        """Efface date_consultation sur ce plan et revient au plan actif courant."""
        self.ensure_one()
        self.with_context(_skip_date_maj=True).write({'date_consultation': False})
        inner = self.env['nc_management.plan_action_smi'].action_open_global_plan()
        return {
            'type': 'ir.actions.client',
            'tag': 'nc_management.clear_and_navigate',
            'params': {'inner_action': inner},
        }

    @api.multi
    def action_print_global(self):
        self.ensure_one()
        return self.env.ref(
            'nc_management.action_report_analyse_efficacite'
        ).report_action(self)

    @api.multi
    def action_print_plan_smi_pdf(self):
        self.ensure_one()
        return self.env.ref(
            'nc_management.action_report_plan_action_smi_pdf'
        ).report_action(self)

    @api.multi
    def action_supprimer_plan(self):
        self.ensure_one()
        self.unlink()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_open_new_child_plan_form(self):
        self.ensure_one()
        view_id = self.env.ref('nc_management.view_plan_smi_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': "Nouveau plan d'action",
            'res_model': 'nc_management.plan_action_smi',
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'target': 'new',
            'context': {
                'default_global_plan_id': self.id,
            },
        }

    @api.multi
    def action_cloturer_plan(self):
        """Clôture le plan actuel et crée automatiquement le suivant
        en y intégrant tous les plans créés/reçus après la date_maj courante."""
        self.ensure_one()
        if self.submission_state == 'cloture':
            raise UserError("Ce Plan d'Amélioration est déjà clôturé.")

        if self.mois_reception:
            from dateutil.relativedelta import relativedelta as _rd
            from datetime import date as _date_cls
            date_creation = fields.Date.from_string(str(self.mois_reception))
            date_min = date_creation + _rd(months=3)
            if _date_cls.today() < date_min:
                raise UserError(
                    "Ce Plan d'Amélioration ne peut être clôturé qu'au moins "
                    "3 mois après sa date de création.\n"
                    "Date minimale de clôture : %s"
                    % date_min.strftime('%d/%m/%Y'))

        cutoff = self.date_maj or self.create_date

        # 1. Clôturer le plan actuel
        self.with_context(_skip_date_maj=True).write(
            {'submission_state': 'cloture'})

        # 2. Créer le nouveau Plan d'Amélioration
        new_plan = self.with_context(_skip_date_maj=True).create({
            'name': 'New',
            'is_global': True,
            'submission_state': 'brouillon',
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
    def action_open_global_plan(self):
        """Ouvre directement le Plan d'Amélioration en cours (le plus récent non clôturé).
        Si aucun n'existe, en crée un nouveau."""
        plan = self.search([
            ('is_global', '=', True),
            ('submission_state', '!=', 'cloture'),
        ], order='create_date desc', limit=1)
        if not plan:
            plan = self.search([
                ('is_global', '=', True),
            ], order='create_date desc', limit=1)
        if not plan:
            plan = self.create({
                'is_global': True,
                'submission_state': 'brouillon',
            })
        view_id = self.env.ref('nc_management.view_plan_smi_form_global').id
        return {
            'type': 'ir.actions.act_window',
            'name': "Plan d'Action d'Amélioration SMI",
            'res_model': 'nc_management.plan_action_smi',
            'res_id': plan.id,
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'view_id': view_id,
            'target': 'current',
            'context': {'default_is_global': True},
        }

    @api.model
    def action_open_analyse_efficacite(self):
        """Ouvre directement le Plan d'Amélioration global le plus récent."""
        plan = self.search([
            ('is_global', '=', True),
        ], order='create_date desc', limit=1)
        if not plan:
            raise UserError("Aucun plan d'amélioration global disponible.")
        stored_id = self.env.ref('nc_management.action_analyse_efficacite_form').id
        view_id = self.env.ref('nc_management.view_plan_smi_form_analyse').id
        return {
            'id': stored_id,
            'type': 'ir.actions.act_window',
            'name': "Analyse d'Efficacité",
            'res_model': 'nc_management.plan_action_smi',
            'res_id': plan.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'flags': {'create': False},
        }

    @api.multi
    def action_open_analyser_wizard(self):
        """Ouvre le popup de sélection de date pour analyser l'efficacité à une date passée."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Analyser l'efficacité à une date",
            'res_model': 'nc_management.consulter_version_wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'nc_management.view_analyser_efficacite_wizard_form').id,
            'target': 'new',
            'context': {
                'default_plan_id': self.id,
                'default_return_view_ref': 'nc_management.view_plan_smi_form_analyse',
            },
        }

    @api.multi
    def action_retour_analyse_actuelle(self):
        """Efface la date de consultation et revient à l'analyse en temps réel."""
        self.ensure_one()
        self.with_context(_skip_date_maj=True).write({'date_consultation': False})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.plan_action_smi',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'nc_management.view_plan_smi_form_analyse').id,
            'target': 'current',
            'flags': {'create': False},
        }

    @api.model
    def _auto_create_global_plan(self):
        from datetime import date as _date
        from dateutil.relativedelta import relativedelta

        today = _date.today()

        # Ne créer un nouveau plan que s'il n'y a aucun plan actif (non clôturé)
        if self.search([('is_global', '=', True),
                        ('submission_state', '!=', 'cloture')], limit=1):
            return True

        submitted = self.search([
            ('submission_state', '=', 'soumis'),
            ('is_global', '=', False),
            ('global_plan_id', '=', False),
        ])
        if not submitted:
            return True

        global_plan = self.create({
            'name': 'New',
            'is_global': True,
            'mois_reception': today.strftime('%Y-%m-%d'),
            'submission_state': 'brouillon',
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
        ('plan_smi', 'Plan d\'Action d\'Amélioration SMI'),
    ], string='Type de Document', required=True)
    revision_number = fields.Integer(string='N° Révision', required=True)
    revision_date = fields.Date(string='Date de Révision', required=True, default=fields.Date.today)
    reference = fields.Char(string='Référence')
    description = fields.Text(string='Modification apportée')
    etat = fields.Selection([
        ('valable', 'Valable'),
        ('obsolete', 'Obsolète'),
    ], string='État', default='obsolete', required=True)

    revision_number_link = fields.Html(string='N° Révision', compute='_compute_revision_number_link')

    @api.depends('revision_number', 'doc_type')
    def _compute_revision_number_link(self):
        for rec in self:
            if rec.doc_type == 'plan_smi':
                url = '/report/pdf/nc_management.report_plan_smi_revision_content/%s' % rec.id
            else:
                url = '/report/pdf/nc_management.report_revision_template/%s' % rec.id
            rec.revision_number_link = '<a href="%s" target="_blank" style="font-weight:bold; color:#00A09D;">%s</a>' % (url, rec.revision_number)

    name = fields.Char(string='Révision', compute='_compute_name', store=True)

    @api.depends('doc_type', 'revision_number')
    def _compute_name(self):
        type_labels = {'fnc': 'FNC', 'fac': 'FAC', 'plan_smi': 'PSMI'}
        for rec in self:
            type_str = type_labels.get(rec.doc_type, '')
            rec.name = "%s - Rev %02d" % (type_str, rec.revision_number)

    def _obsolete_others(self):
        for rec in self:
            if rec.etat == 'valable':
                others = self.search([
                    ('doc_type', '=', rec.doc_type),
                    ('id', '!=', rec.id),
                    ('etat', '=', 'valable'),
                ])
                if others:
                    others.write({'etat': 'obsolete'})

    @api.model
    def create(self, vals):
        rec = super(DocumentRevision, self).create(vals)
        rec._obsolete_others()
        return rec

    @api.multi
    def write(self, vals):
        res = super(DocumentRevision, self).write(vals)
        if vals.get('etat') == 'valable':
            self._obsolete_others()
        return res


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
                lambda f: f.state in ['in_progress', 'validated']))
            realise_50moins = len(fac_recs.filtered(
                lambda f: f.state in ['draft', 'submitted']))
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

        # 12 catégories pour le graphique — basées sur plan.nature
        _CHART_NATURES = [
            ('nc_produit',               'NC Produit'),
            ('reclamation_pi',           'Réclamation Client'),
            ('environnement',            'Environnement'),
            ('sst',                      'SST'),
            ('audit_externe',            'Audit Externe'),
            ('audit_interne',            'Audit Interne'),
            ('swot',                     'SWOT'),
            ('risque',                   'Risque'),
            ('objectif_non_atteint',     'Objectif non atteint'),
            ('decision_revue_direction', 'Décision revue direction'),
            ('amelioration',             'Amélioration'),
            ('nc_reglementaire',         'NC réglementaire'),
        ]
        # Plans intégrés dans un plan global (submission_state == 'integre')
        plan_model     = self.env['nc_management.plan_action_smi']
        integrated_plans = plan_model.search([
            ('is_global',        '=', False),
            ('submission_state', '=', 'integre'),
        ])
        categories_chart = []
        for code, label in _CHART_NATURES:
            cat   = integrated_plans.filtered(lambda p, c=code: p.nature == c)
            total = len(cat)
            eff   = sum(1 for p in cat if p.efficacite == 'oui')
            taux  = round(eff / total * 100, 1) if total else 0.0
            categories_chart.append({'label': label, 'taux': taux})

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
            'categories_chart': categories_chart,
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
    def get_stats(self, period=None, target_year=None, target_month=None):
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        import calendar as cal_mod

        fnc = self.env['nc_management.nonconformity']
        fac = self.env['nc_management.corrective_action']
        plan = self.env['nc_management.plan_action_smi']
        today = date.today()
        if target_year and target_month:
            ref_date = date(int(target_year), int(target_month), 1)
        else:
            ref_date = today
        period_months = {
            '1m': 1,
            '6m': 6,
            '1y': 12,
        }.get(period or '1m', 1)
        period_end = (ref_date.replace(day=1) + relativedelta(months=1))
        period_start = ref_date.replace(day=1) - relativedelta(months=period_months - 1)

        fnc_period_domain = [
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
        ]
        fac_period_domain = [
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
        ]
        received_fnc_period_domain = [
            ('date_envoi', '>=', period_start.strftime('%Y-%m-%d')),
            ('date_envoi', '<', period_end.strftime('%Y-%m-%d')),
            ('state', '!=', 'draft'),
            ('create_uid', '!=', self.env.uid),
        ]
        received_fnc_ids = fnc.search(received_fnc_period_domain).ids
        fac_received_period_domain = [
            '|',
            ('fnc_id', 'in', received_fnc_ids),
            '&', '&',
            ('date_envoi', '>=', period_start.strftime('%Y-%m-%d')),
            ('date_envoi', '<', period_end.strftime('%Y-%m-%d')),
            ('create_uid', '!=', self.env.uid),
        ]

        # Domaine FNC créées par la RMQSE sur la période (toutes, y compris Audit Externe)
        own_fnc_domain = [
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
            ('create_uid', '=', self.env.uid),
        ]
        # Domaine FNC créées par RMQSE (Total FNC/FAC + Évolution) — y compris Audit Externe :
        # les compteurs Total FNC/FAC comptabilisent aussi les FNC/FAC Audit Externe créées par la RMQSE
        combined_fnc_domain = own_fnc_domain
        combined_fnc_ids = fnc.search(combined_fnc_domain).ids
        combined_fac_domain = [
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
            ('fnc_id', 'in', combined_fnc_ids),
        ]

        # ── FNC counters (créées par RMQSE, y compris Audit Externe) ──
        total_fnc     = len(combined_fnc_ids)
        fnc_cours     = fnc.search_count(combined_fnc_domain + [('state','=','in_progress')])
        fnc_envoyes   = fnc.search_count(combined_fnc_domain + [('state','=','submitted')])
        fnc_closed    = fnc.search_count(combined_fnc_domain + [('state','=','closed')])
        fnc_validated = fnc.search_count(combined_fnc_domain + [('state','=','validated')])
        taux_cloture  = round(fnc_validated / total_fnc * 100, 1) if total_fnc else 0
        fnc_brouillon = fnc.search_count(combined_fnc_domain + [('state','=','draft')])
        # Audit interne : FNC reçues des autres directions, de type audit interne
        # Audit externe : FNC créées par la RMQSE (boutons audit externe), de type audit externe
        fnc_audit_interne = fnc.search_count(received_fnc_period_domain + [('type_audit_interne','=',True)])
        fnc_audit_externe = fnc.search_count(own_fnc_domain + [('type_audit_externe','=',True)])

        limit7 = str(today - timedelta(days=7))
        limit1 = str(today - timedelta(days=1))
        fnc_retard_recs = fnc.search_read([
            ('state', '=', 'in_progress'),
            ('date', '<=', limit7),
            ('create_uid', '=', self.env.uid),
        ], ['name', 'direction_id', 'service_id', 'date'], limit=10)
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
                'audit_interne': 0,
                'audit_externe': 0,
                'achat': 0,
                'reception': 0,
                'dysfonctionnement': 0,
                'travaux': 0,
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
                if rec.type_audit_interne:
                    counts['audit_interne'] += 1
                if rec.type_audit_externe:
                    counts['audit_externe'] += 1
                if rec.type_achat:
                    counts['achat'] += 1
                if rec.type_reception:
                    counts['reception'] += 1
                if rec.type_dysfonctionnement:
                    counts['dysfonctionnement'] += 1
                if rec.type_travaux:
                    counts['travaux'] += 1
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

        # ── FAC counters (liées aux FNC créées par RMQSE) ──
        total_fac          = fac.search_count(combined_fac_domain)
        fac_open           = fac.search_count(combined_fac_domain + [('state','=','submitted')])
        fac_verif          = fac.search_count(combined_fac_domain + [('state','=','in_progress')])
        fac_closed         = fac.search_count(combined_fac_domain + [('state','=','closed')])
        fac_brouillon      = fac.search_count(combined_fac_domain + [('state','=','draft')])
        fac_validated      = fac.search_count(combined_fac_domain + [('state','=','validated')])
        fac_efficace       = fac.search_count(combined_fac_domain + [('actions_efficaces','=','oui')])
        taux_eff           = round(fac_efficace / total_fac * 100, 1) if total_fac else 0
        taux_validation_fac = round(fac_verif  / total_fac * 100, 1) if total_fac else 0
        taux_cloture_fac   = round(fac_closed  / total_fac * 100, 1) if total_fac else 0
        # Audit interne : FAC reçues, liées à une FNC audit interne reçue
        # Audit externe : FAC liées à une FNC audit externe créée par la RMQSE
        fac_audit_interne = fac.search_count(fac_received_period_domain + [('fnc_id.type_audit_interne','=',True)])
        fac_audit_externe = fac.search_count([
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<',  period_end.strftime('%Y-%m-%d')),
            ('fnc_id.type_audit_externe', '=', True),
            ('fnc_id.create_uid', '=', self.env.uid),
        ])
        audit_interne_total = fnc_audit_interne + fac_audit_interne
        audit_externe_total = fnc_audit_externe + fac_audit_externe

        # FAC en retard (ouvertes > 7 jours — tout le système)
        fac_retard_recs = fac.search_read(
            [('state', 'in', ['submitted', 'in_progress', 'validated']),
             ('date', '<=', limit7)],
            ['name', 'direction_id', 'date_cloture', 'state'], limit=10)
        fac_retard = len(fac_retard_recs)

        # FAC à clôturer avec urgence (toutes FAC du système — RMQSE clôture tout)
        fac_a_cloturer = []
        for f in fac.search([('state', 'in', ['submitted', 'in_progress', 'validated'])],
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

        # FAC à approuver reçues (en attente d'approbation QSE)
        fac_recues_count = fac.search_count(fac_received_period_domain + [('state','=','in_progress')])

        # ── Evolution mensuelle — FNC/FAC créées par RMQSE, hors Audit Externe (depuis mois actuel) ──
        monthly_fnc = []
        monthly_fac = []
        fr_months = ['Jan','Fév','Mar','Avr','Mai','Jui','Jul','Aoû','Sep','Oct','Nov','Déc']
        monthly_labels = []
        for i in range(period_months - 1, -1, -1):
            d = ref_date - relativedelta(months=i)
            m_start = d.replace(day=1)
            m_end = (d + relativedelta(months=1)).replace(day=1)
            m_fnc_recs = fnc.search([
                ('date', '>=', str(m_start)),
                ('date', '<', str(m_end)),
                ('create_uid', '=', self.env.uid),
                ('type_audit_externe', '=', False),
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
            'fac_validated':      fac_validated,
            'fac_audit_interne':   fac_audit_interne,
            'fac_audit_externe':   fac_audit_externe,
            'audit_interne_total': audit_interne_total,
            'audit_externe_total': audit_externe_total,
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
                'fnc': fnc.search_count(received_fnc_period_domain + [('service_id', '!=', False)]),
                'fac': fac.search_count(fac_received_period_domain + [('fnc_id.service_id', '!=', False)]),
            },
        }
        result['calendar_year'] = ref_date.year
        result['calendar_month'] = ref_date.month
        result['monthly_labels'] = monthly_labels

        result['fnc_audit'] = fnc.search_count(combined_fnc_domain + [('type_audit', '=', True)])
        result['fac_audit'] = fac.search_count([
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<',  period_end.strftime('%Y-%m-%d')),
            ('fnc_id.type_audit', '=', True),
        ])

        # Totaux globaux reçus par les autres directions (hors FNC/FAC créées par la RMQSE)
        result['global_fnc_total'] = fnc.search_count(received_fnc_period_domain)
        result['global_fac_total'] = fac.search_count(fac_received_period_domain)

        # Types globaux pour le cercle "Vue globale" — toutes directions confondues
        _all_received_fnc = fnc.search(received_fnc_period_domain)
        _all_received_fac_fnc = fac.search(fac_received_period_domain).mapped('fnc_id')
        result['global_fnc_types'] = _type_percentages(_all_received_fnc)
        result['global_fac_types'] = _type_percentages(_all_received_fac_fnc)

        # Diagramme global : FNC/FAC propres RMQSE + reçus des autres directions
        monthly_fnc_global = []
        monthly_fac_global = []
        for i in range(period_months - 1, -1, -1):
            d = ref_date - relativedelta(months=i)
            d_start = d.replace(day=1)
            d_end = (d + relativedelta(months=1)).replace(day=1)
            m_own_fnc_ids = fnc.search([
                ('date', '>=', d_start.strftime('%Y-%m-%d')),
                ('date', '<', d_end.strftime('%Y-%m-%d')),
                ('create_uid', '=', self.env.uid),
            ]).ids
            m_recv_fnc_ids = fnc.search([
                ('date_envoi', '>=', d_start.strftime('%Y-%m-%d')),
                ('date_envoi', '<', d_end.strftime('%Y-%m-%d')),
                ('state', '!=', 'draft'),
                ('create_uid', '!=', self.env.uid),
            ]).ids
            all_m_fnc_ids = list(set(m_own_fnc_ids) | set(m_recv_fnc_ids))
            monthly_fnc_global.append(len(all_m_fnc_ids))
            monthly_fac_global.append(
                fac.search_count([('fnc_id', 'in', all_m_fnc_ids)]) if all_m_fnc_ids else 0
            )
        result['monthly_fnc_global'] = monthly_fnc_global
        result['monthly_fac_global'] = monthly_fac_global

        calendar_events = {}
        received_by_date = {}
        fnc_this_month = fnc.search(received_fnc_period_domain)
        fac_this_month = fac.search(fac_received_period_domain)
        for fnc_rec in fnc_this_month:
            k = str(fnc_rec.date_envoi or fnc_rec.date)[:10]
            if k not in calendar_events:
                calendar_events[k] = {'fnc': False, 'fac': False, 'plan': False}
            calendar_events[k]['fnc'] = True
        for fac_rec in fac_this_month:
            k = str(fac_rec.date_envoi or fac_rec.date)[:10]
            if k not in calendar_events:
                calendar_events[k] = {'fnc': False, 'fac': False, 'plan': False}
            calendar_events[k]['fac'] = True
        paa = self.env['nc_management.smi_improvement_plan']
        paa_domain = [
            ('state', '=', 'soumis'),
            ('create_uid', '!=', self.env.uid),
            ('date_soumission', '>=', period_start.strftime('%Y-%m-%d')),
            ('date_soumission', '<', period_end.strftime('%Y-%m-%d')),
        ]
        paa_this_period = paa.search(paa_domain)
        result['plan_total']       = len(paa_this_period)
        result['plan_en_attente']  = len(paa_this_period)
        result['plan_integres']    = len(paa_this_period.filtered(lambda p: p.global_plan_id))
        result['plan_mes_total']      = 0
        result['plan_mes_brouillon']  = 0
        result['plan_mes_realise']    = 0
        result['plan_recus_total']    = len(paa_this_period)
        result['plan_recus_brouillon']= 0
        result['plan_recus_realise']  = 0
        for paa_rec in paa_this_period:
            plan_date = paa_rec.date_soumission
            if not plan_date:
                continue
            k = str(plan_date)[:10]
            if k not in calendar_events:
                calendar_events[k] = {'fnc': False, 'fac': False, 'plan': False}
            calendar_events[k]['plan'] = True
        result['calendar_events'] = calendar_events

        fac_a_cloturer_list = []
        for fac_rec in fac.search([('state', '=', 'validated')],
                                  order='date_validated asc', limit=8):
            delta = 0
            if fac_rec.date_validated:
                delta = (today - fields.Date.from_string(str(fac_rec.date_validated))).days
            fac_a_cloturer_list.append({
                'id': fac_rec.id,
                'name': fac_rec.name,
                'department': fac_rec.direction_id.name if fac_rec.direction_id else '',
                'days': delta,
                'state': fac_rec.state,
            })
        result['fac_a_cloturer'] = fac_a_cloturer_list

        # FAC non reçues : FAC validées par d'autres utilisateurs (pas RMQSE),
        # depuis > 7 jours, que la RMQSE doit recevoir et clôturer
        fac_non_recues_list = []
        threshold_7 = today - timedelta(days=1)  # TEST — remettre à 7 après validation
        for fac_rec in fac.search([
            ('state', '=', 'validated'),
            ('create_uid', '!=', self.env.uid),
            ('date_validated', '<=', str(threshold_7)),
        ], order='date_validated asc', limit=10):
            delta = (today - fields.Date.from_string(str(fac_rec.date_validated))).days \
                if fac_rec.date_validated else 0
            user_name = fac_rec.create_uid.name if fac_rec.create_uid else ''
            responsable_name = fac_rec.responsable_id.name if fac_rec.responsable_id else ''
            owner = responsable_name or user_name
            fac_non_recues_list.append({
                'id': fac_rec.id,
                'name': fac_rec.name,
                'fnc_name': fac_rec.fnc_id.name if fac_rec.fnc_id else '',
                'department': fac_rec.direction_id.name if fac_rec.direction_id else '',
                'days': delta,
                'owner': owner,
            })
        result['fac_non_recues'] = fac_non_recues_list

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

        def _name_initials(name):
            if not name:
                return '??'
            return ''.join([w[0].upper() for w in name.split()[:2]]) or '??'

        # FNC en retard alertes : créées par RMQSE, in_progress depuis > 7 jours
        fnc_retard_list = []
        for fnc_rec in fnc.search([
            ('state', '=', 'in_progress'),
            ('date_in_progress', '!=', False),
            ('date_in_progress', '<=', limit7),
            ('create_uid', '=', self.env.uid),
        ], limit=10):
            delta = 0
            if fnc_rec.date_in_progress:
                delta = (today - fields.Date.from_string(str(fnc_rec.date_in_progress))).days
            fnc_retard_list.append({
                'id': fnc_rec.id,
                'name': fnc_rec.name,
                'department': fnc_rec.direction_id.name if fnc_rec.direction_id else '',
                'days': delta,
                'type': _fnc_type_label(fnc_rec),
            })
        result['fnc_retard_list'] = fnc_retard_list

        # ── Alertes FAC reçues & mes FAC ────────────────────────────────────
        def _fac_alert(fac_rec, date_ref):
            delta = (today - fields.Date.from_string(str(date_ref))).days if date_ref else 0
            return {
                'id': fac_rec.id,
                'name': fac_rec.name,
                'department': fac_rec.direction_id.name if fac_rec.direction_id else '',
                'days': delta,
                'fnc_name': fac_rec.fnc_id.name if fac_rec.fnc_id else '',
            }

        # Ses FAC à valider : créées par RMQSE, en cours depuis > 1 jour (date de début <= limit7)
        mes_fac_en_cours_list = [
            _fac_alert(r, r.date)
            for r in fac.search([
                ('state', '=', 'in_progress'),
                ('create_uid', '=', self.env.uid),
                ('date', '<=', limit7),
            ], order='date asc', limit=10)
        ]

        # FAC reçues à valider : envoyées il y a > 1 jour, encore en cours
        fac_recues_en_cours_list = [
            _fac_alert(r, r.date_envoi)
            for r in fac.search([
                ('state', '=', 'in_progress'),
                ('date_envoi', '!=', False),
                ('date_envoi', '<=', limit1),
                ('create_uid', '!=', self.env.uid),
            ], order='date_envoi asc', limit=10)
        ]

        result['mes_fac_en_cours']     = mes_fac_en_cours_list
        result['fac_recues_en_cours']  = fac_recues_en_cours_list

        def _date_label(value):
            if not value:
                return ''
            # Accepte Date, Datetime ou string YYYY-MM-DD[...]
            v = str(value)[:10]
            return fields.Date.from_string(v).strftime('%d/%m/%Y')

        def _append_received(day_key, item):
            if day_key not in received_by_date:
                received_by_date[day_key] = []
            received_by_date[day_key].append(item)

        received_docs = []
        for fnc_rec in fnc.search(received_fnc_period_domain,
                                  order='date_envoi desc, id desc'):
            responsible = fnc_rec.assigned_to_id or fnc_rec.responsable_action_id
            submitter = fnc_rec.submitted_by_id
            signale = fnc_rec.signale_par_id
            sender_name = (fnc_rec.sent_by_id.name if fnc_rec.sent_by_id
                           else (signale.name if signale
                           else (submitter.name if submitter and submitter.id != self.env.uid
                           else (fnc_rec.direction_id.name if fnc_rec.direction_id else ''))))
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
                'sender_name': sender_name,
                'sender_initials': _name_initials(sender_name),
                'submitted_by_partner_id': submitter.partner_id.id if submitter else None,
                'submitted_by_name': submitter.name if submitter else '',
            }
            received_docs.append(item)
            fnc_key = str(fnc_rec.date_envoi or fnc_rec.date)[:10] if (fnc_rec.date_envoi or fnc_rec.date) else None
            if fnc_key:
                _append_received(fnc_key, item)

        for fac_rec in fac.search(fac_received_period_domain, order='date_envoi desc, date desc, id desc'):
            responsible = fac_rec.responsable_actions_id
            fnc_submitter = fac_rec.fnc_id.submitted_by_id if fac_rec.fnc_id else None
            fnc_signale = fac_rec.fnc_id.signale_par_id if fac_rec.fnc_id else None
            fac_sender_name = (fac_rec.sent_by_id.name if fac_rec.sent_by_id
                               else (fnc_signale.name if fnc_signale
                               else (fnc_submitter.name if fnc_submitter and fnc_submitter.id != self.env.uid
                               else (fac_rec.direction_id.name if fac_rec.direction_id else ''))))
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
                'sender_name': fac_sender_name,
                'sender_initials': _name_initials(fac_sender_name),
                'fnc_id': fac_rec.fnc_id.id if fac_rec.fnc_id else None,
                'state': fac_rec.state,
                'submitted_by_partner_id': fnc_submitter.partner_id.id if fnc_submitter else None,
                'submitted_by_name': fnc_submitter.name if fnc_submitter else '',
            }
            received_docs.append(item)
            fac_key = str(fac_rec.date_envoi or fac_rec.date)[:10] if (fac_rec.date_envoi or fac_rec.date) else None
            if fac_key:
                _append_received(fac_key, item)

        for paa_rec in paa_this_period:
            plan_date = paa_rec.date_soumission
            submitter = paa_rec.submitted_by_id
            plan_sender_name = (submitter.name if submitter
                                else (paa_rec.direction_id.name if paa_rec.direction_id else ''))
            org_parts = []
            if paa_rec.direction_id:
                org_parts.append(paa_rec.direction_id.name)
            if paa_rec.department_id:
                org_parts.append(paa_rec.department_id.name)
            org_label = ', '.join(org_parts) if org_parts else ''
            date_envoi_str = ''
            if plan_date:
                try:
                    from datetime import datetime as _dt2
                    dt_val = _dt2.strptime(str(plan_date)[:19], '%Y-%m-%d %H:%M:%S')
                    date_envoi_str = dt_val.strftime('%Y-%m-%d %H:%M')
                except Exception:
                    date_envoi_str = str(plan_date)[:16]
            item = {
                'id': paa_rec.id,
                'name': paa_rec.name,
                'type': "Plan d'Action d'Amélioration",
                'kind': 'Plan',
                'badge': 'purple',
                'model': 'nc_management.smi_improvement_plan',
                'department': paa_rec.direction_id.name if paa_rec.direction_id else '',
                'org_label': org_label,
                'responsible': submitter.name if submitter else '',
                'date': _date_label(plan_date),
                'date_envoi_str': date_envoi_str,
                'initials': _name_initials(submitter.name if submitter else ''),
                'sender_name': plan_sender_name,
                'sender_initials': _name_initials(plan_sender_name),
                'sent_by_name': submitter.name if submitter else '',
                'date_prevue': '',
                'submission_state': 'soumis',
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
    def get_user_stats(self, period=None, cal_year=None, cal_month=None):
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta

        uid = self.env.uid
        fnc_model = self.env['nc_management.nonconformity']
        fac_model = self.env['nc_management.corrective_action']
        plan_model = self.env['nc_management.plan_action_smi']
        today = date.today()
        fr_months = ['Jan','Fév','Mar','Avr','Mai','Jui','Jul','Aoû','Sep','Oct','Nov','Déc']

        period_months = {'1m': 1, '6m': 6, '1y': 12}.get(period or '1m', 1)
        period_end = today.replace(day=1) + relativedelta(months=1)
        period_start = today.replace(day=1) - relativedelta(months=period_months - 1)

        # Domaines tous temps (alertes, calendrier)
        user_fnc_domain_all = [('create_uid', '=', uid)]
        user_fnc_ids_all = fnc_model.search(user_fnc_domain_all).ids
        user_fac_domain_all = ['|',
            ('fnc_id', 'in', user_fnc_ids_all),
            ('responsable_id', '=', uid),
        ]

        # Domaines filtrés par période (KPI)
        user_fnc_domain = [
            ('create_uid', '=', uid),
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
        ]
        user_fnc_ids = fnc_model.search(user_fnc_domain).ids
        user_fac_domain = ['|',
            ('fnc_id', 'in', user_fnc_ids),
            '&', '&',
            ('responsable_id', '=', uid),
            ('date', '>=', period_start.strftime('%Y-%m-%d')),
            ('date', '<', period_end.strftime('%Y-%m-%d')),
        ]

        # ── KPI totals (période) ──
        fnc_total     = len(user_fnc_ids)
        fnc_brouillon = fnc_model.search_count(user_fnc_domain + [('state', '=', 'draft')])
        fnc_submitted = fnc_model.search_count(user_fnc_domain + [('state', '=', 'submitted')])
        fnc_cours     = fnc_model.search_count(user_fnc_domain + [('state', '=', 'in_progress')])
        fnc_validated = fnc_model.search_count(user_fnc_domain + [('state', '=', 'validated')])
        fnc_closed    = fnc_model.search_count(user_fnc_domain + [('state', '=', 'closed')])
        fnc_taux_validation = round((fnc_validated + fnc_closed) / fnc_total * 100) if fnc_total else 0

        fac_total     = fac_model.search_count(user_fac_domain)
        fac_brouillon = fac_model.search_count(user_fac_domain + [('state', '=', 'draft')])
        fac_submitted = fac_model.search_count(user_fac_domain + [('state', '=', 'submitted')])
        fac_cours     = fac_model.search_count(user_fac_domain + [('state', '=', 'in_progress')])
        fac_validated = fac_model.search_count(user_fac_domain + [('state', '=', 'validated')])
        fac_closed    = fac_model.search_count(user_fac_domain + [('state', '=', 'closed')])

        # ── Plans SMI (tous temps) ──
        plan_domain = [('create_uid', '=', uid), ('is_global', '=', False)]
        plan_total     = plan_model.search_count(plan_domain)
        plan_brouillon = plan_model.search_count(plan_domain + [('submission_state', '=', 'brouillon')])
        plan_soumis    = plan_model.search_count(plan_domain + [('submission_state', '=', 'soumis')])
        plan_integre   = plan_model.search_count(plan_domain + [('submission_state', '=', 'integre')])
        plan_cloture   = plan_model.search_count(plan_domain + [('submission_state', '=', 'cloture')])

        # ── Évolution mensuelle (min 6 mois pour lisibilité du graphique) ──
        nb_chart_months = max(period_months, 6)
        monthly_labels = []
        monthly_fnc = []
        monthly_fac = []
        for i in range(nb_chart_months - 1, -1, -1):
            d = today - relativedelta(months=i)
            m_start = d.replace(day=1)
            m_end = (d + relativedelta(months=1)).replace(day=1)
            m_fnc_ids = fnc_model.search([
                ('create_uid', '=', uid),
                ('date', '>=', str(m_start)),
                ('date', '<', str(m_end)),
            ]).ids
            monthly_fnc.append(len(m_fnc_ids))
            monthly_fac.append(fac_model.search_count([
                ('fnc_id', 'in', m_fnc_ids),
            ]))
            monthly_labels.append(fr_months[m_start.month - 1])

        # ── Calendrier (tous temps) ──
        calendar_events = {}
        for fnc_rec in fnc_model.sudo().search([
            '|',
            ('assigned_to_id.user_id', '=', uid),
            ('current_handler_uid', '=', uid),
            ('date_envoi', '!=', False),
        ]):
            k = str(fnc_rec.date_envoi)[:10]
            if k not in calendar_events:
                calendar_events[k] = {'fnc': False, 'fac': False}
            calendar_events[k]['fnc'] = True
        for fac_rec in fac_model.search([
            ('current_handler_uid', '=', uid),
            ('date_envoi', '!=', False),
        ]):
            k = str(fac_rec.date_envoi)[:10]
            if k not in calendar_events:
                calendar_events[k] = {'fnc': False, 'fac': False}
            calendar_events[k]['fac'] = True

        limit7 = str(today - timedelta(days=7))

        def _u_fnc_item(rec):
            delta = (today - fields.Date.from_string(str(rec.date_in_progress))).days \
                if rec.date_in_progress else 0
            return {'id': rec.id, 'name': rec.name or '',
                    'department': rec.direction_id.name if rec.direction_id else '',
                    'days': delta}

        def _u_fac_item(fac_rec, date_ref):
            delta = (today - fields.Date.from_string(str(date_ref))).days if date_ref else 0
            return {'id': fac_rec.id, 'name': fac_rec.name or '',
                    'department': fac_rec.direction_id.name if fac_rec.direction_id else '',
                    'days': delta,
                    'fnc_name': fac_rec.fnc_id.name if fac_rec.fnc_id else ''}

        # 1. Ses FNC à valider : en cours > 1 jour
        user_fnc_retard_list = [
            _u_fnc_item(r)
            for r in fnc_model.search(user_fnc_domain_all + [
                ('state', '=', 'in_progress'),
                ('date_in_progress', '!=', False),
                ('date_in_progress', '<=', limit7),
            ], order='date_in_progress asc', limit=10)
        ]

        # 2. Ses FAC à valider : en cours > 1 jour (ses FAC via user_fac_domain_all)
        user_fac_en_cours_list = [
            _u_fac_item(r, r.date)
            for r in fac_model.search(user_fac_domain_all + [
                ('state', '=', 'in_progress'),
                ('date', '!=', False),
                ('date', '<=', limit7),
            ], order='date asc', limit=10)
        ]

        # 3. Ses FAC envoyées validées : sudo pour contourner la perte d'accès après changement de responsable_id
        user_fac_validees_list = [
            _u_fac_item(r, r.date_validated)
            for r in fac_model.sudo().search(['|', '|', '|',
                ('fnc_id', 'in', user_fnc_ids_all),
                ('responsable_id', '=', uid),
                ('create_uid', '=', uid),
                ('sent_by_id', '=', uid),
                ('state', '=', 'validated'),
                ('date_envoi', '!=', False),
            ], order='date_validated asc', limit=10)
        ]

        def _initials(name):
            if not name:
                return '??'
            return ''.join([w[0].upper() for w in name.split()[:2]]) or '??'

        # ── Docs reçus par date (calendrier) ──
        received_by_date = {}

        def _append_doc(day_key, item):
            if day_key not in received_by_date:
                received_by_date[day_key] = []
            received_by_date[day_key].append(item)

        user_partner_id = self.env.user.partner_id.id
        for fnc_rec in fnc_model.sudo().search([
            '|', '|',
            ('assigned_to_id.user_id', '=', uid),
            ('current_handler_uid', '=', uid),
            ('message_partner_ids', 'in', [user_partner_id]),
            ('date_envoi', '!=', False),
            ('create_uid', '!=', uid),
        ], order='date_envoi desc, id desc'):
            k = str(fnc_rec.date_envoi)[:10]
            sender_name = (fnc_rec.sent_by_id.name if fnc_rec.sent_by_id
                           else (fnc_rec.signale_par_id.name if fnc_rec.signale_par_id
                           else (fnc_rec.direction_id.name if fnc_rec.direction_id else '')))
            _append_doc(k, {
                'id': fnc_rec.id,
                'name': fnc_rec.name or '',
                'kind': 'FNC',
                'model': 'nc_management.nonconformity',
                'state': fnc_rec.state,
                'sender_name': sender_name,
                'sender_initials': _initials(sender_name),
                'fnc_id': None,
            })

        for fac_rec in fac_model.search([
            ('current_handler_uid', '=', uid),
            ('date_envoi', '!=', False),
        ], order='date_envoi desc, id desc'):
            k = str(fac_rec.date_envoi)[:10]
            sender_name = fac_rec.sent_by_id.name if fac_rec.sent_by_id else ''
            _append_doc(k, {
                'id': fac_rec.id,
                'name': fac_rec.name or '',
                'kind': 'FAC',
                'model': 'nc_management.corrective_action',
                'state': fac_rec.state,
                'sender_name': sender_name,
                'sender_initials': _initials(sender_name),
                'fnc_id': fac_rec.fnc_id.id if fac_rec.fnc_id else None,
            })

        return {
            'today':         today.strftime('%d/%m/%Y'),
            'uid':           uid,
            'period':        period or '1m',
            'fnc_total':     fnc_total,
            'fnc_brouillon': fnc_brouillon,
            'fnc_submitted': fnc_submitted,
            'fnc_cours':     fnc_cours,
            'fnc_validated': fnc_validated,
            'fnc_closed':    fnc_closed,
            'fnc_taux_validation': fnc_taux_validation,
            'fac_total':     fac_total,
            'fac_brouillon': fac_brouillon,
            'fac_submitted': fac_submitted,
            'fac_cours':     fac_cours,
            'fac_validated': fac_validated,
            'fac_closed':    fac_closed,
            'plan_total':    plan_total,
            'plan_brouillon': plan_brouillon,
            'plan_soumis':   plan_soumis,
            'plan_integre':  plan_integre,
            'plan_cloture':  plan_cloture,
            'monthly_labels':  monthly_labels,
            'monthly_fnc':     monthly_fnc,
            'monthly_fac':     monthly_fac,
            'calendar_events': calendar_events,
            'calendar_year':   today.year,
            'calendar_month':  today.month,
            'user_fnc_retard_list':   user_fnc_retard_list,
            'user_fac_en_cours_list': user_fac_en_cours_list,
            'user_fac_validees_list': user_fac_validees_list,
            'received_by_date': received_by_date,
        }

    @api.model
    def get_direction_details(self, direction_id, period=None):
        from dateutil.relativedelta import relativedelta

        fnc = self.env['nc_management.nonconformity']
        fac = self.env['nc_management.corrective_action']
        today = date.today()
        period_months = {'1m': 1, '6m': 6, '1y': 12}.get(period or '1m', 1)
        period_end = today.replace(day=1) + relativedelta(months=1)
        period_start = today.replace(day=1) - relativedelta(months=period_months - 1)

        # Même filtre que les barres : FNC reçues = pas créées par la RMQSE, filtrées par date_envoi
        received_fnc_domain = [
            ('date_envoi', '>=', str(period_start)),
            ('date_envoi', '<', str(period_end)),
            ('state', '!=', 'draft'),
            ('create_uid', '!=', self.env.uid),
        ]

        def _pct(recs):
            counts = {k: 0 for k in [
                'nc_produit', 'reclamation', 'sst', 'environnement',
                'audit_interne', 'audit_externe', 'achat', 'reception',
                'dysfonctionnement', 'travaux', 'autres',
            ]}
            for r in recs:
                if r.type_nc_produit: counts['nc_produit'] += 1
                if r.type_reclamation: counts['reclamation'] += 1
                if r.type_sst: counts['sst'] += 1
                if r.type_environnement: counts['environnement'] += 1
                if r.type_audit_interne: counts['audit_interne'] += 1
                if r.type_audit_externe: counts['audit_externe'] += 1
                if r.type_achat: counts['achat'] += 1
                if r.type_reception: counts['reception'] += 1
                if r.type_dysfonctionnement: counts['dysfonctionnement'] += 1
                if r.type_travaux: counts['travaux'] += 1
                if r.type_autre: counts['autres'] += 1
            total = sum(counts.values()) or 1
            return {k: int(round(v / total * 100)) for k, v in counts.items()}

        dir_fnc_recs = fnc.search(received_fnc_domain + [('direction_id', '=', direction_id)])
        dir_fnc_ids = dir_fnc_recs.ids
        dir_fac_recs = fac.search([('fnc_id', 'in', dir_fnc_ids)])

        departments = self.env['hr.department'].search([
            ('scaek_level', '=', 'departement'),
            ('parent_id', '=', direction_id),
        ], order='name asc')

        dept_data = []
        for dept in departments:
            d_fnc = fnc.search(received_fnc_domain + [
                ('direction_id', '=', direction_id),
                ('department_id', '=', dept.id),
            ])
            d_fnc_ids = d_fnc.ids
            d_fac = fac.search([('fnc_id', 'in', d_fnc_ids)])

            services = self.env['hr.department'].search([
                ('scaek_level', '=', 'service'),
                ('parent_id', '=', dept.id),
            ], order='name asc')

            svc_data = []
            for svc in services:
                s_fnc = fnc.search(received_fnc_domain + [
                    ('direction_id', '=', direction_id),
                    ('service_id', '=', svc.id),
                ])
                s_fnc_ids = s_fnc.ids
                s_fac = fac.search([('fnc_id', 'in', s_fnc_ids)])
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

    @api.model
    def get_sender_info(self, model, record_id):
        import re
        from odoo.tools import html2plaintext
        from datetime import timedelta

        result = {'nom': '', 'prenom': '', 'direction': '', 'service': '', 'department': '', 'send_datetime': '', 'message': ''}

        def _split_name(full):
            parts = (full or '').strip().split(' ', 1)
            return parts[0], (parts[1] if len(parts) > 1 else '')

        def _fmt_dt(dt):
            if not dt:
                return ''
            try:
                return (dt + timedelta(hours=1)).strftime('%d/%m/%Y à %H:%M')
            except Exception:
                return str(dt)[:16]

        def _wizard_note(mod, rid):
            msgs = self.env['mail.message'].sudo().search([
                ('res_id', '=', rid),
                ('model', '=', mod),
                ('body', 'ilike', 'Message :'),
            ], order='id asc', limit=1)
            if not msgs:
                return ''
            plain = html2plaintext(msgs.body or '')
            m = re.search(r'[Mm]essage\s*:\s*(.+)', plain, re.DOTALL)
            return m.group(1).strip() if m else ''

        def _first_msg_dt(mod, rid):
            msg = self.env['mail.message'].sudo().search([
                ('res_id', '=', rid),
                ('model', '=', mod),
                ('message_type', 'in', ['comment', 'notification']),
                ('body', 'not in', [False, '', '<p><br></p>']),
            ], order='id asc', limit=1)
            return _fmt_dt(msg.date) if msg else ''

        try:
            if model == 'nc_management.nonconformity':
                rec = self.env[model].sudo().browse(record_id)
                if not rec.exists():
                    return result
                if rec.sent_by_id:
                    full = rec.sent_by_id.name or ''
                elif rec.signale_par_id:
                    full = rec.signale_par_id.name or ''
                elif rec.submitted_by_id:
                    full = rec.submitted_by_id.name or ''
                elif rec.create_uid and rec.create_uid.id != self.env.uid:
                    full = rec.create_uid.name or ''
                else:
                    full = ''
                result['nom'], result['prenom'] = _split_name(full)
                result['direction']  = rec.direction_id.name  if rec.direction_id  else ''
                result['service']    = rec.service_id.name    if rec.service_id    else ''
                result['department'] = rec.department_id.name if rec.department_id else ''
                result['send_datetime'] = _first_msg_dt(model, record_id)
                result['message'] = _wizard_note(model, record_id)

            elif model == 'nc_management.corrective_action':
                rec = self.env[model].sudo().browse(record_id)
                if not rec.exists():
                    return result
                fnc = rec.fnc_id
                if rec.sent_by_id:
                    full = rec.sent_by_id.name or ''
                elif fnc and fnc.signale_par_id:
                    full = fnc.signale_par_id.name or ''
                elif fnc and fnc.submitted_by_id:
                    full = fnc.submitted_by_id.name or ''
                elif rec.responsable_actions_id:
                    full = rec.responsable_actions_id.name or ''
                else:
                    full = ''
                result['nom'], result['prenom'] = _split_name(full)
                result['direction']  = rec.direction_id.name if rec.direction_id else ''
                result['service']    = (fnc.service_id.name    if fnc and fnc.service_id    else '')
                result['department'] = (fnc.department_id.name if fnc and fnc.department_id else '')
                src_mod = 'nc_management.nonconformity' if fnc else model
                src_id  = fnc.id if fnc else record_id
                result['send_datetime'] = _first_msg_dt(src_mod, src_id)
                result['message'] = _wizard_note(src_mod, src_id)

            elif model == 'nc_management.plan_action_smi':
                rec = self.env[model].sudo().browse(record_id)
                if not rec.exists():
                    return result
                full = rec.sent_by.name if rec.sent_by else (rec.responsable_id.name if rec.responsable_id else '')
                result['nom'], result['prenom'] = _split_name(full)
                result['direction']  = rec.direction_id.name  if rec.direction_id  else ''
                result['service']    = rec.service_id.name    if rec.service_id    else ''
                result['department'] = rec.department_id.name if rec.department_id else ''
                result['send_datetime'] = _fmt_dt(rec.date_envoi) if rec.date_envoi else ''
                result['message'] = rec.description or _wizard_note(model, record_id)

            elif model == 'nc_management.smi_improvement_plan':
                rec = self.env[model].sudo().browse(record_id)
                if not rec.exists():
                    return result
                full = rec.submitted_by_id.name if rec.submitted_by_id else (rec.direction_id.name if rec.direction_id else '')
                result['nom'], result['prenom'] = _split_name(full)
                result['direction']  = rec.direction_id.name  if rec.direction_id  else ''
                result['service']    = rec.service_id.name    if rec.service_id    else ''
                result['department'] = rec.department_id.name if rec.department_id else ''
                result['send_datetime'] = _fmt_dt(rec.date_soumission) if rec.date_soumission else ''
                result['message'] = rec.description or ''

        except Exception:
            pass

        return result


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def write(self, vals):
        result = super(ResUsers, self).write(vals)
        if 'lang' in vals and vals['lang']:
            for user in self:
                if user.partner_id:
                    user.partner_id.sudo().write({'lang': vals['lang']})
        return result
