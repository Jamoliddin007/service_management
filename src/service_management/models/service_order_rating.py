from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class ServiceOrderRating(models.Model):
    _name = "service.order.rating"
    _description = "Buyurtma sifatini baholash"
    _order = "rating_date desc"
    _sql_constraints = [
        ("unique_order_rating", "unique(order_id)", "Bu buyurtma allaqachon baholangan."),
    ]

    center_id = fields.Many2one(
        comodel_name="service.center",
        string="Servis markazi",
        compute="_compute_center_and_technician",
        store=True,
    )
    order_id = fields.Many2one(
        comodel_name="service.order",
        string="Buyurtma",
        required=True,
    )
    customer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Mijoz",
        related="order_id.customer_id",
        store=True,
        readonly=True,
    )
    technician_id = fields.Many2one(
        comodel_name="res.partner",
        string="Usta",
        compute="_compute_center_and_technician",
        store=True,
    )
    score = fields.Integer(
        string="Baholash balli",
        required=True,
    )
    comment = fields.Text(string="Izoh (Fikr-mulohaza)")
    rating_date = fields.Date(
        string="Baholash sanasi",
        default=date.today,
    )

    @api.depends("order_id")
    def _compute_center_and_technician(self):
        for record in self:
            record.center_id = record.order_id.center_id.id if record.order_id else False
            record.technician_id = (
                record.order_id.technician_id.id if record.order_id else False
            )

    @api.constrains("score")
    def _check_score_range(self):
        for record in self:
            if record.score < 1 or record.score > 5:
                raise ValidationError("Baholash balli 1 dan 5 gacha bo‘lishi kerak.")
