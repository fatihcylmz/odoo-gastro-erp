{
    'name': 'Gastro Base (Kiler Yönetimi)',
    'version': '1.0',
    'summary': 'Mutfak hammaddeleri ve temel maliyet tanımları',
    'category': 'Manufacturing',
    'depends': ['base','mail'],
    'data': [
        'security/ir.model.access.csv',  # <--- Kesinlikle EN ÜSTTE olmalı
        'wizard/procure_wizard_views.xml',
        'views/ingredient_views.xml',
        'views/local_inventory_views.xml', # Varsa diğer XML dosyaların...
        'data/ir_cron_data.xml',
        'security/gastro_security.xml',
        
    ],
    'installable': True,
    'application': True, # Bu bir ana uygulama olduğu için True
}