from odoo import models, fields, api
from datetime import date

class ServiceCountry(models.Model):
    _name = "service.country"
    _description = "Davlatlar"
    _order = "name"
    _sql_constraints = [
        ("country_name_uniq", "unique(name)", "Davlat nomi takrorlanmasligi kerak."),
        ("country_code_uniq", "unique(code)", "Davlat kodi takrorlanmasligi kerak."),
        ("phone_code_uniq", "unique(phone_code)", "Telefon kodi takrorlanmasligi kerak.")
    ]

    name = fields.Char(string="Davlat nomi", required=True)
    code = fields.Char(string="Davlat kodi (ISO)", required=True)
    phone_code = fields.Char(string="Telefon kodi")
    is_active = fields.Boolean(string="Faol davlat", default=True)
    state_ids = fields.One2many("service.state", "country_id", string="Viloyatlar")
    district_ids = fields.One2many("service.district", "country_id", string="Tumanlar")
    center_ids = fields.One2many("service.center", "country_id", string="Servis markazlari")
    technician_ids = fields.One2many("service.technician", "country_id", string="Ustalar")
    technician_count = fields.Integer(string="Ustalar soni", compute="_compute_counts", store=True)
    state_count = fields.Integer(string="Viloyatlar soni", compute="_compute_counts", store=True)
    center_count = fields.Integer(string="Servis markazlari soni", compute="_compute_counts", store=True)
    active_order_ids = fields.One2many("service.order", "country_id", string="Faol buyurtmalar", compute="_compute_orders", store=False)
    active_order_count = fields.Integer(string="Faol buyurtmalar soni", compute="_compute_orders", store=False)
    done_order_ids = fields.One2many("service.order", "country_id", string="Yakunlangan buyurtmalar", compute="_compute_orders", store=False)
    done_order_count = fields.Integer(string="Yakunlangan buyurtmalar soni", compute="_compute_orders", store=False)
    today_order_ids = fields.One2many("service.order", "country_id", string="Bugungi buyurtmalar", compute="_compute_orders", store=False)
    today_order_count = fields.Integer(string="Bugungi buyurtmalar soni", compute="_compute_orders", store=False)
    total_revenue = fields.Float(string="Jami tushum", compute="_compute_financials", store=False)
    avg_rating = fields.Float(string="O‘rtacha baho", compute="_compute_financials", store=False)
    last_order_date = fields.Date(string="Oxirgi buyurtma sanasi", compute="_compute_financials", store=False)

    @api.depends("technician_ids", "state_ids", "center_ids")
    def _compute_counts(self):
        for record in self:
            record.technician_count = len(record.technician_ids)
            record.state_count = len(record.state_ids)
            record.center_count = len(record.center_ids)

    def _compute_orders(self):
        Order = self.env["service.order"]
        today = date.today()
        for record in self:
            orders = Order.search([("country_id", "=", record.id)])
            record.active_order_ids = orders.filtered(lambda o: o.state in ["draft", "in_progress"])
            record.active_order_count = len(record.active_order_ids)

            record.done_order_ids = orders.filtered(lambda o: o.state == "done")
            record.done_order_count = len(record.done_order_ids)

            record.today_order_ids = orders.filtered(lambda o: o.create_date.date() == today)
            record.today_order_count = len(record.today_order_ids)

    def _compute_financials(self):
        for record in self:
            all_orders = record.center_ids.order_ids
            record.total_revenue = sum(all_orders.mapped("total_amount"))
            record.avg_rating = sum(all_orders.mapped("rating")) / len(all_orders) if all_orders else 0
            record.last_order_date = max(all_orders.mapped("create_date")).date() if all_orders else False

    def action_deactivate(self):
        for record in self:
            record.is_active = False

    def action_activate(self):
        for record in self:
            record.is_active = True

    def action_deactivate_idle_centers(self):
        for record in self:
            idle_centers = record.center_ids.filtered(lambda c: not c.order_ids)
            idle_centers.write({"is_active": False})

    def action_cleanup_zero_payments(self):
        Payment = self.env["service.payment"]
        for record in self:
            zero_payments = Payment.search([
                ("center_id", "in", record.center_ids.ids),
                ("amount", "=", 0)
            ])
            zero_payments.unlink()

    def action_finish_all_in_progress(self):
        for record in self:
            in_progress_orders = record.center_ids.mapped("order_ids").filtered(lambda o: o.state == "in_progress")
            in_progress_orders.write({"state": "done"})
