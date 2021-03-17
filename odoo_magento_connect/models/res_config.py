from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mob_discount_product = fields.Many2one(
        'product.product',
        string="Discount Product",
        help="""Service type product used for Discount purposes.""")
    mob_coupon_product = fields.Many2one(
        'product.product',
        string="Coupon Product",
        help="""Service type product used in Coupon.""")
    mob_payment_term = fields.Many2one(
        'account.payment.term',
        string="Magento Payment Term",
        help="""Default Payment Term Used In Sale Order.""")
    mob_sales_team = fields.Many2one(
        'crm.team',
        string="Magento Sales Team",
        help="""Default Sales Team Used In Sale Order.""")
    mob_sales_person = fields.Many2one(
        'res.users',
        string="Magento Sales Person",
        help="""Default Sales Person Used In Sale Order.""")
    mob_sale_order_invoice = fields.Boolean(string="Invoice")
    mob_sale_order_shipment = fields.Boolean(string="Shipping")
    mob_sale_order_cancel = fields.Boolean(string="Cancel")
    mob_delivery = fields.Boolean(string="Is Delivery")
    is_enable_rsl = fields.Boolean("RSL Enable?")
    customer_id_3pl = fields.Char(string="RSL Customer ID")
    customer_psw_3pl = fields.Char(string="RSL Password")
    auto_create_mode_3pl = fields.Boolean(string="Auto Mode For Create 3PL "
                                              "Orders")
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrConfigPrmtr = self.env['ir.config_parameter'].sudo()

        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_discount_product", self.mob_discount_product.id
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_coupon_product", self.mob_coupon_product.id
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_payment_term", self.mob_payment_term.id
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_sales_team", self.mob_sales_team.id
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_sales_person", self.mob_sales_person.id
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_sale_order_shipment", self.mob_sale_order_shipment
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_sale_order_cancel", self.mob_sale_order_cancel
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_sale_order_invoice", self.mob_sale_order_invoice
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.is_enable_rsl", self.is_enable_rsl
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.customer_id_3pl", self.customer_id_3pl
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.customer_psw_3pl", self.customer_psw_3pl
        )
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.auto_create_mode_3pl", self.auto_create_mode_3pl
        )
        self.company_id.mob_delivery = self.mob_delivery

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
        OrderShip = IrConfigPrmtr.get_param('odoo_magento_connect.mob_sale_order_shipment')
        OrderInv = IrConfigPrmtr.get_param('odoo_magento_connect.mob_sale_order_invoice')
        OrderCanel = IrConfigPrmtr.get_param('odoo_magento_connect.mob_sale_order_cancel')
        Delivery = IrConfigPrmtr.get_param('odoo_magento_connect.mob_delivery')
        DicsProd = int(IrConfigPrmtr.get_param('odoo_magento_connect.mob_discount_product'))
        CpnProd = int(IrConfigPrmtr.get_param('odoo_magento_connect.mob_coupon_product'))
        pymntTrm = int(IrConfigPrmtr.get_param('odoo_magento_connect.mob_payment_term'))
        salesTeam = int(IrConfigPrmtr.get_param('odoo_magento_connect.mob_sales_team'))
        SalesPrsn = int(IrConfigPrmtr.get_param('odoo_magento_connect.mob_sales_person'))
        is3plenable = IrConfigPrmtr.get_param('odoo_magento_connect.is_enable_rsl')
        auto_create_mode_3pl = IrConfigPrmtr.get_param('odoo_magento_connect.auto_create_mode_3pl')
        if auto_create_mode_3pl == 'True':
            auto_create_mode_3pl = True
        else:
            auto_create_mode_3pl = False
        if is3plenable == 'True':
            is3plenable = True
        else:
            is3plenable = False
        cust_id = IrConfigPrmtr.get_param(
            'odoo_magento_connect.customer_id_3pl')
        cust_psw = IrConfigPrmtr.get_param(
            'odoo_magento_connect.customer_psw_3pl')

        res.update({
            'mob_delivery' : self.env.user.company_id.mob_delivery,
            'mob_sale_order_shipment' : OrderShip,
            'mob_sale_order_invoice' : OrderInv,
            'mob_sale_order_cancel' : OrderCanel,
            'mob_discount_product' : DicsProd,
            'mob_coupon_product' : CpnProd,
            'mob_payment_term' : pymntTrm,
            'mob_sales_team' : salesTeam,
            'mob_sales_person' : SalesPrsn,
            'is_enable_rsl':is3plenable,
            'customer_id_3pl':cust_id,
            'customer_psw_3pl':cust_psw,
            'auto_create_mode_3pl':auto_create_mode_3pl
        })
        return res
