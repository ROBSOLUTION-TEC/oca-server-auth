// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {VaultField, vaultField} from "./vault_field.esm";
import VaultInboxMixin from "./vault_inbox_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export class VaultInboxField extends VaultInboxMixin(VaultField) {
    static template = "vault.FieldVaultInbox";

    /**
     * Save the secret in a vault
     */
    async _onSaveValue() {
        await this.saveValue("vault.field", this.value);
    }
}

export const vaultInboxField = {
    ...vaultField,
    component: VaultInboxField,
    displayName: _t("Vault Inbox Field"),
};

registry.category("fields").add("vault_inbox_field", vaultInboxField);
