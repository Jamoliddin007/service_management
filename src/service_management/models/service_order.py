from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ServiceOrder(models.Model):
    _name = "service.order"
    _description = "Buyurtmalar"
    _order = "order_date desc, id desc"

    name = fields.Char(string="Buyurtma raqami", required=True, copy=False, readonly=True, default="New")
    center_id = fields.Many2one("service.center", string="Servis markazi", required=True, ondelete="restrict")
    customer_id = fields.Many2one("res.partner", string="Mijoz", required=True, ondelete="restrict")
    technician_id = fields.Many2one("service.technician", string="Usta", ondelete="set null")
    order_date = fields.Date(string="Buyurtma sanasi", default=fields.Date.context_today, required=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("received", "Received"),
            ("diagnosed", "Diagnosed"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Holat",
        default="draft",
        required=True
    )

    description = fields.Text(string="Izoh/Muammo")
    line_ids = fields.One2many("service.order.line", "order_id", string="Buyurtma qatorlari")
    labor_fee = fields.Float(string="Ish haqi (xizmat narxi)", default=0.0)
    discount_amount = fields.Float(string="Chegirma", default=0.0)
    payment_ids = fields.One2many("service.payment", "order_id", string="To‘lovlar")

    payment_total = fields.Float(string="Jami to‘lov", compute="_compute_payments", store=True)
    balance_due = fields.Float(string="Qarz (qoldiq)", compute="_compute_payments", store=True)
    last_payment_date = fields.Date(string="Oxirgi to‘lov sanasi", compute="_compute_payments", store=True)

    rating_ids = fields.One2many("service.rating", "order_id", string="Baholashlar")
    total_amount = fields.Float(string="Umumiy summa", compute="_compute_total_amount", store=True)

    is_warranty = fields.Boolean(string="Kafolat mavjud")
    warranty_days = fields.Integer(string="Kafolat (kun)")

    @api.constrains("is_warranty", "warranty_days")
    def _check_warranty_days(self):
        for rec in self:
            if rec.is_warranty and rec.warranty_days <= 0:
                raise ValidationError("Kafolat mavjud bo'lsa, kun miqdori musbat bo'lishi kerak.")

    @api.depends("payment_ids.amount")
    def _compute_payments(self):
        for rec in self:
            total = sum(rec.payment_ids.mapped("amount"))
            rec.payment_total = total
            rec.balance_due = rec.total_amount - total
            rec.last_payment_date = (
                max(rec.payment_ids.mapped("payment_date")) if rec.payment_ids else False
            )

    @api.depends("line_ids.subtotal", "labor_fee", "discount_amount")
    def _compute_total_amount(self):
        for rec in self:
            subtotal = sum(rec.line_ids.mapped("subtotal"))
            rec.total_amount = subtotal + rec.labor_fee - rec.discount_amount

    def action_receive(self):
        self.write({"state": "received"})

    def action_diagnose(self):
        self.write({"state": "diagnosed"})

    def action_start_progress(self):
        self.write({"state": "in_progress"})

    def action_finish(self):
        for rec in self:
            if rec.balance_due > 0:
                raise ValidationError("Buyurtmani yakunlash uchun barcha qarzlar yopilishi kerak.")
            rec.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_cleanup_zero_payments(self):
        for rec in self:
            zero_payments = rec.payment_ids.filtered(lambda p: p.amount == 0)
            zero_payments.unlink()

    def action_close_if_paid(self):
        for rec in self:
            if rec.balance_due <= 0:
                rec.write({"state": "done"})
            else:
                raise ValidationError("Qarz to'liq yopilmagani uchun buyurtmani yopib bo‘lmaydi.")
