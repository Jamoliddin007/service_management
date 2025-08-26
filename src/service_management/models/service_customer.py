from odoo import models, fields, api
from datetime import date


class ServiceCustomer(models.Model):
    _name = "service.customer"
    _description = "Service Customer"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(string="Mijoz F.I.O / Tashkilot nomi", required=True)
    code = fields.Char(string="Mijoz kodi")
    phone = fields.Char(string="Telefon")
    mobile = fields.Char(string="Qo‘shimcha telefon")
    email = fields.Char(string="Elektron pochta")
    address = fields.Char(string="Manzil")

    center_ids = fields.Many2many(
        "service.center",
        string="Servis markazlari",
        compute="_compute_center_ids",
        store=False,
    )

    order_ids = fields.One2many("service.order", "customer_id", string="Buyurtmalar")
    payment_ids = fields.One2many("service.payment", "customer_id", string="To‘lovlar")
    rating_ids = fields.One2many("service.rating", "customer_id", string="Baholar")

    order_count = fields.Integer(string="Buyurtmalar soni", compute="_compute_order_stats")
    active_order_ids = fields.One2many(
        "service.order",
        compute="_compute_order_stats",
        string="Faol buyurtmalar",
        store=False,
    )
    active_order_count = fields.Integer(string="Faol buyurtmalar soni", compute="_compute_order_stats")

    done_order_ids = fields.One2many(
        "service.order",
        compute="_compute_order_stats",
        string="Yakunlangan buyurtmalar",
        store=False,
    )
    done_order_count = fields.Integer(string="Yakunlangan buyurtmalar soni", compute="_compute_order_stats")

    today_order_ids = fields.One2many(
        "service.order",
        compute="_compute_order_stats",
        string="Bugungi buyurtmalar",
        store=False,
    )
    today_order_count = fields.Integer(string="Bugungi buyurtmalar soni", compute="_compute_order_stats")

    total_payment = fields.Float(string="Jami to‘lov", compute="_compute_payment_stats")
    balance_due = fields.Float(string="Qarz (qoldiq)", compute="_compute_payment_stats")

    avg_rating = fields.Float(string="O‘rtacha baho", compute="_compute_avg_rating")
    last_order_date = fields.Date(string="Oxirgi buyurtma sanasi", compute="_compute_last_dates")
    last_payment_date = fields.Date(string="Oxirgi to‘lov sanasi", compute="_compute_last_dates")

    @api.depends("order_ids")
    def _compute_center_ids(self):
        for record in self:
            record.center_ids = record.order_ids.mapped("center_id")

    @api.depends("order_ids")
    def _compute_order_stats(self):
        today = date.today()
        for record in self:
            orders = record.order_ids
            record.order_count = len(orders)
            record.active_order_ids = orders.filtered(lambda o: o.state == "active")
            record.active_order_count = len(record.active_order_ids)
            record.done_order_ids = orders.filtered(lambda o: o.state == "done")
            record.done_order_count = len(record.done_order_ids)
            record.today_order_ids = orders.filtered(lambda o: o.order_date == today)
            record.today_order_count = len(record.today_order_ids)

    @api.depends("payment_ids.amount", "order_ids.total_price")
    def _compute_payment_stats(self):
        for record in self:
            total_paid = sum(record.payment_ids.mapped("amount"))
            total_due = sum(record.order_ids.mapped("total_price")) - total_paid
            record.total_payment = total_paid
            record.balance_due = total_due

    @api.depends("rating_ids.score")
    def _compute_avg_rating(self):
        for record in self:
            ratings = record.rating_ids.mapped("score")
            record.avg_rating = sum(ratings) / len(ratings) if ratings else 0.0

    @api.depends("order_ids", "payment_ids")
    def _compute_last_dates(self):
        for record in self:
            record.last_order_date = max(record.order_ids.mapped("order_date") or [False])
            record.last_payment_date = max(record.payment_ids.mapped("payment_date") or [False])

    def action_close_debt(self):
        for record in self:
            if record.balance_due > 0:
                self.env["service.payment"].create({
                    "customer_id": record.id,
                    "amount": record.balance_due,
                    "payment_date": date.today(),
                    "state": "confirmed",
                })

    def action_cleanup_zero_payments(self):
        for record in self:
            zero_payments = record.payment_ids.filtered(lambda p: p.amount == 0)
            zero_payments.unlink()

    def action_cleanup_cancelled_orders(self):
        for record in self:
            cancelled_orders = record.order_ids.filtered(lambda o: o.state == "cancelled")
            cancelled_orders.unlink()
