from odoo import models, fields, api
from datetime import date


class ServiceTechnician(models.Model):
    _name = "service.technician"
    _description = "Ustalar"
    _order = "name"

    name = fields.Char(string="Usta F.I.O", required=True)
    code = fields.Char(string="Usta kodi", required=True)
    is_active = fields.Boolean(string="Faol usta", default=True)
    center_id = fields.Many2one(
        comodel_name="service.center",
        string="Servis markazi",
        ondelete="set null"
    )
    phone = fields.Char(string="Telefon")
    email = fields.Char(string="Elektron pochta")
    specialty = fields.Text(string="Mutaxassislik tavsifi")
    hire_date = fields.Date(string="Ishga kirgan sana")
    capacity_per_day = fields.Integer(string="Kunlik quvvat (buyurtma)", default=1)

    order_ids = fields.One2many(
        comodel_name="service.order",
        inverse_name="technician_id",
        string="Biriktirilgan buyurtmalar"
    )

    order_count = fields.Integer(
        string="Biriktirilgan buyurtmalar soni",
        compute="_compute_order_counts",
        store=True
    )
    active_order_ids = fields.One2many(
        comodel_name="service.order",
        inverse_name="technician_id",
        string="Faol buyurtmalar",
        compute="_compute_order_lists",
    )
    active_order_count = fields.Integer(
        string="Faol buyurtmalar soni",
        compute="_compute_order_counts",
        store=True
    )
    done_order_ids = fields.One2many(
        comodel_name="service.order",
        inverse_name="technician_id",
        string="Yakunlangan buyurtmalar",
        compute="_compute_order_lists",
    )
    done_order_count = fields.Integer(
        string="Yakunlangan buyurtmalar soni",
        compute="_compute_order_counts",
        store=True
    )
    today_order_ids = fields.One2many(
        comodel_name="service.order",
        inverse_name="technician_id",
        string="Bugungi buyurtmalar",
        compute="_compute_order_lists",
    )
    today_order_count = fields.Integer(
        string="Bugungi buyurtmalar soni",
        compute="_compute_order_counts",
        store=True
    )


    def action_deactivate(self):
        for rec in self:
            rec.is_active = False

    def action_activate(self):
        for rec in self:
            rec.is_active = True

    @api.depends("order_ids", "order_ids.state")
    def _compute_order_counts(self):
        today = date.today()
        for rec in self:
            rec.order_count = len(rec.order_ids)
            rec.active_order_count = len(
                rec.order_ids.filtered(lambda o: o.state not in ["done", "cancel"])
            )
            rec.done_order_count = len(
                rec.order_ids.filtered(lambda o: o.state == "done")
            )
            rec.today_order_count = len(
                rec.order_ids.filtered(lambda o: o.order_date == today)
            )

    def _compute_order_lists(self):
        today = date.today()
        for rec in self:
            rec.active_order_ids = rec.order_ids.filtered(
                lambda o: o.state not in ["done", "cancel"]
            )
            rec.done_order_ids = rec.order_ids.filtered(lambda o: o.state == "done")
            rec.today_order_ids = rec.order_ids.filtered(
                lambda o: o.order_date == today
            )
