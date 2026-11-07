// © 2021-2022 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {ORM} from "@web/core/orm_plugin";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {usePlugin} from "@odoo/owl";
import {user} from "@web/core/user";
import {useService} from "@web/core/utils/hooks";

// Since 20.0 the user menu items are evaluated in the setup of the user menu
export function vaultPreferencesItem() {
    const action = useService("action");
    const orm = usePlugin(ORM);

    return {
        type: "item",
        id: "key_management",
        description: _t("Key Management"),
        callback: async function () {
            const actionDescription = await orm.call("res.users", "action_get_vault");
            actionDescription.res_id = user.userId;
            action.doAction(actionDescription);
        },
        sequence: 55,
    };
}

registry
    .category("user_menuitems")
    .add("vault_key_management", vaultPreferencesItem, {force: true});
