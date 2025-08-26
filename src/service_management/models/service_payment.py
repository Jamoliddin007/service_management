from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class ServicePayment(models.Model):
    _name = "service.payment"
    _description = "Buyurtma bo‘yicha qabul qilingan pullar"
    _order = "payment_date desc"
    _sql_constraints = [
        ("unique_payment_name", "unique(name)", "To‘lov raqami takrorlanmas bo‘lishi kerak."),
    ]

    name = fields.Char(string="To‘lov raqami", required=True)
    center_id = fields.Many2one(
        comodel_name="service.center",
        string="Servis markazi",
        compute="_compute_center",
        store=True
    )
    order_id = fields.Many2one(
        comodel_name="service.order",
        string="Buyurtma",
        required=True
    )
    customer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Mijoz",
        compute="_compute_customer",
        store=True
    )
    payment_date = fields.Date(string="To‘lov sanasi", required=True)
    amount = fields.Float(string="Summasi", required=True)
    note = fields.Text(string="Izoh")
    state = fields.Selection(
        [
            ("draft", "Qoralama"),
            ("confirmed", "Tasdiqlangan"),
            ("cancelled", "Bekor qilingan"),
        ],
        string="Holat",
        default="draft",
        required=True
    )
    method = fields.Selection(
        [
            ("cash", "Naqd"),
            ("card", "Karta"),
            ("bank", "Bank o‘tkazmasi"),
        ],
        string="To‘lov usuli",
        required=True
    )
    order_total = fields.Float(
        string="Buyurtma summasi",
        compute="_compute_order_totals",
        store=True
    )
    order_balance_due = fields.Float(
        string="Buyurtma bo‘yicha qoldiq",
        compute="_compute_order_totals",
        store=True
    )
    customer_total_payment = fields.Float(
        string="Mijozning jami to‘lovlari",
        compute="_compute_customer_total_payment",
        store=True
    )

    @api.depends("order_id")
    def _compute_center(self):
        for record in self:
            record.center_id = record.order_id.center_id if record.order_id else False

    @api.depends("order_id")
    def _compute_customer(self):
        for record in self:
            record.customer_id = record.order_id.customer_id if record.order_id else False

    @api.depends("order_id", "order_id.payment_ids.amount")
    def _compute_order_totals(self):
        for record in self:
            if record.order_id:
                order_total = record.order_id.total_amount
                paid_amount = sum(record.order_id.payment_ids.mapped("amount"))
                record.order_total = order_total
                record.order_balance_due = order_total - paid_amount
            else:
                record.order_total = 0.0
                record.order_balance_due = 0.0

    @api.depends("customer_id", "customer_id.payment_ids.amount")
    def _compute_customer_total_payment(self):
        for record in self:
            if record.customer_id:
                payments = self.search([
                    ("customer_id", "=", record.customer_id.id),
                    ("state", "=", "confirmed")
                ])
                record.customer_total_payment = sum(payments.mapped("amount"))
            else:
                record.customer_total_payment = 0.0

    def action_confirm(self):
        for record in self:
            record.state = "confirmed"

    def action_cancel(self):
        for record in self:
            record.state = "cancelled"

    def action_reset_draft(self):
        for record in self:
            record.state = "draft"

    @api.constrains("amount", "order_id")
    def _check_payment_limit(self):
        for record in self:
            if record.order_id:
                total_paid = sum(record.order_id.payment_ids.filtered(lambda p: p.id != record.id).mapped("amount"))
                if total_paid + record.amount > record.order_id.total_amount:
                    raise ValidationError("Umumiy to‘lov miqdori buyurtma summasidan oshmasligi kerak.")

    @api.constrains("payment_date")
    def _check_payment_date(self):
        for record in self:
            if record.payment_date and record.payment_date > date.today():
                raise ValidationError("To‘lov sanasi kelajakdagi sana bo‘lishi mumkin emas.")
