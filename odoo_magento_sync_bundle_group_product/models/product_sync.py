# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from collections import defaultdict
import sys
from odoo.http import request
from odoo import api, models


class MagentoSynchronization(models.TransientModel):
    _inherit = "magento.synchronization"

    def display_message(self, message):
        reqCtx = dict(request.context or {})
        if reqCtx.get('bundle_group'):
            message = reqCtx.pop('bundle_group')
            request.context = reqCtx
        return super(MagentoSynchronization, self).display_message(message)

    @api.model
    def get_sync_template_ids(self, templateIds):
        ctx = dict(self._context or {})
        packTemplates = []
        successExpIds, errorIds = [], []
        template = super(MagentoSynchronization, self).get_sync_template_ids(templateIds)
        if template and ctx.get('sync_opr') == 'export':
            tempObjs = self.env['product.template'].browse(template)
            packTemplates = tempObjs.filtered(lambda obj: obj.is_pack == True)
            template = list(set(template) - set(packTemplates.ids))
            if packTemplates:
                successExpIds, errorIds = self._export_groupbundle_check(packTemplates)
        if not template and packTemplates:
            template = packTemplates.ids
            text = ''
            if successExpIds:
                text = "\nThe Listed product(s) %s successfully created on Magento." % (
                    successExpIds)
            if errorIds:
                text += '\nThe Listed Product(s) %s does not synchronized on magento.' % errorIds
            reqCtx = dict(request.context or {})
            reqCtx['bundle_group'] = text
            request.context = reqCtx
        return template

    @api.model
    def _export_groupbundle_check(self, packTemplates):
        connection = self.env['magento.configure']._create_connection()
        successExpIds, errorIds = [], []
        if connection:
            url = connection[0]
            token = connection[1]
            for templateObj in packTemplates:
                expProduct = self._export_specific_template(templateObj, url, token)
                if expProduct[0] > 0:
                    successExpIds.append(templateObj.id)
                else:
                    errorIds.append(templateObj.id)
        return successExpIds, errorIds

    @api.model
    def _check_mapping(self, mapData, mapModel):
        ctx = dict(self._context or {})
        domain = [('instance_id', '=', ctx.get('instance_id')), (mapData[0] , '=', mapData[1])]
        return self.env[mapModel].search(domain, limit=1)

    def _get_product_array(self, url, token, prodObj, getProductData):
        getProductData = super(MagentoSynchronization, self)._get_product_array(url, token, prodObj, getProductData)
        if prodObj._name == 'product.product' and prodObj.is_pack:
            getProductData = self._update_bundle_group_product_array(prodObj, getProductData, url, token)
        if sys._getframe().f_back.f_code.co_name == '_update_specific_product' and prodObj.is_pack:
            getProductData.pop('price')
        return getProductData

    def _update_bundle_group_product_array(self, prodObj, getProductData, url, token):
        titleList = []
        for packItem in prodObj.wk_product_pack:
            vrntItem = packItem.product_name
            iTitle = packItem.magento_item_title
            pQty = packItem.product_quantity
            existProdMap = self._check_mapping(['pro_name', vrntItem.id], 'magento.product')
            if not existProdMap:
                existProdTempMap = self._check_mapping(['template_name', vrntItem.product_tmpl_id.id], 'magento.product.template')
                if not existProdTempMap:
                    res1 = self._export_specific_template(vrntItem.product_tmpl_id, url, token)
                else:
                    res2 = self._update_specific_product_template(existProdTempMap, url, token)
                existProdMap = self._check_mapping(['pro_name', vrntItem.id], 'magento.product')
            mProdId = existProdMap and existProdMap.mag_product_id
            if mProdId:
                titleList.append((iTitle or 'wk_no', [vrntItem.default_code, pQty]))

        if prodObj.magento_prod_type == 'bundle':
            customAttributes = getProductData.get('custom_attributes', [])
            extensionAttributes = getProductData.get('extension_attributes', {})
            custAttrList = [
                {'attribute_code' : 'price_view', 'value' : 0 },
                {'attribute_code' : 'price_type', 'value' : 0 }
            ]
            customAttributes += custAttrList
            titleDict = defaultdict(dict)
            for titel, prodData in titleList:
                mProdId = str(prodData[0])
                titleDict[titel].update({mProdId : prodData[1]})
            titleDict = dict(titleDict)
            bundlOPtion = []
            for title, linkItems in titleDict.items():
                productLink = []
                for pSku, pQty in linkItems.items():
                    productLink.append({
                        'sku' : pSku,
                        'qty' : pQty,
                        'can_change_quantity' : 1
                        })
                bundleAttr = {
                    'title' : title,
                    'type' : 'select',
                    'required' : 1,
                    'product_links' : productLink
                    }
                bundlOPtion.append(bundleAttr)
            extensionAttributes.update(
                {'bundle_product_options' : bundlOPtion}
            )
            getProductData.update({'extension_attributes' : extensionAttributes})
            getProductData.update({'custom_attributes' : customAttributes})
        else:
            productLink = getProductData.get('product_links', [])
            sku = getProductData.get('sku') or prodObj.default_code
            for lineItem in titleList:
                productLink.append({
                    'sku' : sku,
                    'link_type' : 'associated',
                    'linked_product_sku' : lineItem[1][0],
                    'linked_product_type' : 'simple',
                    "extension_attributes": {
                        "qty": lineItem[1][1]
                        }
                    })
            getProductData.update({'product_links' : productLink})
        return getProductData

    def _export_specific_template(self, templateObj, url, token):
        existRec = self._check_mapping(['template_name', templateObj.id], 'magento.product.template')
        if existRec:
            return [1, templateObj.id]
        return super(MagentoSynchronization, self)._export_specific_template(templateObj, url, token)

    def prodcreate(self, url, token, vrntObj, prodtype, sku, getProductData):
        if vrntObj.wk_product_pack:
            prodtype = vrntObj.magento_prod_type
            getProductData.update({'type_id' : prodtype})
            if prodtype == 'bundle':
                getProductData.pop('price')
        return super(MagentoSynchronization, self).prodcreate(
            url, token, vrntObj, prodtype, sku, getProductData)
