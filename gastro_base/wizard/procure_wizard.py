from odoo import models, fields

class GastroProcureWizard(models.TransientModel):
    _name = 'gastro.procure.wizard'
    _description = 'Tedarik Etme Sihirbazı'

    # DİKKAT: Sihirbaz da artık tedarikçi ilanı üzerinden çalışıyor
    product_id = fields.Many2one('gastro.supplier.offer', string='Alınacak İlan', readonly=True)
    
    available_stock = fields.Float(related='product_id.available_stock', string='Tedarikçideki Stok', readonly=True)
    procure_qty = fields.Float(string='Alınacak Miktar', required=True, default=1.0)

    def action_confirm_procurement(self):
        # 1. Tedarikçinin stokundan düş
        if self.product_id.available_stock >= self.procure_qty:
            self.product_id.available_stock -= self.procure_qty
        
        # 2. Mutfağın kendi deposuna ekle
        local_stock = self.env['gastro.local.inventory'].search([('supplier_product_id', '=', self.product_id.id)], limit=1)
        if local_stock:
            local_stock.qty_in_stock += self.procure_qty
        else:
            self.env['gastro.local.inventory'].create({
                'supplier_product_id': self.product_id.id,
                'qty_in_stock': self.procure_qty
            })