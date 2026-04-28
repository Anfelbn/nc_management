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
        'data/sequences.xml',
        'reports/report_fnc.xml',
        'reports/report_fac.xml',
        'views/views.xml',
        'views/dashboard.xml',
    ],
    'qweb': [
        'static/src/xml/dashboard.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
