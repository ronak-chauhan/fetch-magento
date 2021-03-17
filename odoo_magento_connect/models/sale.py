#import json
import requests
import xml.etree.ElementTree as ET
#from odoo.http import request
from odoo import api, models, fields, _
#from odoo.exceptions import UserError


class ProductProductRakuten(models.Model):
    _inherit = "product.product"

    rsl_product_name = fields.Char(string="Rakuten Product Name")
    rsl_date = fields.Datetime(string="Posted Date", readonly=True)
    rsl_response = fields.Char(string="Rakuten Response", readonly=True)

    def create_post_to_rsl(self):
        IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
        cust_id = IrConfigPrmtr.get_param(
            'odoo_magento_connect.customer_id_3pl')
        cust_psw = IrConfigPrmtr.get_param(
            'odoo_magento_connect.customer_psw_3pl')
        for product in self:
            if not product.rsl_product_name:

                product_detail = """<Item><ItemID>{}</ItemID>
                                    <ShortDescription>{}</ShortDescription>
                                    <UnitPrice>{}</UnitPrice></Item>""".format(product.display_name,
                                                                               product.display_name,
                                                                               product.standard_price)

                order_payload = RSL_PRODUCT_PAYLOAD.strip().format(cust_id=cust_id,
                                                    cust_psw=cust_psw,
                                                    prd_payload=product_detail)

                rsl_response = posting_rml(product,url=RSLPRODUCT,
                                           payload=order_payload)
                myroot = ET.fromstring(rsl_response)
                error_msg = ""
                response_msg = False
                for main_tag in myroot:
                    if main_tag.tag == "Error":
                        error_msg += main_tag.text
                    for sub_tag in main_tag:
                        if sub_tag.tag == "Success":
                            if sub_tag.text == "True":
                                product.rsl_product_name = product.display_name
                                product.rsl_date = fields.Datetime.now()
                        if sub_tag.tag == "Message":
                            product.rsl_response = response_msg
                if error_msg:
                    product.rsl_response = error_msg
        return True


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_magento_order = fields.Boolean(compute='_compute_do_create_by_magento',
                                      string='Field DO')
    shipment_name = fields.Char("RSL Order Name")
    shipment_status = fields.Char("RSL Order Status")
    rsl_error = fields.Char("RSL Error")
    is_rsl_enable = fields.Boolean("Is RSL Enable?",
                                     compute="_rs_auto_mode")

    @api.depends("shipment_name")
    def _rs_auto_mode(self):
        IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
        isAutoMode = IrConfigPrmtr.get_param('odoo_magento_connect.is_enable_rsl')
        if isAutoMode and isAutoMode == "True":
            isAutoMode = True
        else:
            isAutoMode = False
        for rec in self:
            rec.is_rsl_enable = isAutoMode

    #Approved, Not Approved, Shipped, BackOrder, Not Yet Determined

    def _get_ecommerces(self):
        res = super(SaleOrder, self)._get_ecommerces()
        res.append(('magento', 'Magento'))
        return res

    def action_cancel(self):
        ctx = dict(self._context or {})
        res = super(SaleOrder, self).action_cancel()
        enableOrderCancel = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_magento_connect.mob_sale_order_cancel'
        )
        if not enableOrderCancel or 'magento' in ctx:
            return res
        for saleObj in self:
            if saleObj.ecommerce_channel == "magento" and enableOrderCancel:
                saleObj.manual_magento_order_operation("cancel")
        return res

    @api.model
    def manual_magento_order_operation(self, opr):
        text = ''
        status = 'no'
        session = False
        mageShipment = False
        ctx = dict(self._context or {})
        OrderMapObj = self.env['wk.order.mapping'].search(
            [('erp_order_id', '=', self.id)], limit=1)
        if OrderMapObj:
            incrementId = OrderMapObj.name
            orderName = self.name
            connectionObj = OrderMapObj.instance_id
            ctx['instance_id'] = connectionObj.id
            if connectionObj.active:
                if connectionObj.state != 'enable':
                    return False
                else:
                    connection = self.env[
                        'magento.configure'].with_context(ctx)._create_connection()
                    if connection:
                        url = connection[0]
                        token = connection[1]
                        apiOpr = ''
                        if token and incrementId:
                            if opr == "shipment":
                                apiOpr = 'OrderShipment'
                            elif opr == "cancel":
                                apiOpr = 'OrderCancel'
                            elif opr == "invoice":
                                apiOpr = 'OrderInvoice'
                        if apiOpr:
                            OrderData = {'orderId': incrementId}
                            itemData = self._context.get('itemData', {})
                            if connectionObj.notify:
                                itemData.update({'send_email': True})
                            if itemData :
                                OrderData.update(itemData=itemData)
                            apiResponse = self.env['magento.synchronization'].with_context(ctx).callMagentoApi(
                                baseUrl=url,
                                url='/V1/odoomagentoconnect/' + apiOpr,
                                method='post',
                                token=token,
                                data=OrderData
                            )
                            if apiResponse:
                                if apiOpr == "OrderShipment":
                                    mageShipment = apiResponse
                                text = '%s of order %s has been successfully updated on magento.' % (opr, orderName)
                                status = 'yes'
                            else:
                                text = 'Magento %s Error For Order %s , Error' % (opr, orderName)
                                status = 'no'
                    else:
                        text = 'Magento %s Error For Order %s >> Could not able to connect Magento.' % (opr, orderName)
                self._cr.commit()
                self.env['magento.sync.history'].create(
                    {'status': status, 'action_on': 'order', 'action': 'b', 'error_message': text})
        return mageShipment

    def _compute_do_create_by_magento(self):
        '''This method is used to check is magento order or not. when is magento order
        then its return true.'''

        for rec in self:
            magento_order_id = self.env['wk.order.mapping'].search([('erp_order_id', '=', rec.id)])
            if rec.company_id.mob_delivery and magento_order_id:
                rec.is_magento_order = True
            else:
                rec.is_magento_order = False

    def action_confirm(self):
        context = dict(self._context or {})
        rtn = super(SaleOrder, self).action_confirm()
        for record in self:
            if record.picking_ids:
                pick = record.picking_ids.sorted(lambda lm: lm.id)[0]
                pick.action_sync_shipment_to_magento()
            IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
            is3plenable = IrConfigPrmtr.get_param('odoo_magento_connect.is_enable_rsl')
            isAutoEnable = IrConfigPrmtr.get_param('odoo_magento_connect.auto_create_mode_3pl')
            if is3plenable != 'True' or isAutoEnable != 'True':
                return rtn
            cust_id = IrConfigPrmtr.get_param(
                'odoo_magento_connect.customer_id_3pl')
            cust_psw = IrConfigPrmtr.get_param(
                'odoo_magento_connect.customer_psw_3pl')
            record.postToRSL(cust_id=cust_id, cust_psw=cust_psw)
        return rtn

    def autoCronPostingToRsl(self):
        IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
        is3plenable = IrConfigPrmtr.get_param('odoo_magento_connect.is_enable_rsl')
        if is3plenable != 'True':
            for order in self.search([('is_rsl_enable','=',True), ('shipment_status','!=','Shipped'),
                                      ('shipment_name','!=',False)], order='date_order', limit=100):
                order.getStatusFromRSL()

    def postToRSL(self, cust_id='', cust_psw=''):
        for record in self:
            IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
            cust_id = cust_id or IrConfigPrmtr.get_param(
                'odoo_magento_connect.customer_id_3pl')
            cust_psw = cust_psw or IrConfigPrmtr.get_param(
                'odoo_magento_connect.customer_psw_3pl')
            name = record.partner_shipping_id.name
            ref = record.name
            cmp = record.company_id.name
            add = record.partner_shipping_id.street or ''
            add1 = record.partner_shipping_id.street2 or ''
            add2 = ''
            city = record.partner_shipping_id.city or ''
            state = record.partner_shipping_id.state_id and record.partner_shipping_id.state_id.code or ''
            zip = record.partner_shipping_id.zip or ''
            country = record.partner_shipping_id.country_id and record.partner_shipping_id.country_id.name or ''
            email = record.partner_shipping_id.email or ''
            phone = record.partner_shipping_id.phone or ''
            mobile = record.partner_shipping_id.mobile or ''
            phone = phone + ' '+ mobile
            instruction = record.note or 'Ground'
            comment = record.note or ''
            subtotal = record.amount_untaxed or 0
            total = record.amount_total or 0
            tax = record.amount_tax or 0
            order_payload = RSL_ORDER_CREATE

            order_lines = ""
            for line in record.order_line:
                order_lines += """<Item>
                    <ItemID>{name}</ItemID>
                    <ItemQty>{qty}</ItemQty>
                    <UnitPrice>{amt}</UnitPrice>
                </Item>""".format(name=line.product_id.rsl_product_name or line.name, qty=line.product_uom_qty,
                                  amt=line.price_unit)
            order_payload = order_payload.strip().format(cust_id=cust_id,
                                               cust_psw=cust_psw,
                                 ref=ref, cmp=cmp, name=name, add=add,
                                 add1=add1,add2=add2,city=city, state=state,
                                 zip=zip,country=country, email=email,
                                 phone=phone,instruction=instruction,
                                 comment=comment, subtotal=subtotal,
                                 tax=tax, total=total,itemline=order_lines)
            rsl_response = posting_rml(record,url=RSLPOSTORDER,
                                       payload=order_payload)

            myroot = ET.fromstring(rsl_response)
            error_msg = ""
            final_order = False
            for x in myroot:
                if x.tag == "Error":
                    error_msg += x.text
                if x.tag == "Success":
                    final_order = x.text
                    record.shipment_name = x.text
                if x.tag == "OrderID" and final_order == "True":
                    record.shipment_name = x.text
            if error_msg:
                record.rsl_error = error_msg
            else:
                record.rsl_error = None
                picking = record.picking_ids.filtered(lambda lm :lm.picking_type_id.code == "outgoing")
                picking.carrier_tracking_ref = record.shipment_name
                # raise UserError(_("Error {}".format(error_msg)))

    def getStatusFromRSL(self):
        IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
        is3plenable = IrConfigPrmtr.get_param('odoo_magento_connect.is_enable_rsl')
        # if is3plenable != 'True':
        #     return True
        cust_id = IrConfigPrmtr.get_param(
            'odoo_magento_connect.customer_id_3pl')
        cust_psw = IrConfigPrmtr.get_param(
            'odoo_magento_connect.customer_psw_3pl')
        for record in self:
            if not record.shipment_name:
                continue

            order_payload = RSL_ORDER_STATUS.strip().format(cust_id=cust_id,
                                                    cust_psw=cust_psw,
                                                    order=record.name)

            rsl_response = posting_rml(record,url=RSLGETORDERDETAIL,
                                       payload=order_payload)
            myroot = ET.fromstring(rsl_response)
            error_msg = ""
            is_shipped = False
            for x in myroot:
                if x.tag == "OrderDetails":
                    for order in x:
                        if order.tag=="Status" and order.text:
                            record.shipment_status = order.text
                            if order.text == "Shipped":
                                is_shipped = True
                        elif order.tag == "Error":
                            error_msg += order.text

            if error_msg:
                record.rsl_error = error_msg
                #raise UserError(_("Error {}".format(error_msg)))
            else:
                record.rsl_error = None
                if is_shipped:
                    picking = record.picking_ids.filtered(lambda lm :lm.picking_type_id.code == "outgoing")
                    for pick in picking:
                        if pick.state in ("waiting", "confirmed"):
                            pick.action_assign()
                            for line in pick.move_line_ids_without_package:
                                if line.product_uom_qty > line.qty_done:
                                    line.qty_done = line.product_uom_qty

                        if pick.state == "assigned":
                            for line in pick.move_line_ids_without_package:
                                if line.product_uom_qty > line.qty_done and line.state not in ("done", "cancel"):
                                    line.qty_done = line.product_uom_qty
                            pick.button_validate()

                # picking = record.picking_ids.filtered(lambda lm :lm.picking_type_id.code == "outgoing")
                # print("Picking... ",picking)
                # picking.carrier_tracking_ref = record.shipment_name


RSL_ORDER_CREATE = """<?xml version="1.0" encoding="UTF-8"?>
<OrderXML>
<CustomerID>{cust_id}</CustomerID>
<Password>{cust_psw}</Password>
<Order>
    <ReferenceNumber>{ref}</ReferenceNumber>
    <Company>{cmp}</Company>
    <Name>{name}</Name >
    <Address1>{add}</Address1>
    <Address2>{add1}</Address2>
    <Address3>{add2}</Address3>
    <City>{city}</City>
    <State>{state}</State>
    <ZipCode>{zip}</ZipCode>
    <Country>{country}</Country>
    <Email>{email}</Email>
    <Phone>{phone}</Phone>
    <ShippingInstructions>{instruction}</ShippingInstructions>
    <OrderComments>{comment}</OrderComments>
    <OrderType>0</OrderType>
    <SubTotal>{subtotal}</SubTotal>
    <Tax>{tax}</Tax>
    <Shipping>0</Shipping>
    <Total>{total}</Total>
    <Approve>0</Approve>
    {itemline}
</Order> </OrderXML>"""

RSL_ORDER_STATUS = """<?xml version="1.0" encoding="UTF-8"?>
<OrderDetailsXML><CustomerID>{cust_id}</CustomerID><Password>{cust_psw}</Password>
<OrderDetails><Order>{order}</Order></OrderDetails></OrderDetailsXML>"""

RSL_ORDER_TRACKING = """<?xml version="1.0" encoding="UTF-8"?>
<TrackingXML>
<CustomerID>{cust_id}</CustomerID>
<Password>{cust_psw}</Password>
<Tracking>
<Order>{order}</Order>
</Tracking>
</TrackingXML>"""

RSL_PRODUCT_PAYLOAD = """
<?xml version="1.0" encoding="UTF-8"?>
<ItemXML>
<CustomerID>{cust_id}</CustomerID>
<Password>{cust_psw}</Password>
{prd_payload}
</ItemXML>"""

RSLPOSTORDER = "http://www.webgistix.com/XML/CreateOrder.asp"
RSLGETORDERDETAIL = "http://www.webgistix.com/XML/getOrderDetails.asp"
RSLPRODUCT = "http://www.webgistix.com/XML/CreateItems.asp"
# RSLORDERTRACK = "http://www.webgistix.com/XML/GetTracking.asp"
DEFAULTHEADERS = {'Content-Type': 'text/xml; charset=utf-8'}


def posting_rml(self, url, headers=DEFAULTHEADERS, payload=''):
    response = requests.request("POST", url, headers=headers, data = payload)
    return response.text.encode('utf8')

#Approved, Not Approved, Shipped, BackOrder, Not Yet Determined