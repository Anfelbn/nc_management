from odoo import models, fields, api

CATEGORIES = [
    ('reclamation_pi', 'Réclamation PI'),
    ('nc_produit',     'NC Produit'),
    ('environnement',  'Environnement'),
    ('sst',            'SST'),
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
    chart_html = fields.Html(string='Graphique', compute='_compute_chart_html')

    @api.depends('line_ids.taux', 'line_ids.categorie')
    def _compute_chart_html(self):
        for rec in self:
            lines = rec.line_ids
            if not lines:
                rec.chart_html = '<p style="color:#888;">Aucune donnée disponible.</p>'
                continue

            bar_w   = 70
            gap     = 25
            h_chart = 180
            w_chart = gap + len(lines) * (bar_w + gap) + 30

            def color(t):
                if t >= 75:   return '#5cb85c'
                if t >= 50:   return '#f0ad4e'
                return '#d9534f'

            bars = labels = pcts = ''
            for i, ln in enumerate(lines):
                x      = gap + i * (bar_w + gap)
                height = int(ln.taux * h_chart / 100)
                y      = h_chart - height
                c      = color(ln.taux)
                bars  += ('<rect x="%d" y="%d" width="%d" height="%d" '
                          'fill="%s" rx="4"/>' % (x, y, bar_w, height, c))
                labels += ('<text x="%d" y="%d" text-anchor="middle" '
                           'font-size="11" fill="#555">%s</text>'
                           % (x + bar_w // 2, h_chart + 16, ln.categorie))
                pcts  += ('<text x="%d" y="%d" text-anchor="middle" '
                          'font-size="12" font-weight="bold" fill="%s">%d%%</text>'
                          % (x + bar_w // 2, max(y - 6, 14), c, int(ln.taux)))

            svg = (
                '<div style="margin-top:20px;">'
                '<p style="font-weight:bold;font-size:14px;margin-bottom:8px;">'
                'Taux d\'efficacité par catégorie (%)</p>'
                '<svg width="{w}" height="{h}" style="overflow:visible;display:block;">'
                '<line x1="24" y1="0" x2="24" y2="{hc}" stroke="#ddd" stroke-width="1"/>'
                '<line x1="24" y1="{hc}" x2="{w}" y2="{hc}" stroke="#ddd" stroke-width="1"/>'
                '<text x="20" y="10" text-anchor="end" font-size="9" fill="#aaa">100%</text>'
                '<text x="20" y="{h50}" text-anchor="end" font-size="9" fill="#aaa">50%</text>'
                '<text x="20" y="{hc}" text-anchor="end" font-size="9" fill="#aaa">0%</text>'
                '{bars}{pcts}{labels}'
                '</svg>'
                '</div>'
            ).format(
                w=w_chart, h=h_chart + 30, hc=h_chart,
                h50=h_chart // 2 + 4,
                bars=bars, pcts=pcts, labels=labels,
            )
            rec.chart_html = svg

    @api.model
    def default_get(self, fields_list):
        res = super(PlanEfficaciteWizard, self).default_get(fields_list)
        plan_id = self.env.context.get('default_plan_id')
        if not plan_id:
            return res

        child_plans = self.env['nc_management.plan_action_smi'].browse(
            plan_id).child_plan_ids

        lines = []
        for code, label in CATEGORIES:
            cat = child_plans.filtered(lambda p: p.nature == code)
            total = len(cat)
            if total:
                eff     = sum(1 for p in cat if p.efficacite == 'oui')
                non_eff = sum(1 for p in cat if p.efficacite == 'non')
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
