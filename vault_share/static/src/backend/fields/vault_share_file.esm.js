// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {VaultFile, vaultFileField} from "@vault/backend/fields/vault_file.esm";
import VaultShareMixin from "./vault_share_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export class VaultShareFile extends VaultShareMixin(VaultFile) {
    static template = "vault.FileShareVault";

    /**
     * secret_file is a Char field: store the encrypted base64 string as is
     * (the 20.0 binary widget writes {filename, content} objects)
     *
     * @param {Object} param0
     */
    async update({data, name}) {
        const {fileNameField, record} = this.props;
        const changes = {
            [this.props.name]: data ? await this._encrypt(data) : false,
        };
        if (fileNameField in record.fields && record.data[fileNameField] !== name)
            changes[fileNameField] = name || "";
        return await record.update(changes);
    }
}

export const vaultShareFileField = {
    ...vaultFileField,
    component: VaultShareFile,
    displayName: _t("Vault Share Field"),
    supportedTypes: ["char"],
};

registry.category("fields").add("vault_share_file", vaultShareFileField);
