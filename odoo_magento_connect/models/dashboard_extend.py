##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2019 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from datetime import date
import json
from datetime import datetime, timedelta

from babel.dates import format_date, format_datetime

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

Itme_Type = [
    ('product', 'Product'),
    ('category', 'Category'),
    ('partner', 'Partner'),
    ('order', 'Order'),
    ('attribute', 'Attribute'),
]

modelName = {
    'product': [
        1,
        'product.template',
        'magento.product.template',
        'template_name',
        'magento_product_template'],
    'category': [
        1,
        'product.category',
        'magento.category',
        'cat_name',
        'magento_category'],
    'order': [
        2,
        'sale.order',
        'wk.order.mapping',
        'erp_order_id',
        'wk_order_mapping'],
    'partner': [
        0,
        'res.partner',
        'magento.customers',
        '',
        'magento_customers'],
    'attribute': [
        0,
        'product.attribute',
        'magento.product.attribute',
        'name',
        'magento_product_attribute'],
}
fieldName = {
    'product': [
        'count_need_sync_product',
        'count_no_sync_product',
        'product.product_template_form_view'],
    'category': [
        'count_need_sync_category',
        'count_no_sync_category',
        'product.product_category_form_view'],
    'order': [
        'count_need_invoice',
        'count_need_delivery',
        'sale.view_order_form'],
    'partner': [
        '',
        '',
        'base.view_partner_form'],
    'attribute': [
        '',
        'count_no_sync_attribute',
        'product.product_attribute_view_form'],
}


class MobDashboard(models.Model):
    _name = 'mob.dashboard'
    _description = 'Mob Dashboard'

    active = fields.Boolean(related="instance_id.active")
    instance_id = fields.Many2one(
        'magento.configure', 'Magento Instance', ondelete='cascade',
        default=lambda self: self.env['magento.configure'].search(
            [('active', '=', True)], limit=1))
    item_name = fields.Selection(Itme_Type, string="Dashboard Item Name")
    name = fields.Char(string="Name")
    color = fields.Integer(string='Color Index')
    kanban_dashboard_graph = fields.Text()
    count_mapped_records = fields.Integer(compute='_compute_record_count')
    count_need_sync_product = fields.Integer(compute='_compute_record_count')
    count_no_sync_product = fields.Integer(compute='_compute_record_count')
    count_need_sync_category = fields.Integer(compute='_compute_record_count')
    count_no_sync_category = fields.Integer(compute='_compute_record_count')
    count_need_invoice = fields.Integer(compute='_compute_record_count')
    count_need_delivery = fields.Integer(compute='_compute_record_count')
    count_no_sync_attribute = fields.Integer(compute='_compute_record_count')
    count_invoiced_records = fields.Integer(compute='_compute_record_count')
    count_delivered_records = fields.Integer(compute='_compute_record_count')


    def get_connection_info(self):
        configModel = self.env['magento.configure']
        success = False
        defId = False
        activeConObjs = configModel.search([('active', '=', True)])
        inactiveConObjs = configModel.search([('active', '=', False)])
        if activeConObjs:
            defConnection = activeConObjs[0]
            defId = defConnection.id
            if defConnection.connection_status:
                success = True
        totalConnections = activeConObjs.ids + inactiveConObjs.ids
        res = {
            'totalcon': len(totalConnections),
            'total_ids': totalConnections,
            'active_ids': activeConObjs.ids,
            'inactive_ids': inactiveConObjs.ids,
            'active': len(activeConObjs.ids),
            'inactive': len(inactiveConObjs.ids),
            'def_id': defId,
            'success': success
        }
        return res


    @api.model
    def _create_dashboard(self, instanceObj):
        for itemName in modelName.keys():
            vals = {
                'name': itemName.title(),
                'instance_id': instanceObj.id,
                'item_name': itemName,
            }
            self.create(vals)
        return True


    def open_configuration(self):
        self.ensure_one()
        instanceId = self.instance_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configure Magento Api',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'magento.configure',
            'res_id': instanceId,
            'target': 'current',
            'domain': '[]',
        }


    def open_view_rec(self):
        self.ensure_one()
        ctx = dict(self._context or {})
        instanceId = self.instance_id.id
        resModel = ctx.get('res_model')
        rType = ctx.get('rec_type')
        domain = [('instance_id', '=', instanceId)]
        if rType == 'config':
            domain += [('is_variants', '=', True)]
        elif rType == 'simple':
            domain += [('is_variants', '=', False)]
        elif rType == 'partner':
            domain += [('mag_address_id', '=', 'customer')]
        elif rType == 'address':
            domain += [('mag_address_id', '!=', 'customer')]
        recIds = self.env[resModel].search(domain).ids
        return {
            'name': ('Records'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': resModel,
            'view_id': False,
            'domain': [('id', 'in', recIds)],
            'target': 'current',
        }


    def open_order_view_rec(self):
        self.ensure_one()
        ctx = dict(self._context or {})
        instanceId = self.instance_id.id
        resModel = ctx.get('res_model')
        rType = ctx.get('rec_type')
        domain = [('instance_id', '=', instanceId)]
        orderObjs = self.env[resModel].search(domain)
        recIds = []
        for orderObj in orderObjs:
            if orderObj.order_status == rType:
                recIds.append(orderObj.id)

        return {
            'name': ('Records'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': resModel,
            'view_id': False,
            'domain': [('id', 'in', recIds)],
            'target': 'current',
        }


    def show_report(self):
        self.ensure_one()
        ctx = dict(self._context or {})
        repType = ctx.get('r_type')
        itemType = self.item_name
        if itemType == "partner":
            itemType = "customer"
        if repType == 'success':
            status = 'yes'
        else:
            status = 'no'
        resModel = "magento.sync.history"
        domain = [('status', '=', status), ('action_on', '=', itemType)]
        itemHistory = self.env[resModel].search(domain).ids
        return {
            'name': ('Reports'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': resModel,
            'view_id': False,
            'domain': [('id', 'in', itemHistory)],
            'target': 'current',
        }


    def create_new_rec(self):
        self.ensure_one()
        ctx = dict(self._context or {})
        itemType = self.item_name
        resModel = modelName[itemType][1]
        envRefId = fieldName[itemType][2]
        viewId = self.env.ref(envRefId).id
        return {
            'name': _('Create invoice/bill'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': resModel,
            'view_id': viewId,
            'context': ctx,
        }


    def get_action_mapped_records(self):
        self.ensure_one()
        resModel = self._context.get('map_model')
        recordIds = self.env[resModel].search(
            [('instance_id', '=', self.instance_id.id)]).ids
        return {
            'name': ('Records'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': resModel,
            'view_id': False,
            'domain': [('id', 'in', recordIds)],
            'target': 'current',
        }


    def open_action(self):
        self.ensure_one()
        itemType = self.item_name
        ctx = dict(
            map_model=modelName[itemType][2]
        )
        res = self.with_context(ctx).get_action_mapped_records()
        return res


    def action_open_update_records(self):
        self.ensure_one()
        resModel = self._context.get('map_model')
        domain = [('instance_id', '=', self.instance_id.id),
                  ('need_sync', '=', 'Yes')]
        recordIds = self.env[resModel].search(domain).ids
        return {
            'name': ('Record'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': resModel,
            'view_id': False,
            'domain': [('id', 'in', recordIds)],
            'target': 'current',
        }


    def action_open_export_records(self):
        self.ensure_one()
        mapModel = self._context.get('map_model')
        coreModel = self._context.get('core_model')
        fieldName = self._context.get('field_name')
        domain = []
        mappedObj = self.env[mapModel].search(
            [('instance_id', '=', self.instance_id.id)])
        mapObjIds = mappedObj.mapped(fieldName).ids
        if coreModel == 'product.template':
            domain += [('type', '!=', 'service')]
        recordIds = self.env[coreModel].search(domain).ids
        notMapIds = list(set(recordIds) - set(mapObjIds))

        return {
            'name': ('Record'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': coreModel,
            'view_id': False,
            'domain': [('id', 'in', notMapIds)],
            'target': 'current',
        }


    def action_open_order_need(self):
        self.ensure_one()
        instanceId = self.instance_id.id
        needAction = self._context.get('action')
        neddActionIds = self._get_need_so_action_record(instanceId, needAction)
        return {
            'name': ('Record'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'domain': [('id', 'in', neddActionIds)],
            'target': 'current',
        }

    @api.model
    def _get_need_so_action_record(self, instanceId, needAction):
        recordMapObjs = self.env['wk.order.mapping'].search(
            [('instance_id', '=', instanceId)])
        saleOrderObjs = recordMapObjs.mapped('erp_order_id')
        idList = []
        for orderObj in saleOrderObjs.filtered(
                lambda obj: obj.state != 'cancel'):
            if needAction == 'delivery':
                if not orderObj.is_shipped:
                    idList.append(orderObj.id)
            if needAction == 'invoice':
                if not orderObj.is_invoiced:
                    idList.append(orderObj.id)

        return idList


    def _get_process_order_record(self, instanceId, doneAction):
        recordMapObjs = self.env['wk.order.mapping'].search(
            [('instance_id', '=', instanceId)])
        recList = []
        for orderObj in recordMapObjs:
            if doneAction == 'invoice' and orderObj.is_invoiced:
                recList.append(orderObj.erp_order_id.id)
            if doneAction == 'delivery' and orderObj.is_shipped:
                recList.append(orderObj.erp_order_id.id)
        return recList


    def get_action_prosess_records(self):
        self.ensure_one()
        instanceId = self.instance_id.id
        doneAction = self._context.get('action')
        doneActionIds = self._get_process_order_record(instanceId, doneAction)
        return {
            'name': ('Records'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'domain': [('id', 'in', doneActionIds)],
            'target': 'current',
        }


    def _compute_record_count(self):
        for singleRecord in self:
            instanceId = singleRecord.instance_id.id
            name = singleRecord.item_name
            needOne = fieldName[name][0]
            needTwo = fieldName[name][1]
            model = modelName[name][1]
            mappedModel = modelName[name][2]
            mappedfieldName = modelName[name][3]
            action = modelName[name][0]
            singleRecord.count_mapped_records = 0
            singleRecord.count_need_sync_product = 0
            singleRecord.count_no_sync_product = 0
            singleRecord.count_need_sync_category = 0
            singleRecord.count_no_sync_category = 0
            singleRecord.count_need_invoice = 0
            singleRecord.count_need_delivery = 0
            singleRecord.count_no_sync_attribute = 0
            singleRecord.count_invoiced_records = 0
            singleRecord.count_delivered_records = 0

            if action == 1:
                totalOne = self._get_need_sync_record(mappedModel, instanceId)
                totalTwo = self._get_no_sync_record(
                    model, mappedModel, mappedfieldName, instanceId)
                singleRecord[needOne] = totalOne
                singleRecord[needTwo] = totalTwo
            elif action == 2:
                singleRecord[needOne] = len(
                    self._get_need_so_action_record(
                        instanceId, 'invoice'))
                singleRecord[needTwo] = len(
                    self._get_need_so_action_record(
                        instanceId, 'delivery'))
                singleRecord.count_invoiced_records = len(
                    self._get_process_order_record(instanceId, 'invoice'))
                singleRecord.count_delivered_records = len(
                    self._get_process_order_record(instanceId, 'delivery'))

            elif mappedfieldName:
                singleRecord[needTwo] = self._get_no_sync_record(
                    model, mappedModel, mappedfieldName, instanceId)
            singleRecord.count_mapped_records = self._get_mapped_records(
                mappedModel, instanceId)

    @api.model
    def _get_mapped_records(self, mappedModel, instanceId):
        return len(self.env[mappedModel].search(
            [('instance_id', '=', instanceId)]))

    @api.model
    def _get_need_sync_record(self, mappedModel, instanceId):
        domain = [('need_sync', '=', "Yes"), ('instance_id', '=', instanceId)]
        needSyncObjs = self.env[mappedModel].search(domain)
        return len(needSyncObjs)

    @api.model
    def _get_no_sync_record(
            self,
            model,
            mappedModel,
            mappedfieldName,
            instanceId):
        if model == "product.template":
            domin = [('type', '!=', 'service')]
        else:
            domin = []
        allRecordIds = self.env[model].search(domin).ids
        allSyncedObjs = self.env[mappedModel].search(
            [('instance_id', '=', instanceId)])
        allSynedRecordIds = allSyncedObjs.mapped(mappedfieldName).ids
        return len(set(allRecordIds) - set(allSynedRecordIds))
