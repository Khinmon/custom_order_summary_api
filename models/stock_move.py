from odoo import models, api, fields, _

class StockMoveBus(models.Model):
    _inherit = "stock.move"

    def _os_notify(self, extra=None):
        extra = extra or {}
        picking_ids = list({p.id for p in self.mapped("picking_id") if p})
        if not picking_ids:
            return
        message = _("Stock move by %s." % (picking_ids))
        payload = {
            "event": "order_summary_changed",
            "picking_ids": picking_ids,
            "ts": fields.Datetime.now(),
            "message": message,
            "sticky": True,
            "notification_type": "warning"
        }
        self.env["bus.bus"]._sendone(
                        self.env.user.partner_id,
                        'simple_notification',
                        payload
                    )

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._os_notify({"op": "create"})
        return recs

    def write(self, vals):
        res = super().write(vals)
        self._os_notify({"op": "write", "vals": list(vals.keys())})
        return res


class StockMoveLineBus(models.Model):
    _inherit = "stock.move.line"

    def _os_notify(self, extra=None):
        extra = extra or {}
        picking_ids = list({m.picking_id.id for m in self.mapped("move_id") if m.picking_id})
        if not picking_ids:
            return
        message = _("Stock move line by %s." % (picking_ids))
        payload = {
            "event": "order_summary_changed",
            "picking_ids": picking_ids,
            "ts": fields.Datetime.now(),
            "message": message,
            "sticky": True,
            "notification_type": "warning"
        }
        self.env["bus.bus"]._sendone(
                        self.env.user.partner_id,
                        'simple_notification',
                        payload
                    )


    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._os_notify({"op": "create"})
        return recs

    def write(self, vals):
        res = super().write(vals)
        self._os_notify({"op": "write", "vals": list(vals.keys())})
        return res