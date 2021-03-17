import requests
import binascii
from odoo import api, fields, models
from .res_partner import _unescape

class ProductTemplate(models.Model):
    _inherit = "product.template"

    prod_type = fields.Char(string='Magento Type')
    config_sku = fields.Char(string='SKU')
    categ_ids = fields.Many2many(
        'product.category',
        'product_categ_rel',
        'product_id',
        'categ_id',
        string='Extra Categories')
    attribute_set_id = fields.Many2one(
        'magento.attribute.set', copy=False,
        string='Magento Attribute Set',
        help="Magento Attribute Set, Used during configurable product generation at Magento.")
    mob_mapping_ids = fields.One2many(
        string='Mappings',
        comodel_name='magento.product.template',
        inverse_name='template_name',
        copy=False
    )

    @api.model
    def create(self, vals):
        ctx = dict(self._context or {})
        if 'magento' in ctx:
            mageId = vals.pop('mage_id', 0)
            vals = self.update_vals(vals, True)
        prodTempObj = super(ProductTemplate, self).create(vals)
        if 'magento' in ctx and 'configurable' in ctx:
            mappingData = {
                'template_name' : prodTempObj.id,
                'erp_template_id' : prodTempObj.id,
                'mage_product_id' : mageId,
                'base_price' : vals['list_price'],
                'is_variants' : True,
                'instance_id' : ctx.get('instance_id'),
                'created_by' : 'Magento'
            }
            self.env['magento.product.template'].create(mappingData)
        #if vals.get('attribute_set_id', False):
        #    prodAttribute = {
        #        'template_name' : prodTempObj.id,
         #       'erp_template_id' : prodTempObj.id,
          #      'base_price' : vals['list_price'],
           #     'is_variants' : True,
            #    'instance_id' : ctx.get('instance_id'),
             #   'created_by' : 'Magento'
           # }
           # default = self.env['magento.product.template'].create(
            # prodAttribute)
            ## prodTempObj.set_magento_attribute()
            #prodTempObj._create_variant_ids()

        return prodTempObj

    # def set_magento_attribute(self):
    #     for rec in self.attribute_line_ids:
    #         for value in rec.value_ids:
    #             vals = {}
    #             lines_without_no_variants = self.valid_product_template_attribute_line_ids._without_no_variant_attributes()
    #             all_variants = self.with_context(
    #                 active_test=False).product_variant_ids.sorted('active')
    #             single_value_lines = lines_without_no_variants.filtered(
    #                 lambda ptal: len(
    #                     ptal.product_template_value_ids._only_active()) == 1)

                # for variants in all_variants:
                #     combination = variants.product_template_attribute_value_ids
                #     for comb in combination:
                #         vals = {
                #            'name': value.id,
                #            'erp_id' : variants.product_tmpl_id.id,
                #             }
                # self.env['magento.product.attribute.value'].create(vals)

    def write(self, vals):
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id', False)
        if 'magento' in ctx:
            vals.pop('mage_id', None)
            vals = self.update_vals(vals)
        mapTempModel = self.env['magento.product.template']
        for tempObj in self:
            tempMapObjs = mapTempModel.search(
                [('template_name', '=', tempObj.id)])
            for tempMapObj in tempMapObjs:
                if instanceId and tempMapObj.instance_id.id == instanceId:
                    tempMapObj.need_sync = 'No'
                else:
                    tempMapObj.need_sync = 'Yes'
        return super(ProductTemplate, self).write(vals)

    def _create_variant_ids(self):
        if not self._context.get("magento", False):
            return super(ProductTemplate, self)._create_variant_ids()
        return True

    @api.model
    def update_vals(self, vals, create=False):
        if vals.get('default_code'):
            vals['config_sku'] = _unescape(vals.pop('default_code', ''))
        if vals.get('name'):
            vals['name'] = _unescape(vals['name'])
        if vals.get('description'):
            vals['description'] = _unescape(vals['description'])
        if vals.get('description_sale'):
            vals['description_sale'] = _unescape(vals['description_sale'])
        category_ids = vals.pop('category_ids', None)
        if category_ids:
            categIds = list(set(category_ids))
            defaultCategObj = self.env["magento.configure"].browse(
                self._context['instance_id']).category
            if defaultCategObj and create:
                vals['categ_id'] = defaultCategObj.id
            vals['categ_ids'] = [(6, 0, categIds)]
        imageUrl = vals.pop('image_url', False)
        if imageUrl:
            proImage = binascii.b2a_base64(requests.get(imageUrl, verify=False).content)
            vals['image_1920'] = proImage
        vals.pop('attribute_list', None)
        vals.pop('magento_stock_id', None)
        return vals



