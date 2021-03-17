# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################


from odoo import api, fields, models


class ProductPack(models.Model):
    _inherit = "product.pack"


    magento_item_title = fields.Char(string="Bundle's Option Title", help="Item title for the bundle type products. For grouped product this will be readonly")

    @api.model
    def assign_packitems(self, productId, prodType, vals):
        prdouctTemplt = self.env['product.product'].browse(int(productId)).product_tmpl_id
        prdouctTemplt.write({
            'is_pack' : True,
            'pack_stock_management' : 'decrmnt_products',
            'magento_prod_type' : prodType,
        })
        unlinkRecs = self.search([('wk_product_template', '=', prdouctTemplt.id)])
        if unlinkRecs:
            unlinkRecs.unlink()
        packItemIds = []
        for itemDIct in vals:
            packItemIds.append((0, 0, itemDIct))
        prdouctTemplt.write({'wk_product_pack' : packItemIds})
        return True
