{
    'name': 'Gastro Kitchen (Reçete Yönetimi)',
    'version': '1.0',
    'summary': 'Yemek reçeteleri, fason üretim teklifleri ve otomatik maliyet hesaplama',
    'category': 'Manufacturing',
    'depends': ['base', 'gastro_base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',  
        'views/recipe_views.xml', 
        'views/bidding_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}