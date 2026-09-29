from odoo import models, fields, api

# ==========================================
# 1. EVRENSEL KATALOG MODELİ
# ==========================================
class GastroIngredient(models.Model):
    _name = 'gastro.ingredient'
    _description = 'Evrensel Mutfak Hammaddesi'

    name = fields.Char(string='Malzeme Adı (Örn: Süt)', required=True)
    category = fields.Selection([
        ('dairy', 'Süt ve Süt Ürünleri'),
        ('dry', 'Kuru Gıda / Bakliyat'),
        ('spice', 'Baharat / Tatlandırıcı'),
        ('fresh', 'Taze Meyve / Sebze')
    ], string='Kategori', default='dry')
    
    uom = fields.Selection([
        ('kg', 'Kilogram (Kg)'),
        ('lt', 'Litre (Lt)'),
        ('gr', 'Gram (Gr)'),
        ('unit', 'Adet')
    ], string='Ölçü Birimi', required=True, default='kg')

    offer_ids = fields.One2many('gastro.supplier.offer', 'ingredient_id', string='Tedarikçi Teklifleri')


# ==========================================
# 2. TEDARİKÇİ İLANLARI MODELİ
# ==========================================
class GastroSupplierOffer(models.Model):
    _name = 'gastro.supplier.offer'
    _description = 'Tedarikçi Ürün İlanları'
    _rec_name = 'partner_id'
    
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string='Tedarikçi Firma', required=True, default=lambda self: self.env.user.partner_id,readonly=True)
    ingredient_id = fields.Many2one('gastro.ingredient', string='Satılan Ürün', required=True)
    
    original_price = fields.Float(string='Normal Fiyat (TL)', required=True, default=0.0)
    price = fields.Float(string='Birim Fiyatı (TL)', compute='_compute_final_price', store=True, readonly=False)
    
    available_stock = fields.Float(string='Elimdeki Stok', default=0.0, tracking=True)

    stock_status = fields.Selection([
        ('var', 'Depoda Var'),
        ('yok', 'Tükendi')
    ], string="Stok Durumu", compute='_compute_stock_status', store=True)

    expiration_date = fields.Date(string='Son Kullanma Tarihi (SKT)')
    added_date = fields.Date(string='Eklenme Tarihi', default=fields.Date.context_today, readonly=True)
    discount_rate = fields.Float(string='İndirim Oranı (%)', default=0.0)
    discount_threshold_days = fields.Integer(string='İndirim Eşiği (Gün Kala)', default=30)
    remaining_days = fields.Integer(string="SKT'ye Kalan Gün", compute='_compute_remaining_days', store=True)

    @api.depends('available_stock')
    def _compute_stock_status(self):
        for rec in self:
            if rec.available_stock > 0:
                rec.stock_status = 'var'
            else:
                rec.stock_status = 'yok'

    def write(self, vals):
        res = super(GastroSupplierOffer, self).write(vals)
        if 'available_stock' in vals:
            for rec in self:
                if rec.available_stock <= 0:
                    rec.message_post(
                        body=f"⚠️ DİKKAT: {rec.ingredient_id.name} ürününün stoğu tükenmiştir! Lütfen tedarikçi ({rec.partner_id.name}) ile iletişime geçin.",
                        subject="Stok Tükendi Uyarısı",
                        message_type="notification",
                        subtype_xmlid="mail.mt_note"
                    )
        return res

    @api.depends('expiration_date')
    def _compute_remaining_days(self):
        today = fields.Date.today()
        for offer in self:
            if offer.expiration_date:
                delta = fields.Date.from_string(offer.expiration_date) - today
                offer.remaining_days = delta.days
            else:
                offer.remaining_days = 9999

    @api.depends('original_price', 'discount_rate', 'remaining_days', 'discount_threshold_days')
    def _compute_final_price(self):
        for offer in self:
            base = offer.original_price or 0.0
            if offer.discount_rate > 0 and offer.remaining_days <= offer.discount_threshold_days:
                offer.price = base * (1.0 - (offer.discount_rate / 100.0))
            else:
                offer.price = base

    def action_open_procure_wizard(self):
        self.ensure_one()
        return {
            'name': 'Satın Alınacak Miktarı Girin',
            'type': 'ir.actions.act_window',
            'res_model': 'gastro.procure.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.id, # İŞTE BURASI DÜZELDİ!
                'default_procure_qty': 1.0,
            }
        }

    @api.model
    def cron_update_expiry_and_discounts(self):
        offers = self.search([('available_stock', '>', 0)])
        for offer in offers:
            offer._compute_remaining_days()
            offer._compute_final_price()


# ==========================================
# 3. YENİ EKLENEN SATIN ALMA SİHİRBAZI (POP-UP)
# ==========================================
class GastroProcureWizard(models.TransientModel):
    _name = 'gastro.procure.wizard'
    _description = 'Satın Alma Sihirbazı'

    # Orijinal yapındaki isimle eşleşmesi için product_id kullanıyoruz
    product_id = fields.Many2one('gastro.supplier.offer', string='Tedarikçi İlanı', readonly=True)
    procure_qty = fields.Float(string='Alınacak Miktar', required=True, default=1.0)

    def action_confirm_procurement(self):
        self.ensure_one()
        
        # 1. Depoda var mı kontrol et (self.product_id.id üzerinden)
        existing_stock = self.env['gastro.local.inventory'].search([
            ('supplier_product_id', '=', self.product_id.id)
        ], limit=1)

        alinan_miktar = self.procure_qty 

        # 2. Mutfağa ekle veya yeni kayıt aç
        if existing_stock:
            existing_stock.qty_in_stock += alinan_miktar
        else:
            self.env['gastro.local.inventory'].create({
                'supplier_product_id': self.product_id.id, # Hatayı çözen kritik satır
                'qty_in_stock': alinan_miktar,
            })
        
        # 3. Tedarikçiden düş
        if self.product_id.available_stock >= alinan_miktar:
            self.product_id.available_stock -= alinan_miktar
        else:
            self.product_id.available_stock = 0.0


