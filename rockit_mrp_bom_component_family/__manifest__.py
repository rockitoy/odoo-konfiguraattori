# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "BoM component families",
    "summary": "One attribute-matched BoM line chooses the component template (family) "
    "by the attribute values of the produced variant",
    "version": "20.0.1.0.0",
    "development_status": "Beta",
    "category": "Manufacturing",
    "website": "https://github.com/rockitoy/odoo-konfiguraattori",
    "author": "RockIT Oy",
    "license": "AGPL-3",
    "depends": ["mrp_bom_attribute_match"],
    "data": ["views/mrp_bom_views.xml"],
    "installable": True,
}
