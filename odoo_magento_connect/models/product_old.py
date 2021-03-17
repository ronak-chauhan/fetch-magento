import binascii

import requests

from odoo import _, api, fields, models
from .res_partner import _unescape


class ProductProduct(models.Model):
    _inherit = 'product.product'

    mob_mapping_ids = fields.One2many(
        string='Mappings',
        comodel_name='magento.product',
        inverse_name='pro_name',
        copy=False
    )


    @api.model
    def create(self, vals):
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        mapTempModel = self.env['magento.product.template']
        if 'magento' in ctx:
            mageId = vals.pop('mage_id', 0)
            magento_stock_id = vals.pop('magento_stock_id', 0)
            attrValIds = vals.get('value_ids', [])
            vals = self.update_vals(vals, instanceId, True)
        productObj = super(ProductProduct, self).create(vals)
        if 'magento' in ctx:
            attrValModel = self.env['product.attribute.value']
            attrLineModel = self.env['product.template.attribute.line']
            productAttrValModel = self.env['product.template.attribute.value']
            templateId = productObj.product_tmpl_id.id
            if templateId:
                mappDict = {
                    'instance_id' : instanceId,
                    'created_by' : 'Magento',
                }
                domain = [('product_tmpl_id', '=', templateId)]
                for attrValId in attrValIds:
                    attrId = attrValModel.browse(attrValId).attribute_id.id
                    searchDomain = domain + [('attribute_id', '=', attrId)]
                    attrLineObjs = attrLineModel.search(searchDomain)
                    if not attrLineObjs:
                        attrLineObjs = attrLineModel.create({'attribute_id':
                                                                 attrId,
                                                             'product_tmpl_id': templateId})
                    for attrLineObj in attrLineObjs:
                        if attrValId not in attrLineObj.value_ids.ids:
                            attrLineObj.value_ids = [(4, attrValId)]
                        productAttrValObj = productAttrValModel.search(
                            [('product_attribute_value_id', '=', attrValId),
                             ('attribute_line_id', '=', attrLineObj.id),
                             ('product_tmpl_id', '=', templateId)])
                        if not productAttrValObj:
                            pavm_id = productAttrValModel.create({
                                'product_attribute_value_id': attrValId,
                                'attribute_line_id': attrLineObj.id,
                                'product_tmpl_id': templateId
                            })
                            self._cr.execute("insert into "
                                             "product_variant_combination("
                                             "product_product_id,"
                                             "product_template_attribute_value_id) values({}, {})".format(self.id, pavm_id.id))

                        else:
                            if productAttrValObj:
                                if self.id not in \
                                        productAttrValObj.ptav_product_variant_ids.ids:
                                    self._cr.execute("insert into "
                                                     "product_variant_combination("
                                                     "product_product_id,"
                                                     "product_template_attribute_value_id) values({}, {})".format(
                                    self.id, productAttrValObj[0].id))

                if mageId:
                    mapTempObjs = mapTempModel.search([
                        ('erp_template_id', '=', templateId),
                        ('instance_id', '=', instanceId)
                    ])
                    if not mapTempObjs:
                        price = vals.get('list_price', 0)
                        mapTempDict = mappDict.copy()
                        mapTempDict.update({
                            'template_name' : templateId,
                            'erp_template_id' : templateId,
                            'mage_product_id' : mageId,
                            'base_price' : price,
                        })
                        mapTempModel.create(mapTempDict)
                    else:
                        mapTempObjs.need_sync = 'No'
                    mappDict.update({
                        'pro_name' : productObj.id,
                        'oe_product_id' : productObj.id,
                        'mag_product_id' : mageId,
                        'magento_stock_id' : magento_stock_id
                    })
                    self.env['magento.product'].create(mappDict)

        return productObj


class ProductCategory(models.Model):
    _inherit = 'product.category'

    def write(self, vals):
        if 'magento' in self._context:
            if vals.get('name'):
                vals['name'] = _unescape(vals['name'])
        else:
            categModel = self.env['magento.category']
            for catObj in self:
                mapObjs = categModel.search(
                    [('oe_category_id', '=', catObj.id)])
                if mapObjs:
                    mapObjs.write({'need_sync' : 'Yes'})
        return super(ProductCategory, self).write(vals)
