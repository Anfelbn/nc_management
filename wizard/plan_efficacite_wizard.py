from odoo import models, fields, api

# Les 12 natures du plan d'action — correspondent au champ nature de plan_action_smi
CATEGORIES = [
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
]


class PlanEfficaciteLine(models.TransientModel):
    _name = 'nc_management.plan_efficacite_line'
    _description = "Ligne analyse efficacité"

    wizard_id       = fields.Many2one('nc_management.plan_efficacite_wizard', required=True)
    categorie       = fields.Char(string='Catégorie')
    total           = fields.Integer(string='Total')
    efficace        = fields.Integer(string='Efficace')
    non_efficace    = fields.Integer(string='Non Efficace')
    realise_100     = fields.Integer(string='Réalisé 100%')
    realise_50plus  = fields.Integer(string='Réalisé >50%')
    realise_50moins = fields.Integer(string='Réalisé <50%')
    taux            = fields.Float(string='Taux Efficacité %', digits=(5, 1))


class PlanEfficaciteWizard(models.TransientModel):
    _name = 'nc_management.plan_efficacite_wizard'
    _description = "Analyse Efficacité Plan d'Amélioration"

    plan_id    = fields.Many2one('nc_management.plan_action_smi',
                                 string="Plan d'Amélioration", readonly=True)
    line_ids   = fields.One2many('nc_management.plan_efficacite_line', 'wizard_id',
                                 string='Analyse par catégorie')
    chart_html = fields.Html(string='Graphique', compute='_compute_chart_html',
                             sanitize_attributes=False, sanitize_tags=False)

    @api.depends('line_ids.taux', 'line_ids.categorie')
    def _compute_chart_html(self):
        for rec in self:
            lines = rec.line_ids
            if not lines:
                rec.chart_html = '<p style="color:#555;">Aucune donnée disponible.</p>'
                continue

            bar_w       = 52
            gap         = 18
            h_chart     = 220
            margin_left = 44
            margin_bot  = 100
            w_chart     = margin_left + len(lines) * (bar_w + gap) + gap
            total_h     = h_chart + margin_bot

            def color(t):
                if t >= 75:  return '#1e5c38'   # vert foncé industriel
                if t >= 50:  return '#7a5200'   # ambre foncé
                return '#6e1f1f'                 # rouge sombre

            grid = ''
            for pct in [25, 50, 75, 100]:
                gy = h_chart - int(pct * h_chart / 100)
                grid += (
                    '<line x1="%d" y1="%d" x2="%d" y2="%d" '
                    'stroke="#9aabaa" stroke-width="1" stroke-dasharray="4,3"/>'
                    '<text x="%d" y="%d" text-anchor="end" '
                    'font-size="9" fill="#6a7878">%d%%</text>'
                    % (margin_left, gy, w_chart, gy,
                       margin_left - 4, gy + 3, pct)
                )

            bars = labels = pcts = ''
            for i, ln in enumerate(lines):
                x  = margin_left + gap + i * (bar_w + gap)
                cx = x + bar_w // 2
                h  = max(int(ln.taux * h_chart / 100), 2) if ln.taux > 0 else 0
                y  = h_chart - h
                c  = color(ln.taux)

                bars += (
                    '<rect x="%d" y="%d" width="%d" height="%d" '
                    'fill="%s" rx="3"/>'
                    % (x, y, bar_w, h, c)
                )
                if ln.taux > 0:
                    pcts += (
                        '<text x="%d" y="%d" text-anchor="middle" '
                        'font-size="10" font-weight="bold" fill="#e8ece8">%d%%</text>'
                        % (cx, max(y + 13, 12), int(ln.taux))
                    )
                labels += (
                    '<text transform="rotate(-42 %d %d)" '
                    'x="%d" y="%d" text-anchor="end" '
                    'font-size="10" fill="#3a4a48">%s</text>'
                    % (cx, h_chart + 10, cx, h_chart + 10, ln.categorie)
                )

            svg = (
                '<div style="margin-top:20px;overflow-x:auto;">'
                '<p style="font-weight:bold;font-size:14px;margin-bottom:10px;'
                'color:#1a2e2c;letter-spacing:.3px;">'
                'Taux d\'efficacité par catégorie (%)</p>'
                '<svg width="{w}" height="{h}" '
                'style="display:block;background:#eef0ec;'
                'border:1px solid #9aabaa;border-radius:4px;">'
                '{grid}'
                '<line x1="{ml}" y1="0" x2="{ml}" y2="{hc}" '
                'stroke="#5a7070" stroke-width="1.5"/>'
                '<line x1="{ml}" y1="{hc}" x2="{w}" y2="{hc}" '
                'stroke="#5a7070" stroke-width="1.5"/>'
                '{bars}{pcts}{labels}'
                '</svg>'
                '</div>'
            ).format(
                w=w_chart, h=total_h, hc=h_chart, ml=margin_left,
                grid=grid, bars=bars, pcts=pcts, labels=labels,
            )
            rec.chart_html = svg

    @api.model
    def default_get(self, fields_list):
        res = super(PlanEfficaciteWizard, self).default_get(fields_list)
        plan_id = self.env.context.get('default_plan_id')
        if not plan_id:
            return res

        # Plans intégrés dans ce plan d'action d'amélioration
        global_plan  = self.env['nc_management.plan_action_smi'].browse(plan_id)
        child_plans  = global_plan.child_plan_ids.filtered(
            lambda p: p.submission_state == 'integre'
        )

        lines = []
        for code, label in CATEGORIES:
            # Plans de cette nature intégrés dans le plan global
            cat   = child_plans.filtered(lambda p, c=code: p.nature == c)
            total = len(cat)

            if total:
                eff     = sum(1 for p in cat if p.efficacite == 'oui')
                non_eff = sum(1 for p in cat if p.efficacite == 'non')
                # Réalisation basée sur l'état d'avancement
                r100    = sum(1 for p in cat if p.avancement == 100)
                r50p    = sum(1 for p in cat if 50 < p.avancement < 100)
                r50m    = sum(1 for p in cat if p.avancement <= 50)
                taux    = round(eff / total * 100, 1)
            else:
                eff = non_eff = r100 = r50p = r50m = 0
                taux = 0.0

            lines.append((0, 0, {
                'categorie':       label,
                'total':           total,
                'efficace':        eff,
                'non_efficace':    non_eff,
                'realise_100':     r100,
                'realise_50plus':  r50p,
                'realise_50moins': r50m,
                'taux':            taux,
            }))

        res['plan_id']  = plan_id
        res['line_ids'] = lines
        return res
