from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    mob_delivery = fields.Boolean(string="Delivery Order Create By magento.")

