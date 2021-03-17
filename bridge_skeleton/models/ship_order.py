import logging
from odoo import api, models
_logger = logging.getLogger(__name__)

class WkSkeleton(models.TransientModel):
    _inherit = "wk.skeleton"

    @api.model
    def set_order_shipped(self, orderId):
        """Ship the order in Odoo via requests from XML-RPC
        @param order_id: Odoo Order ID
        @param context: Mandatory Dictionary with key 'ecommerce' to identify the request from E-Commerce
        @return:  A dictionary of status and status message of transaction"""
        ctx = dict(self._context or {})
        status = True
        status_message = "Order Successfully Shipped."
        try:
            saleObj = self.env['sale.order'].browse(orderId)
            backOrderModel = self.env['stock.backorder.confirmation']
            if saleObj.state == 'draft':
                self.confirm_odoo_order([orderId])
            if saleObj.picking_ids:
                self.turn_odoo_connection_off()
                for pickingObj in saleObj.picking_ids.filtered(
                        lambda pickingObj: pickingObj.picking_type_code == 'outgoing' and pickingObj.state != 'done'):
                    backorder = False
                    ctx['active_id'] = pickingObj.id
                    ctx['picking_id'] = pickingObj.id
                    # pickingObj.force_assign()
                    is_validate_check = False
                    for ln in pickingObj.move_line_ids_without_package:
                        if ln.product_id and ln.product_id.tracking == "none":
                            if ln.product_uom_qty > ln.qty_done:
                                ln.qty_done = ln.product_uom_qty
                                is_validate_check = True
                    if is_validate_check:
                        try:
                            pickingObj.button_validate()
                        except Exception as e:
                            _logger.info("{} picking having something wrong "
                                         "while validating.".format(
                                pickingObj))
                    # for packObj in pickingObj.move_line_ids:
                    #     if packObj.qty_done and packObj.qty_done < packObj.product_qty:
                    #         backorder = True
                    #         continue
                    #     elif packObj.product_qty > 0:
                    #         packObj.write({'qty_done': packObj.product_qty})
                    #     else:
                    #         packObj.unlink()
                    # if backorder:
                    #     backorderObj = backOrderModel.create(
                    #         {'pick_ids': [(4, pickingObj.id)]})
                    #     backorderObj.process_cancel_backorder()
                    # else:
                    #     pickingObj.button_validate()
                    self.with_context(ctx).set_extra_values()
        except Exception as e:
            status = False
            status_message = "Error in Delivering Order: %s" % str(e)
        finally:
            self.turn_odoo_connection_on()
            _logger.info("This is response from set_order_shipped {"
                         "} {}".format(status_message, status))
            return {
                'status_message': status_message,
                'status': status
            }
