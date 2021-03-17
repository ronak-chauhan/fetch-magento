from odoo import fields, models


class wk_order_mapping(models.Model):
    _name = "wk.order.mapping"
    _description = "MOB Order Mapping"
    _order = 'id desc'

    name = fields.Char(string='eCommerce Order Ref.')
    ecommerce_channel = fields.Selection(
        related="erp_order_id.ecommerce_channel", string="eCommerce Channel")
    erp_order_id = fields.Many2one(
        'sale.order', string='ODOO Order Id', required=1)
    ecommerce_order_id = fields.Integer(
        string='eCommerce Order Id', required=1)
    order_status = fields.Selection(
        related="erp_order_id.state", string="Order Status")
    is_invoiced = fields.Boolean(
        related="erp_order_id.is_invoiced", string="Paid")
    is_shipped = fields.Boolean(
        related="erp_order_id.is_shipped", string="Shipped")
