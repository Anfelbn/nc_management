from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Revision = env['nc_management.document_revision']
    for doc_type in ('fnc', 'fac'):
        already_valable = Revision.search([('doc_type', '=', doc_type), ('etat', '=', 'valable')])
        if not already_valable:
            latest = Revision.search([('doc_type', '=', doc_type)], limit=1)
            if latest:
                latest.write({'etat': 'valable'})
