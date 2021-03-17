# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"


    magento_prod_type = fields.Selection([
        ('bundle', 'Bundle'),
        ('grouped', 'Grouped')], string='Product Type', default='grouped')
