from odoo import models, fields, api
from datetime import date


class ServiceDistrict(models.Model):
    _name = "service.district"
    _description = "District"
    _rec_name = "name"
    _order = "name"

    name = fields.Char(string="Tuman nomi", required=True)
    code = fields.Char(string="Tuman kodi", required=True)
    is_active = fields.Boolean(string="Faol", default=True)
    state_id = fields.Many2one(
        "service.state", string="Viloyat", ondelete="set null"
    )
    country_id = fields.Many2one(
        "service.country", string="Davlat", related="state_id.country_id", store=True
    )
    center_ids = fields.One2many(
        "service.center", "district_id", string="Servis markazlari"
    )
    population = fields.Integer(string="Aholi soni", default=0)
    area_km2 = fields.Float(string="Maydon (km²)", default=0.0)
    latitude = fields.Float(string="Kenglik")
    longitude = fields.Float(string="Uzunlik")
    technician_ids = fields.One2many(
        "service.technician", "district_id", string="Ustalar"
    )
    center_count = fields.Integer(
        string="Servis markazlari soni", compute="_compute_counts", store=True
    )
    technician_count = fields.Integer(
        string="Ustalar soni", compute="_compute_counts", store=True
    )
    active_order_ids = fields.One2many(
        "service.order", "district_id", string="Faol buyurtmalar",
        compute="_compute_orders", store=True
    )
    active_order_count = fields.Integer(
        string="Faol buyurtmalar soni", compute="_compute_orders", store=True
    )
    done_order_ids = fields.One2many(
        "service.order", "district_id", string="Yakunlangan buyurtmalar",
        compute="_compute_orders", store=True
    )
    done_order_count = fields.Integer(
        string="Yakunlangan buyurtmalar soni", compute="_compute_orders", store=True
    )
    today_order_ids = fields.One2many(
        "service.order", "district_id", string="Bugungi buyurtmalar",
        compute="_compute_orders", store=True
    )
    today_order_count = fields.Integer(
        string="Bugungi buyurtmalar soni", compute="_compute_orders", store=True
    )
    total_revenue = fields.Float(
        string="Jami tushum", compute="_compute_revenue", store=True
    )
    avg_rating = fields.Float(
        string="O‘rtacha baho", compute="_compute_avg_rating", store=True
    )
    last_order_date = fields.Date(
        string="Oxirgi buyurtma sanasi", compute="_compute_last_order_date", store=True
    )
    _sql_constraints = [
        ("unique_code", "unique(code)", "Tuman kodi takrorlanmas bo‘lishi kerak!"),
    ]

    @api.depends("center_ids", "technician_ids")
    def _compute_counts(self):
        for record in self:
            record.center_count = len(record.center_ids)
            record.technician_count = len(record.technician_ids)

    @api.depends("center_ids.order_ids.state", "center_ids.order_ids.order_date")
    def _compute_orders(self):
        today = date.today()
        for record in self:
            orders = self.env["service.order"].search([
                ("center_id.district_id", "=", record.id)
            ])
            record.active_order_ids = orders.filtered(lambda o: o.state not in ["done", "cancelled"])
            record.active_order_count = len(record.active_order_ids)
            record.done_order_ids = orders.filtered(lambda o: o.state == "done")
            record.done_order_count = len(record.done_order_ids)
            record.today_order_ids = orders.filtered(lambda o: o.order_date == today)
            record.today_order_count = len(record.today_order_ids)

    @api.depends("center_ids.order_ids.total_amount")
    def _compute_revenue(self):
        for record in self:
            orders = self.env["service.order"].search([
                ("center_id.district_id", "=", record.id),
                ("state", "=", "done")
            ])
            record.total_revenue = sum(orders.mapped("total_amount"))

    @api.depends("center_ids.order_ids.rating_ids.score")
    def _compute_avg_rating(self):
        for record in self:
            ratings = self.env["service.order.rating"].search([
                ("order_id.center_id.district_id", "=", record.id)
            ])
            record.avg_rating = sum(ratings.mapped("score")) / len(ratings) if ratings else 0.0

    @api.depends("center_ids.order_ids.order_date")
    def _compute_last_order_date(self):
        for record in self:
            orders = self.env["service.order"].search([
                ("center_id.district_id", "=", record.id)
            ], order="order_date desc", limit=1)
            record.last_order_date = orders.order_date if orders else False


    def action_deactivate(self):
        self.write({"is_active": False})

    def action_activate(self):
        self.write({"is_active": True})

    def action_deactivate_idle_centers(self):
        for record in self:
            idle_centers = record.center_ids.filtered(lambda c: not c.active_order_ids)
            idle_centers.write({"is_active": False})

    def action_cleanup_zero_payments(self):
        for record in self:
            payments = self.env["service.payment"].search([
                ("center_id.district_id", "=", record.id),
                ("amount", "=", 0)
            ])
            payments.unlink()

    def action_finish_all_in_progress(self):
        for record in self:
            orders = self.env["service.order"].search([
                ("center_id.district_id", "=", record.id),
                ("state", "=", "in_progress")
            ])
            orders.write({"state": "done"})
