{
    'name': 'NC Management',
    'summary': 'NC Management module',
    'version': '11.0.0.1',
    'category': 'Tools',
    'author': 'Your Name',

    'depends': ['base', 'hr', 'mail', 'web'],

    'data': [
        'security/quality_groups.xml',
        'security/ir.model.access.csv',
        'security/nc_rules.xml',
        'data/sequences.xml',
        'views/views.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
