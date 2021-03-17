

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mob_stock_action = fields.Selection(
        [('qoh', 'Quantity on hand'), ('fq', 'Forecast Quantity')],
        string='Stock Management',
        help="Manage Stock")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
        IrConfigPrmtr.set_param(
            "odoo_magento_connect.mob_stock_action", self.mob_stock_action
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
        stockAction = IrConfigPrmtr.get_param('odoo_magento_connect.mob_stock_action', default='qoh')
        res.update({
            'mob_stock_action' : stockAction,
        })
        return res
