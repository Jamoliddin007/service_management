from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class ServiceState(models.Model):
    _name = "service.state"
    _description = "Viloyatlar"
    _order = "name"
    _sql_constraints = [
        ("name_unique", "unique(name)", "Viloyat nomi takrorlanmas bo‘lishi kerak."),
        ("code_unique", "unique(code)", "Viloyat kodi takrorlanmas bo‘lishi kerak."),
    ]

    name = fields.Char(string="Viloyat nomi", required=True)
    code = fields.Char(string="Viloyat kodi", required=True)
    is_active = fields.Boolean(string="Faol viloyat", default=True)

    country_id = fields.Many2one(
        "service.country",
        string="Davlat",
        required=True,
        ondelete="cascade",
    )

    district_ids = fields.One2many(
        "service.district", "state_id", string="Tumanlar"
    )

    center_ids = fields.One2many(
        "service.center", "state_id", string="Servis markazlari"
    )

    population = fields.Integer(string="Aholi soni")
    area_km2 = fields.Float(string="Maydon (km²)")
    latitude = fields.Float(string="Kenglik")
    longitude = fields.Float(string="Uzunlik")

    technician_ids = fields.One2many(
        "service.technician", "state_id", string="Ustalar"
    )

    district_count = fields.Integer(
        string="Tumanlar soni",
        compute="_compute_counts",
        store=True,
    )
    center_count = fields.Integer(
        string="Servis markazlari soni",
        compute="_compute_counts",
        store=True,
    )
    technician_count = fields.Integer(
        string="Ustalar soni",
        compute="_compute_counts",
        store=True,
    )

    active_order_ids = fields.One2many(
        "service.order", "state_id",
        string="Faol buyurtmalar",
        domain=[("state", "in", ["new", "in_progress"])]
    )
    active_order_count = fields.Integer(
        string="Faol buyurtmalar soni",
        compute="_compute_order_stats",
        store=True,
    )

    done_order_ids = fields.One2many(
        "service.order", "state_id",
        string="Yakunlangan buyurtmalar",
        domain=[("state", "=", "done")]
    )
    done_order_count = fields.Integer(
        string="Yakunlangan buyurtmalar soni",
        compute="_compute_order_stats",
        store=True,
    )

    today_order_ids = fields.One2many(
        "service.order", "state_id",
        string="Bugungi buyurtmalar",
        domain=[("order_date", "=", fields.Date.today())]
    )
    today_order_count = fields.Integer(
        string="Bugungi buyurtmalar soni",
        compute="_compute_order_stats",
        store=True,
    )

    total_revenue = fields.Float(
        string="Jami tushum",
        compute="_compute_revenue_rating",
        store=True,
    )
    avg_rating = fields.Float(
        string="O‘rtacha baho",
        compute="_compute_revenue_rating",
        store=True,
    )
    last_order_date = fields.Date(
        string="Oxirgi buyurtma sanasi",
        compute="_compute_revenue_rating",
        store=True,
    )

    # --- Constraints ---
    @api.constrains("population", "area_km2")
    def _check_positive_values(self):
        for record in self:
            if record.population and record.population < 0:
                raise ValidationError("Aholi soni musbat bo‘lishi kerak.")
            if record.area_km2 and record.area_km2 <= 0:
                raise ValidationError("Maydon musbat qiymat bo‘lishi kerak.")

    # --- Compute methods ---
    @api.depends("district_ids", "center_ids", "technician_ids")
    def _compute_counts(self):
        for record in self:
            record.district_count = len(record.district_ids)
            record.center_count = len(record.center_ids)
            record.technician_count = len(record.technician_ids)

    @api.depends("active_order_ids", "done_order_ids", "today_order_ids")
    def _compute_order_stats(self):
        for record in self:
            record.active_order_count = len(record.active_order_ids)
            record.done_order_count = len(record.done_order_ids)
            record.today_order_count = len(record.today_order_ids)

    @api.depends("done_order_ids")
    def _compute_revenue_rating(self):
        for record in self:
            done_orders = record.done_order_ids
            record.total_revenue = sum(done_orders.mapped("amount_total"))
            ratings = done_orders.mapped("rating")
            record.avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
            record.last_order_date = max(done_orders.mapped("order_date")) if done_orders else False

    def action_deactivate(self):
        for record in self:
            record.is_active = False

    def action_activate(self):
        for record in self:
            record.is_active = True

    def action_deactivate_idle_centers(self):
        for record in self:
            idle_centers = record.center_ids.filtered(lambda c: not c.active_order_ids)
            idle_centers.write({"is_active": False})

    def action_cleanup_zero_payments(self):
        Payment = self.env["service.payment"]
        for record in self:
            zero_payments = Payment.search([
                ("center_id", "in", record.center_ids.ids),
                ("amount", "=", 0.0),
            ])
            zero_payments.unlink()

    def action_finish_all_in_progress(self):
        for record in self:
            in_progress_orders = record.center_ids.mapped("order_ids").filtered(
                lambda o: o.state == "in_progress"
            )
            in_progress_orders.write({"state": "done"})
