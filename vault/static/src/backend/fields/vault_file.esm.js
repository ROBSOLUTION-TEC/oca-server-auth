// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {
    BinaryField,
    binaryField,
    binaryFieldProps,
} from "@web/views/fields/binary/binary_field";
import VaultMixin, {binaryContent} from "./vault_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {downloadFile} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class VaultFile extends VaultMixin(BinaryField, binaryFieldProps) {
    static template = "vault.FileVault";

    setup() {
        super.setup();

        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
    }

    get value() {
        return this.props.record.data[this.props.name];
    }

    /**
     * Update the value field by encrypting the file before
     *
     * @param {Object} param0
     */
    async update({data, name}) {
        if (!data) return await super.update({});
        const encrypted = await this._encrypt(data);
        return await super.update({data: encrypted, name: name});
    }

    /**
     * Get the encrypted (base64 encoded) content of the file
     *
     * @returns the encrypted content
     */
    async _getCryptedValue() {
        // Since 20.0 the record holds the full content (no bin_size anymore)
        const value = binaryContent(this.value);
        if (value || !this.props.record.resId) return value;

        const crypted = await this.orm.read(
            this.props.record.resModel,
            [this.props.record.resId],
            [this.props.name]
        );
        return binaryContent(crypted[0][this.props.name]);
    }

    /**
     * Send the secret to an inbox of an user
     *
     * @param {Object} ev
     */
    async _onSendValue(ev) {
        ev.stopPropagation();

        await this.sendValue("", await this._getCryptedValue(), this.fileName);
    }

    /**
     * Decrypt the file and download it
     */
    async onFileDownload() {
        const cryptedValue = await this._getCryptedValue();
        if (!cryptedValue) {
            this.notification.add(_t("The field is empty, there's nothing to save!"), {
                title: _t("Save As..."),
                type: "danger",
            });
        } else if (this.vault_utils.supported()) {
            const decrypted = await this._decrypt(cryptedValue);
            const base64 = atob(decrypted);
            const buffer = new ArrayBuffer(base64.length);
            const arr = new Uint8Array(buffer);
            for (let i = 0; i < base64.length; i++) arr[i] = base64.charCodeAt(i);
            const blob = new Blob([arr]);
            await downloadFile(blob, this.fileName || "");
        }
    }
}

export const vaultFileField = {
    ...binaryField,
    component: VaultFile,
    displayName: _t("Vault File"),
};

registry.category("fields").add("vault_file", vaultFileField);
