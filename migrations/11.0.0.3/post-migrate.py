from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # Trouve le menu "Configuration" sous le menu racine nc_management
    # et le renomme en "Révision Documents" (robuste même si ir_model_data
    # a un ancien module name comme smi_management)
    cr.execute("""
        UPDATE ir_ui_menu
        SET name = 'Révision Documents'
        WHERE name IN ('Configuration', 'Révision Documents')
          AND parent_id = (
              SELECT id FROM ir_ui_menu
              WHERE name IN ('NC Management', 'SMI Management')
                AND parent_id IS NULL
              LIMIT 1
          )
    """)

    # Supprime les traductions résiduelles sur ces menus
    cr.execute("""
        DELETE FROM ir_translation
        WHERE type = 'model'
          AND name = 'ir.ui.menu,name'
          AND res_id IN (
              SELECT id FROM ir_ui_menu
              WHERE name = 'Révision Documents'
                AND parent_id = (
                    SELECT id FROM ir_ui_menu
                    WHERE name IN ('NC Management', 'SMI Management')
                      AND parent_id IS NULL
                    LIMIT 1
                )
          )
    """)
