from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class ServiceCenter(models.Model):
    _name = "service.center"
    _description = "Service Center"
    _order = "name"
    _sql_constraints = [
        ("name_uniq", "unique(name)", "Servis markazi nomi takrorlanmasligi kerak."),
        ("code_uniq", "unique(code)", "Markaz kodi takrorlanmasligi kerak."),
    ]

    # --- Basic Info ---
    name = fields.Char(string="Servis markazi nomi", required=True)
    code = fields.Char(string="Markaz kodi", required=True)
    is_active = fields.Boolean(string="Faol markaz", default=True)

    country_id = fields.Many2one("record.country", string="Davlat", ondelete="set null")
    state_id = fields.Many2one("record.country.state", string="Viloyat", ondelete="set null")
    district_id = fields.Many2one("record.city", string="Tuman", ondelete="set null")
    address = fields.Char(string="Manzil")
    latitude = fields.Float(string="Kenglik (Latitude)")
    longitude = fields.Float(string="Uzunlik (Longitude)")
    phone = fields.Char(string="Telefon")
    email = fields.Char(string="Elektron pochta")
    manager_name = fields.Char(string="Mas'ul shaxs")
    capacity_per_day = fields.Integer(string="Kunlik quvvat (buyurtma)", default=0)
    order_ids = fields.One2many("service.order", "center_id", string="Buyurtmalar")
    payment_ids = fields.One2many("service.payment", "center_id", string="To'lovlar")
    rating_ids = fields.One2many("service.rating", "center_id", string="Baholar")
    technician_ids = fields.One2many("service.technician", "center_id", string="Ustalar")

    technician_count = fields.Integer(string="Ustalar soni", compute="_compute_technician_count", store=True)
    active_order_ids = fields.One2many(
        "service.order", "center_id",
        string="Faol buyurtmalar",
        domain=[("state", "=", "in_progress")]
    )
    active_order_count = fields.Integer(string="Faol buyurtmalar soni", compute="_compute_order_counts", store=True)
    done_order_ids = fields.One2many(
        "service.order", "center_id",
        string="Yakunlangan buyurtmalar",
        domain=[("state", "=", "done")]
    )
    done_order_count = fields.Integer(string="Yakunlangan buyurtmalar soni", compute="_compute_order_counts", store=True)
    today_order_ids = fields.One2many(
        "service.order", "center_id",
        string="Bugungi buyurtmalar",
        domain=[("order_date", "=", fields.Date.today())]
    )
    today_order_count = fields.Integer(string="Bugungi buyurtmalar soni", compute="_compute_order_counts", store=True)
    total_revenue = fields.Float(string="Jami tushum", compute="_compute_total_revenue", store=True)
    avg_rating = fields.Float(string="O'rtacha baho", compute="_compute_avg_rating", store=True)
    utilization_rate = fields.Float(string="Bandlik foizi (%)", compute="_compute_utilization_rate", store=True)
    last_order_date = fields.Date(string="Oxirgi buyurtma sanasi", compute="_compute_last_order_date", store=True)

    # --- Compute methods ---
    @api.depends("technician_ids")
    def _compute_technician_count(self):
        for record in self:
            record.technician_count = len(record.technician_ids)

    @api.depends("order_ids")
    def _compute_order_counts(self):
        today = date.today()
        for record in self:
            record.active_order_count = len(record.order_ids.filtered(lambda o: o.state == "in_progress"))
            record.done_order_count = len(record.order_ids.filtered(lambda o: o.state == "done"))
            record.today_order_count = len(record.order_ids.filtered(lambda o: o.order_date == today))

    @api.depends("payment_ids.amount")
    def _compute_total_revenue(self):
        for record in self:
            record.total_revenue = sum(p.amount for p in record.payment_ids)

    @api.depends("rating_ids.score")
    def _compute_avg_rating(self):
        for record in self:
            if record.rating_ids:
                record.avg_rating = sum(r.score for r in record.rating_ids) / len(record.rating_ids)
            else:
                record.avg_rating = 0.0

    @api.depends("active_order_count", "capacity_per_day")
    def _compute_utilization_rate(self):
        for record in self:
            if record.capacity_per_day > 0:
                record.utilization_rate = (record.active_order_count / record.capacity_per_day) * 100
            else:
                record.utilization_rate = 0.0

    @api.depends("order_ids.order_date")
    def _compute_last_order_date(self):
        for record in self:
            dates = record.order_ids.mapped("order_date")
            record.last_order_date = max(dates) if dates else False

    def action_mark_inactive_if_idle(self):
        for record in self:
            if record.active_order_count == 0:
                record.is_active = False

    def action_activate(self):
        for record in self:
            record.is_active = True

    def action_cleanup_zero_payments(self):
        for record in self:
            record.payment_ids.filtered(lambda p: p.amount == 0).unlink()

    def action_finish_all_in_progress(self):
        for record in self:
            in_progress_orders = record.order_ids.filtered(lambda o: o.state == "in_progress")
            in_progress_orders.write({"state": "done"})
