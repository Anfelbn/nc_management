{
    'name': 'NC Management',
    'summary': 'NC Management module',
    'version': '11.0.0.1',
    'category': 'Tools',
    'author': 'Your Name',

    'depends': ['base'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
