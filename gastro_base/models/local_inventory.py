from odoo import models, fields, api

class GastroLocalInventory(models.Model):
    _name = 'gastro.local.inventory'
    _description = 'Mutfak Yerel Deposu'

    supplier_product_id = fields.Many2one('gastro.supplier.offer', string='Tedarikçi İlanı', required=True)
    name = fields.Char(string='Stok Adı', compute='_compute_name', store=True) 
    
    partner_id = fields.Many2one(related='supplier_product_id.partner_id', string='Tedarikçi', store=True)
    purchase_price = fields.Float(related='supplier_product_id.price', string='Birim Maliyeti', readonly=True)
    expiration_date = fields.Date(related='supplier_product_id.expiration_date', string='SKT', store=True)
    
    # 1. YENİ EKLENEN: Tedarikçi ilanındaki indirim oranını otomatik çeker
    discount_rate = fields.Float(related='supplier_product_id.discount_rate', string='İndirim (%)', readonly=True)
    
    qty_in_stock = fields.Float(string='Depomuzdaki Miktar', default=0.0)

    # 2. YENİ EKLENEN: Kendi depomuzun stok durumu (Rozet için)
    stock_status = fields.Selection([
        ('var', 'Yeterli Stok'),
        ('kritik', 'Kritik Seviye'),
        ('yok', 'Tükendi')
    ], string="Stok Durumu", compute='_compute_stock_status', store=True)

    @api.depends('supplier_product_id') 
    def _compute_name(self):
        for record in self:
            if record.supplier_product_id:
                record.name = f"{record.supplier_product_id.ingredient_id.name} ({record.partner_id.name})"
            else:
                record.name = "Yeni Stok"

    # Depodaki miktara göre otomatik rozet hesaplama
    @api.depends('qty_in_stock')
    def _compute_stock_status(self):
        for rec in self:
            if rec.qty_in_stock > 10:  # Stok 10'dan fazlaysa YEŞİL
                rec.stock_status = 'var'
            elif rec.qty_in_stock > 0: # Stok 1 ile 10 arasındaysa SARI (Uyarı)
                rec.stock_status = 'kritik'
            else:                      # Stok 0 veya altındaysa KIRMIZI
                rec.stock_status = 'yok'