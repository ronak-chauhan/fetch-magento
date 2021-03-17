# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################


from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _action_launch_stock_rule(self):
        ctx = dict(self._context or {})
        filterIds = []
        for line in self:
            orderObj = line.order_id
            if orderObj.ecommerce_channel == "magento":
                filterIds.append(line.id)
        if filterIds:
            ctx.update({'wk_skip': filterIds})
        return super(SaleOrderLine, self.with_context(ctx))._action_launch_stock_rule()