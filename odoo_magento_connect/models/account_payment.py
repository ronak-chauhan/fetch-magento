from odoo import api, models


class account_payment(models.Model):
    _inherit = "account.payment"

    def post(self):
        res = super(account_payment, self).post()
        saleModel = self.env['sale.order']
        enableOrderInvoice = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_magento_connect.mob_sale_order_invoice'
        )
        for rec in self:
            invObjs = rec.invoice_ids
            for invObj in invObjs:
                invInfo = invObj.read(['ref', 'state'])
                if invInfo[0]['ref']:
                    saleObjs = saleModel.search(
                        [('name', '=', invInfo[0]['ref'])])
                    for saleObj in saleObjs:
                        mapObjs = self.env['wk.order.mapping'].search(
                            [('erp_order_id', '=', saleObj.id)])
                        if mapObjs and saleObj.ecommerce_channel == "magento" \
                                and enableOrderInvoice and saleObj.is_invoiced:
                            saleObj.manual_magento_order_operation("invoice")
        return res
