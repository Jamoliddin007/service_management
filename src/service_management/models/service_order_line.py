from odoo import models, fields

class ServiceOrderLine(models.Model):
    _name = "service.order.line"
    _description = "Buyurtma qatori"

    order_id = fields.Many2one(
        "service.order",
        string="Buyurtma",
        required=True,
        ondelete="cascade"
    )
    part_id = fields.Many2one(
        "service.part",
        string="Detal",
        required=True,
        ondelete="restrict"
    )
    description = fields.Char(
        string="Qisqa tavsif"
    )
    note = fields.Text(
        string="Eslatma"
    )
