from odoo import models, fields, api
from odoo.exceptions import ValidationError

class GastroRecipe(models.Model):
    _name = 'gastro.recipe'
    _description = 'Üretim Reçetesi'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reçete Adı', required=True, tracking=True)
    portion_count = fields.Float(string='Porsiyon Adedi', default=1.0, required=True, tracking=True)
    description = fields.Text(string='Hazırlanış Notları')
    
    line_ids = fields.One2many('gastro.recipe.line', 'recipe_id', string='Kullanılan Malzemeler')
    
    total_cost = fields.Float(string='Tahmini Toplam Maliyet (TL)', compute='_compute_recipe_costs', store=True)
    portion_cost = fields.Float(string='Tahmini Porsiyon Maliyeti (TL)', compute='_compute_recipe_costs', store=True)

    state = fields.Selection([
        ('draft', 'Taslak'),
        ('test', 'Test Aşamasında'),
        ('approved', 'Onaylandı')
    ], string='Durum', default='draft', tracking=True)

    @api.depends('line_ids.line_cost')
    def _compute_recipe_costs(self):
        for recipe in self:
            total = sum(line.line_cost for line in recipe.line_ids)
            recipe.total_cost = total
            if recipe.portion_count > 0:
                recipe.portion_cost = total / recipe.portion_count
            else:
                recipe.portion_cost = 0.0


class GastroRecipeLine(models.Model):
    _name = 'gastro.recipe.line'
    _description = 'Reçete Malzeme Satırı'

    recipe_id = fields.Many2one('gastro.recipe', string='Reçete', ondelete='cascade')
    ingredient_id = fields.Many2one('gastro.ingredient', string='Evrensel Hammadde', required=True)
    qty = fields.Float(string='Gereken Miktar', required=True, default=1.0)
    uom = fields.Selection(related='ingredient_id.uom', string='Birim', readonly=True)
    
    # Tedarikçi ilanlarından o anki ortalama fiyatı güvenli şekilde çeker, hata vermez
    line_cost = fields.Float(string='Tahmini Satır Maliyeti', compute='_compute_line_cost', store=True)

    @api.depends('ingredient_id', 'qty')
    def _compute_line_cost(self):
        for line in self:
            if line.ingredient_id:
                # Bu ürüne ait tedarikçi ilanlarını buluyoruz
                offers = self.env['gastro.supplier.offer'].search([('ingredient_id', '=', line.ingredient_id.id)])
                if offers:
                    # Varsa ortalama birim fiyatını baz alıyoruz
                    avg_price = sum(offers.mapped('price')) / len(offers)
                    line.line_cost = avg_price * line.qty
                else:
                    # Tedarikçi ilanı henüz yoksa sistem hata vermez, maliyeti 0 sayar
                    line.line_cost = 0.0
            else:
                line.line_cost = 0.0






 # ==========================================
# ALICI TALEPLERİ (İHALE AÇILIŞI)
# ==========================================
class GastroBuyerRequest(models.Model):
    _name = 'gastro.buyer.request'
    _description = 'Alıcı Talepleri (İhale)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Talep Başlığı', required=True, tracking=True)
    
    # HATA VEREN EKSİK SATIR BURASIYDI, EKLENDİ:
    recipe_id = fields.Many2one('gastro.recipe', string='Talep Edilen Reçete', required=True)

    buyer_id = fields.Many2one(
        'res.partner', 
        string='Alıcı / Müşteri', 
        default=lambda self: self.env.user.partner_id.id, 
        readonly=True 
    )
    
    expected_date = fields.Date(string='İstenen Teslim Tarihi', required=True)
    total_portions = fields.Integer(string='Porsiyon / Adet Miktarı', required=True)
    description = fields.Text(string='Özel Şartlar ve Detaylar')
    
    state = fields.Selection([
        ('draft', 'Taslak'),
        ('open', 'Tekliflere Açık'),
        ('closed', 'İhale Kapandı')
    ], string='İhale Durumu', default='draft', tracking=True)

    bid_ids = fields.One2many('gastro.restaurant.bid', 'request_id', string='Gelen Teklifler')

    def action_open_bidding(self):
        for rec in self:
            rec.state = 'open'

    def action_close_bidding(self):
        for rec in self:
            rec.state = 'closed'


# ==========================================
# RESTORAN TEKLİFLERİ (İHALEYE KATILIM)
# ==========================================
class GastroRestaurantBid(models.Model):
    _name = 'gastro.restaurant.bid'
    _description = 'Restoran İhale Teklifi'

    request_id = fields.Many2one('gastro.buyer.request', string='İlgili İhale', required=True, ondelete='cascade')
    restaurant_id = fields.Many2one(
        'res.partner', 
        string='Teklif Veren Restoran', 
        default=lambda self: self.env.user.partner_id.id, 
        readonly=True
    )
    
    # MALİYET VE FİYATLANDIRMA
    raw_material_cost = fields.Float(string='Toplam Ham Madde Maliyeti (TL)', compute='_compute_totals', store=True)
    commission_rate = fields.Float(string='Üretim Komisyonu (%)', default=20.0)
    proposed_price = fields.Float(string='Alıcıya Sunulan Fiyat (TL)', compute='_compute_totals', store=True)

    notes = fields.Text(string='Restoranın Notu / Teslimat Şartları')
    state = fields.Selection([
        ('pending', 'Değerlendirmede'),
        ('accepted', 'Kabul Edildi'),
        ('rejected', 'Reddedildi')
    ], string='Teklif Durumu', default='pending')
    # 1. KURAL: Bir restoran aynı ihaleye sadece BİR KERE teklif verebilir
    _sql_constraints = [
        ('unique_restaurant_bid', 'UNIQUE(request_id, restaurant_id)', 'Bu ihale için zaten bir teklif verdiniz. İkinci bir teklif oluşturamazsınız!')
    ]

    # 2. KURAL: Depoda yeterli ürün yoksa teklifi kaydettirmez, hata verir
    @api.constrains('line_ids')
    def _check_inventory_stock(self):
        for bid in self:
            for line in bid.line_ids:
                # Malzeme seçilmiş ama depodaki stok yetersizse
                if line.local_inventory_id and line.qty > line.local_inventory_id.qty_in_stock:
                    raise ValidationError(
                        f"Stok Hatası: '{line.ingredient_name}' için deponuzda yeterli miktar yok!\n"
                        f"İstenen Miktar: {line.qty}\n"
                        f"Deponuzdaki Miktar: {line.local_inventory_id.qty_in_stock}"
                    )
    

    # SEÇİLEN MALZEMELER LİSTESİ (Restoranın Deposundan)
    line_ids = fields.One2many('gastro.restaurant.bid.line', 'bid_id', string='Kullanılacak Depo Malzemeleri')

    @api.depends('line_ids.line_cost', 'commission_rate')
    def _compute_totals(self):
        for bid in self:
            total_cost = sum(line.line_cost for line in bid.line_ids)
            bid.raw_material_cost = total_cost
            bid.proposed_price = total_cost + (total_cost * (bid.commission_rate / 100.0))

    def action_accept_bid(self):
        for bid in self:
            other_bids = self.search([('request_id', '=', bid.request_id.id), ('id', '!=', bid.id)])
            other_bids.write({'state': 'rejected'})
            
            bid.state = 'accepted'
            bid.request_id.state = 'closed'

    def action_reject_bid(self):
        """Alıcı teklifi uygun bulmazsa reddeder."""
        for bid in self:
            bid.state = 'rejected'

    @api.onchange('request_id')
    def _onchange_request_id(self):
        """İhale seçildiğinde, reçetedeki malzemeleri porsiyonla çarparak otomatik tabloya doldurur."""
        if self.request_id and self.request_id.recipe_id:
            # Önceki satırları temizle (ihale değiştirilirse üst üste binmemesi için)
            self.line_ids = [(5, 0, 0)]
            
            line_vals = []
            portions = self.request_id.total_portions or 1.0
            
            # Reçetedeki malzemeleri dönüp teklif satırlarına ekle
            for r_line in self.request_id.recipe_id.line_ids:
                line_vals.append((0, 0, {
                    'ingredient_id': r_line.ingredient_id.id,     # <--- EKLENEN YENİ SATIR (Filtreleme için gizli anahtar)
                    'ingredient_name': r_line.ingredient_id.name, # Evrensel hammadde adını al
                    'qty': r_line.qty * portions,                 # Reçete miktarı * İhale Porsiyonu
                    'uom': r_line.uom,                            # Birimi al
                    # local_inventory_id alanı boş kalacak, restoran kendi seçecek
                }))
            
            self.line_ids = line_vals
    
# ==========================================
# TEKLİFİN ALT SATIRLARI (MUTFAK DEPOSUNDAN SEÇİM)
# ==========================================
class GastroRestaurantBidLine(models.Model):
    _name = 'gastro.restaurant.bid.line'
    _description = 'Teklif Malzeme Satırı'

    bid_id = fields.Many2one('gastro.restaurant.bid', string='İlgili Teklif', required=True, ondelete='cascade')

    # BU ALANIN TAM BURADA OLMASI ŞART:
    ingredient_id = fields.Many2one('gastro.ingredient', string='Hammadde Bağlantısı')

    ingredient_name = fields.Char(string='Gerekli Malzeme (Örn: Süt)', required=True)
    qty = fields.Float(string='Kullanılacak Miktar', required=True)
    uom = fields.Char(string='Birim')

    # DOMAIN KISMI:
    local_inventory_id = fields.Many2one(
        'gastro.local.inventory', 
        string='Mutfak Deposundan Seç', 
        domain="[('create_uid', '=', uid), ('qty_in_stock', '>', 0), ('supplier_product_id.ingredient_id', '=', ingredient_id)]",
        required=True
    )

    unit_price = fields.Float(string='Depo Geliş Fiyatı (TL)', related='local_inventory_id.purchase_price', readonly=True)
    line_cost = fields.Float(string='Satır Maliyeti (TL)', compute='_compute_line_cost', store=True)

    @api.depends('qty', 'unit_price')
    def _compute_line_cost(self):
        for line in self:
            line.line_cost = line.qty * line.unit_price



# ==========================================
# REÇETE EKLEME BAŞVURUSU (RESTORAN -> ADMİN)
# ==========================================
class GastroRecipeRequest(models.Model):
    _name = 'gastro.recipe.request'
    _description = 'Reçete Ekleme Başvurusu'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Önerilen Reçete Adı', required=True, tracking=True)
    restaurant_id = fields.Many2one(
        'res.partner', 
        string='Başvuru Yapan Restoran', 
        default=lambda self: self.env.user.partner_id.id, 
        readonly=True
    )
    state = fields.Selection([
        ('draft', 'Taslak'),
        ('submitted', 'Onay Bekliyor'),
        ('approved', 'Kabul Edildi'),
        ('rejected', 'Reddedildi')
    ], string='Başvuru Durumu', default='draft', tracking=True)

    # Evrensel katalogdan hammadde seçilecek satırlar
    line_ids = fields.One2many('gastro.recipe.request.line', 'request_id', string='Önerilen Malzemeler')

    def action_submit_request(self):
        for rec in self:
            rec.state = 'submitted'

    def action_approve_request(self):
        for rec in self:
            # Ana reçeteyi oluştur
            new_recipe = self.env['gastro.recipe'].create({
                'name': rec.name,
                'portion_count': 1.0,
                'state': 'draft'
            })
            # Başvuru içindeki hammadde satırlarını ana reçeteye aktar
            for line in rec.line_ids:
                self.env['gastro.recipe.line'].create({
                    'recipe_id': new_recipe.id,
                    'ingredient_id': line.ingredient_id.id,
                    'qty': line.qty,
                    'uom': line.uom.id if hasattr(line, 'uom') else False,
                })
            rec.state = 'approved'

    def action_reject_request(self):
        for rec in self:
            rec.state = 'rejected'


class GastroRecipeRequestLine(models.Model):
    _name = 'gastro.recipe.request.line'
    _description = 'Reçete Başvuru Malzeme Satırı'

    request_id = fields.Many2one('gastro.recipe.request', string='Başvuru Referansı', ondelete='cascade')
    ingredient_id = fields.Many2one('gastro.ingredient', string='Evrensel Hammadde', required=True)
    qty = fields.Float(string='Gerekli Miktar', default=1.0)
    uom = fields.Many2one('uom.uom', string='Birim')