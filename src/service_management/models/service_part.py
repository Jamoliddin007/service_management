from odoo import models, fields

class ServicePart(models.Model):
    _name = "service.part"
    _description = "Servis detali"
    _order = "name"

    name = fields.Char(
        string="Detal nomi",
        required=True
    )
    code = fields.Char(
        string="Detal kodi",
        required=True
    )
    is_active = fields.Boolean(
        string="Faol detal",
        default=True
    )
    description = fields.Text(
        string="Tavsif"
    )

    _sql_constraints = [
        ("code_unique", "unique(code)", "Detal kodi takrorlanmasligi kerak.")
    ]

    def action_deactivate(self):
        """Detalni nofaol qilish"""
        for record in self:
            record.is_active = False

    def action_activate(self):
        """Detalni faol qilish"""
        for record in self:
            record.is_active = True
