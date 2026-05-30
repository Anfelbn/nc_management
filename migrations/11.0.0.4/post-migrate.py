from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # Force le nom du menu et supprime toutes les traductions résiduelles
    cr.execute("""
        UPDATE ir_ui_menu
        SET name = 'Révision Documents'
        WHERE id = (
            SELECT res_id FROM ir_model_data
            WHERE module = 'nc_management' AND name = 'menu_config'
        )
    """)

    cr.execute("""
        DELETE FROM ir_translation
        WHERE type = 'model'
          AND name = 'ir.ui.menu,name'
          AND res_id = (
              SELECT res_id FROM ir_model_data
              WHERE module = 'nc_management' AND name = 'menu_config'
          )
    """)
