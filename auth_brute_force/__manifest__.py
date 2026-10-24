# Copyright 2015 GRAP - Sylvain LE GAL
# Copyright 2017 Tecnativa - Jairo Llopis
# Copyright 2025 Nitrokey GmbH
# Copyright 2026 ROBSOLUTION - port 20.0
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Authentication - Brute-Force Filter",
    "version": "20.0.1.0.0",
    "category": "Tools",
    "summary": "Track Authentication Attempts and Prevent Brute-force Attacks",
    "author": "ROBSOLUTION, Nitrokey GmbH, GRAP, Tecnativa, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-auth",
    "license": "AGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.access.csv",
        "views/res_authentication_attempt_views.xml",
    ],
    "installable": True,
}
