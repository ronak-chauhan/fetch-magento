from odoo import api, models
from .res_partner import _unescape


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.model
    def create(self, vals):
        if 'magento' in self._context:
            vals['name'] = _unescape(vals['name'])
            prodObj = self.env['product.product'].create({
                'name' : vals['name'],
                'type' : 'service'
            })
            vals['product_id'] = prodObj.id
        return super(DeliveryCarrier, self).create(vals)
