# -*- coding: utf-8 -*-
from odoo import models, fields, api
import xlwt
import base64
from io import BytesIO

class ExportPlanWizard(models.TransientModel):
    _name = 'nc_management.export_plan_wizard'
    _description = 'Export Plan Action SMI as Excel'

    excel_file = fields.Binary('Fichier Excel', readonly=True)
    file_name = fields.Char('Nom du fichier', readonly=True)

    @api.multi
    def action_export(self):
        # Create workbook
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('Plan Action SMI')

        # Define styles
        header_style = xlwt.easyxf('font: bold on; align: horiz center; pattern: pattern solid, fore_colour gray25; border: top thin, bottom thin, left thin, right thin;')
        data_style = xlwt.easyxf('border: top thin, bottom thin, left thin, right thin;')

        # Headers
        headers = [
            'Référence', 'Nature', 'FNC Liée', 'Description', 'Causes', 'Action',
            'Responsable', 'Moyens', 'Durée Est.', 'Date Prévue', 'Date Lanc.',
            'Date Réal.', 'Avancement %', 'Durée Réelle', 'Efficacité', 'État'
        ]
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_style)

        # Data
        plans = self.env['nc_management.plan_action_smi'].search([])
        for row, plan in enumerate(plans, start=1):
            sheet.write(row, 0, plan.name or '', data_style)
            sheet.write(row, 1, dict(plan._fields['nature'].selection).get(plan.nature, ''), data_style)
            sheet.write(row, 2, plan.fnc_id.name or '', data_style)
            sheet.write(row, 3, plan.description or '', data_style)
            sheet.write(row, 4, plan.causes or '', data_style)
            sheet.write(row, 5, plan.action or '', data_style)
            sheet.write(row, 6, plan.responsable_id.name or '', data_style)
            sheet.write(row, 7, plan.moyens or '', data_style)
            sheet.write(row, 8, plan.duree_estimee or '', data_style)
            sheet.write(row, 9, str(plan.date_prevue) if plan.date_prevue else '', data_style)
            sheet.write(row, 10, str(plan.date_lancement) if plan.date_lancement else '', data_style)
            sheet.write(row, 11, str(plan.date_realisation) if plan.date_realisation else '', data_style)
            sheet.write(row, 12, plan.avancement or 0, data_style)
            sheet.write(row, 13, plan.duree_reelle or '', data_style)
            sheet.write(row, 14, dict(plan._fields['efficacite'].selection).get(plan.efficacite, ''), data_style)
            sheet.write(row, 15, dict(plan._fields['state'].selection).get(plan.state, ''), data_style)

        # Save to binary field
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        file_data = fp.read()
        fp.close()

        self.write({
            'excel_file': base64.b64encode(file_data),
            'file_name': 'Plan_Action_SMI.xls'
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.export_plan_wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
