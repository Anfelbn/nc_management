from odoo import models, fields, api

FIELD_RENDER_TYPES = {
    'name': 'char', 'direction_id': 'many2one', 'department_id': 'many2one',
    'service_id': 'many2one', 'section_id': 'many2one', 'equipe_id': 'many2one',
    'date': 'date', 'service_dpt': 'char', 'sce_dpt_computed': 'char',
    'type_nc_produit': 'boolean', 'type_reclamation': 'boolean', 'type_sst': 'boolean',
    'type_environnement': 'boolean', 'type_travaux': 'boolean', 'type_audit': 'boolean',
    'type_audit_interne': 'boolean', 'type_audit_externe': 'boolean',
    'type_achat': 'boolean', 'type_reception': 'boolean',
    'type_dysfonctionnement': 'boolean', 'type_autre': 'boolean',
    'type_autre_preciser': 'char', 'description': 'text',
    'signale_par_id': 'many2one', 'date_signalement': 'date', 'fonction_visa': 'char',
    'trait_reprise': 'boolean', 'trait_declassement': 'boolean',
    'trait_retour_fourn': 'boolean', 'trait_recyclage': 'boolean',
    'trait_reparation': 'boolean', 'trait_autre': 'boolean',
    'trait_autre_preciser': 'char', 'action_immediate': 'text',
    'realise_par_id': 'many2one', 'date_realisation': 'date',
    'analyse_causes': 'text', 'impact': 'text',
    'fac_number_display': 'char', 'responsable_action_id': 'many2one',
    'superieur_id': 'many2one', 'date_validation': 'date', 'signature': 'char',
    # FAC
    'responsable_id': 'many2one', 'fnc_id': 'many2one', 'date_fnc': 'date',
    'rappel_nc': 'text', 'responsable_analyse_id': 'many2one',
    'date_analyse': 'date', 'visa_analyse': 'char',
    'responsable_actions_id': 'many2one', 'date_actions': 'date', 'visa_actions': 'char',
    'actions_efficaces': 'selection_yes_no', 'responsable_efficacite_id': 'many2one',
    'qse_nom_id': 'many2one', 'qse_date': 'date', 'qse_visa': 'char',
    'verification_efficacite': 'text', 'extension_possible': 'selection_non_oui',
    'cloture_par_id': 'many2one', 'date_cloture': 'date', 'visa_cloture': 'char',
}

ALL_FIELD_SELECTION = [
    ('', '— (aucun) —'),
    ('name', 'N° FNC / N° FAC'), ('date', 'Date'),
    ('direction_id', 'Direction / Emetteur'), ('department_id', 'Département'),
    ('service_id', 'Service'), ('section_id', 'Section'), ('equipe_id', 'Équipe'),
    ('sce_dpt_computed', 'Sce / DPT (calculé auto)'),
    ('service_dpt', 'Sce / DPT (champ libre)'),
    ('type_nc_produit', '☐ NC Produit'), ('type_reclamation', '☐ Réclamation clients/PI'),
    ('type_sst', '☐ SST Accident'), ('type_environnement', '☐ Environnement'),
    ('type_travaux', '☐ Travaux'), ('type_audit', '☐ Audit interne/Externe'),
    ('type_audit_interne', '☐ Audit interne'), ('type_audit_externe', '☐ Audit externe'),
    ('type_achat', '☐ Achat'), ('type_reception', '☐ Réception'),
    ('type_dysfonctionnement', '☐ Dysfonctionnement'), ('type_autre', '☐ Autre'),
    ('type_autre_preciser', 'Préciser (type Autre)'),
    ('description', 'Description de la NC'), ('signale_par_id', 'Nom qui signale'),
    ('date_signalement', 'Date de signalement'), ('fonction_visa', 'Fonction et visa'),
    ('trait_reprise', '☐ Reprise pour mise en conformité'),
    ('trait_declassement', '☐ Déclassement pour autre utilisation'),
    ('trait_retour_fourn', '☐ Retour au fournisseur'),
    ('trait_recyclage', '☐ Recyclage'), ('trait_reparation', '☐ Réparation'),
    ('trait_autre', '☐ Autre (traitement)'), ('trait_autre_preciser', 'Préciser traitement'),
    ('action_immediate', 'Action immédiate'), ('realise_par_id', 'Réalisé par'),
    ('date_realisation', 'Date de réalisation'), ('analyse_causes', 'Analyse des causes'),
    ('impact', 'Impact : coût, incidence, risque'),
    ('fac_number_display', "N° Fiche d'action"),
    ('responsable_action_id', "Responsable de l'action(s)"),
    ('superieur_id', 'Supérieur hiérarchique'),
    ('date_validation', 'Date de validation'), ('signature', 'Signature'),
    # FAC
    ('responsable_id', 'Responsable (FAC)'), ('fnc_id', 'N° FNC ou autre document'),
    ('date_fnc', 'Date FNC'), ('rappel_nc', 'Rappel de la NC'),
    ('responsable_analyse_id', 'Responsable analyse'),
    ('date_analyse', 'Date analyse'), ('visa_analyse', 'Visa analyse'),
    ('responsable_actions_id', 'Responsable actions'),
    ('date_actions', 'Date actions'), ('visa_actions', 'Visa actions'),
    ('actions_efficaces', 'Actions efficaces (Oui/Non)'),
    ('responsable_efficacite_id', 'Responsable efficacité'),
    ('qse_nom_id', 'Nom Responsable QSE'), ('qse_date', 'Date approbation QSE'),
    ('qse_visa', 'Visa QSE'),
    ('verification_efficacite', "Vérification de l'efficacité"),
    ('extension_possible', 'Extension possible (Non/Oui)'),
    ('cloture_par_id', 'Clôturée par'), ('date_cloture', 'Date clôture'),
    ('visa_cloture', 'Visa clôture'),
]


class FormTemplate(models.Model):
    _name = 'smi_management.form_template'
    _description = 'Gabarit de formulaire FNC/FAC'
    _order = 'doc_type asc, id desc'

    name = fields.Char(string='Nom', required=True)
    doc_type = fields.Selection([
        ('fnc', 'Fiche Non-Conformité (FNC)'),
        ('fac', "Fiche d'Action Corrective (FAC)"),
    ], string='Type de document', required=True)
    is_active = fields.Boolean(string='Gabarit actif', default=False)
    revision_id = fields.Many2one(
        'smi_management.document_revision', string='Révision liée', ondelete='set null')
    section_ids = fields.One2many(
        'smi_management.form_section', 'template_id', string='Sections')
    section_count = fields.Integer(compute='_compute_counts', store=False)

    @api.depends('section_ids')
    def _compute_counts(self):
        for rec in self:
            rec.section_count = len(rec.section_ids)

    @api.multi
    def action_activate(self):
        self.ensure_one()
        self.search([
            ('doc_type', '=', self.doc_type),
            ('id', '!=', self.id),
            ('is_active', '=', True),
        ]).write({'is_active': False})
        self.write({'is_active': True})
        return True

    @api.multi
    def action_new_revision(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nouvelle révision de document',
            'res_model': 'smi_management.new_revision_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_source_template_id': self.id},
        }

    @api.model
    def get_active_template(self, doc_type):
        return self.search(
            [('doc_type', '=', doc_type), ('is_active', '=', True)], limit=1)


class FormSection(models.Model):
    _name = 'smi_management.form_section'
    _description = 'Section du gabarit'
    _order = 'sequence asc, id asc'

    template_id = fields.Many2one(
        'smi_management.form_template', required=True, ondelete='cascade')
    name = fields.Char(string='Titre', required=True)
    sequence = fields.Integer(string='Ordre', default=10)
    is_active = fields.Boolean(string='Actif', default=True)
    show_title = fields.Boolean(string='Afficher titre', default=True)
    section_layout = fields.Selection([
        ('standard', 'Standard'),
        ('checkboxes_2col', 'Cases à cocher (2 colonnes)'),
        ('action_lines', 'Tableau actions (FAC)'),
    ], string='Disposition', default='standard', required=True)
    line_ids = fields.One2many(
        'smi_management.form_line', 'section_id', string='Lignes')
    line_count = fields.Integer(compute='_compute_line_count', store=False)

    @api.depends('line_ids', 'line_ids.is_active')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = sum(1 for l in rec.line_ids if l.is_active)


class FormLine(models.Model):
    _name = 'smi_management.form_line'
    _description = 'Ligne du gabarit'
    _order = 'sequence asc, id asc'

    section_id = fields.Many2one(
        'smi_management.form_section', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Ordre', default=10)
    is_active = fields.Boolean(string='Actif', default=True)
    line_type = fields.Selection([
        ('textarea',    'Zone de texte'),
        ('row',         'Rangée de champs (1-3 col.)'),
        ('checkbox',    'Case à cocher'),
        ('custom_text', 'Texte fixe'),
        ('separator',   'Séparateur'),
    ], string='Type', required=True, default='row')

    # ── textarea ────────────────────────────────────────────────
    ta_field = fields.Selection(ALL_FIELD_SELECTION, string='Champ')
    ta_label = fields.Char(string='Libellé au-dessus (optionnel)')
    ta_height = fields.Selection([
        ('sm', 'Petit (32px)'), ('md', 'Moyen (80px)'),
        ('lg', 'Grand (140px)'), ('xl', 'Très grand (180px)'),
    ], string='Hauteur', default='md')

    # ── row : jusqu'à 3 colonnes ────────────────────────────────
    col1_field = fields.Selection(ALL_FIELD_SELECTION, string='Champ col.1')
    col1_label = fields.Char(string='Libellé col.1')
    col2_field = fields.Selection(ALL_FIELD_SELECTION, string='Champ col.2')
    col2_label = fields.Char(string='Libellé col.2')
    col3_field = fields.Selection(ALL_FIELD_SELECTION, string='Champ col.3')
    col3_label = fields.Char(string='Libellé col.3')

    # ── checkbox ────────────────────────────────────────────────
    cb_field  = fields.Selection(ALL_FIELD_SELECTION, string='Champ')
    cb_label  = fields.Char(string='Libellé')
    cb_column = fields.Selection([
        ('left', 'Colonne gauche'), ('right', 'Colonne droite'),
    ], string='Colonne', default='left')
    cb_extra_field = fields.Selection(ALL_FIELD_SELECTION, string='Champ texte après case')
    cb_extra_label = fields.Char(string='Libellé champ extra')

    # ── texte fixe ──────────────────────────────────────────────
    custom_text = fields.Char(string='Texte')

    # ── render types stockés ────────────────────────────────────
    render_type_ta   = fields.Char(compute='_compute_render_types', store=True)
    render_type_col1 = fields.Char(compute='_compute_render_types', store=True)
    render_type_col2 = fields.Char(compute='_compute_render_types', store=True)
    render_type_col3 = fields.Char(compute='_compute_render_types', store=True)
    render_type_cb   = fields.Char(compute='_compute_render_types', store=True)
    nb_cols          = fields.Integer(compute='_compute_render_types', store=True)

    @api.depends('ta_field', 'col1_field', 'col2_field', 'col3_field', 'cb_field')
    def _compute_render_types(self):
        for rec in self:
            rec.render_type_ta   = FIELD_RENDER_TYPES.get(rec.ta_field   or '', 'char')
            rec.render_type_col1 = FIELD_RENDER_TYPES.get(rec.col1_field or '', 'char')
            rec.render_type_col2 = FIELD_RENDER_TYPES.get(rec.col2_field or '', 'char')
            rec.render_type_col3 = FIELD_RENDER_TYPES.get(rec.col3_field or '', 'char')
            rec.render_type_cb   = FIELD_RENDER_TYPES.get(rec.cb_field   or '', 'boolean')
            if rec.col3_field:
                rec.nb_cols = 3
            elif rec.col2_field:
                rec.nb_cols = 2
            elif rec.col1_field:
                rec.nb_cols = 1
            else:
                rec.nb_cols = 0
