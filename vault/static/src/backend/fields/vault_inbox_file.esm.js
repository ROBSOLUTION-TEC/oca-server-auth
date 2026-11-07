// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {VaultFile, vaultFileField} from "./vault_file.esm";
import VaultInboxMixin from "./vault_inbox_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export class VaultInboxFile extends VaultInboxMixin(VaultFile) {
    static template = "vault.FileVaultInbox";

    /**
     * Save the file in a vault
     */
    async _onSaveValue() {
        await this.saveValue(
            "vault.file",
            await this._getCryptedValue(),
            this.fileName || ""
        );
    }
}

const vaultInboxFileField = {
    ...vaultFileField,
    component: VaultInboxFile,
    displayName: _t("Vault Inbox File"),
};

registry.category("fields").add("vault_inbox_file", vaultInboxFileField);
