# -*- coding: utf-8 -*-
from odoo import models, fields, api
import xlwt
import base64
from io import BytesIO

class ExportSmiAnalysisWizard(models.TransientModel):
    _name = 'nc_management.export_smi_analysis_wizard'
    _description = 'Export SMI Analysis as Excel'

    excel_file = fields.Binary('Fichier Excel', readonly=True)
    file_name = fields.Char('Nom du fichier', readonly=True)

    @api.multi
    def action_export(self):
        # Get stats from dashboard model
        stats = self.env['nc_management.dashboard'].get_plan_smi_stats()

        # Create workbook
        workbook = xlwt.Workbook(encoding='utf-8')
        
        # --- Sheet 1: Efficacité Globale ---
        sheet1 = workbook.add_sheet('Efficacité Globale')
        
        # Styles
        title_style = xlwt.easyxf('font: bold on, height 240; align: horiz center; pattern: pattern solid, fore_colour gray25;')
        header_style = xlwt.easyxf('font: bold on; align: horiz center; pattern: pattern solid, fore_colour gray25; border: top thin, bottom thin, left thin, right thin;')
        data_style = xlwt.easyxf('border: top thin, bottom thin, left thin, right thin;')
        percent_style = xlwt.easyxf('border: top thin, bottom thin, left thin, right thin;', num_format_str='0.0%')

        # Title
        sheet1.write_merge(0, 0, 0, 7, 'ANALYSE EFFICACITÉ GLOBALE', title_style)

        # Headers
        headers = [
            'Catégorie', 'Efficace', 'Non efficace', 'Réalisé 100%', 
            'Réalisé plus 50%', 'Réalisée moins 50%', 'Taux Efficacité', 'Total'
        ]
        for col, header in enumerate(headers):
            sheet1.write(2, col, header, header_style)

        # Data
        for row, cat in enumerate(stats['categories'], start=3):
            d = cat['data']
            sheet1.write(row, 0, cat['label'], data_style)
            sheet1.write(row, 1, d['efficace'], data_style)
            sheet1.write(row, 2, d['non_efficace'], data_style)
            sheet1.write(row, 3, d['realise_100'], data_style)
            sheet1.write(row, 4, d['realise_50plus'], data_style)
            sheet1.write(row, 5, d['realise_50moins'], data_style)
            sheet1.write(row, 6, d['taux'] / 100.0, percent_style)
            sheet1.write(row, 7, d['total'], data_style)

        # --- Sheet 2: Réalisation Processus ---
        sheet2 = workbook.add_sheet('Réalisation Processus')
        sheet2.write_merge(0, 0, 0, 1, 'TAUX DE RÉALISATION (REVUE PROCESSUS)', title_style)
        
        headers2 = ['Processus', 'Taux de réalisation']
        for col, header in enumerate(headers2):
            sheet2.write(2, col, header, header_style)

        for row, proc in enumerate(stats['processus'], start=3):
            sheet2.write(row, 0, proc['label'], data_style)
            sheet2.write(row, 1, proc['taux'] / 100.0, percent_style)

        # Save to binary field
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        file_data = fp.read()
        fp.close()

        self.write({
            'excel_file': base64.b64encode(file_data),
            'file_name': 'Analyse_Efficacite_SMI.xls'
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nc_management.export_smi_analysis_wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
