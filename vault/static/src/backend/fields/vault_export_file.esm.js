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

export class VaultExportFile extends VaultMixin(BinaryField, binaryFieldProps) {
    static template = "vault.FileVaultExport";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.exporter = useService("vault_export");
        this.vault_utils = useService("vault_utils");
    }

    /**
     * Get the exported JSON content
     *
     * @returns the JSON string
     */
    async _getCryptedValue() {
        let value = binaryContent(this.props.record.data[this.props.name]);
        if (!value && this.props.record.resId) {
            const crypted = await this.orm.read(
                this.props.record.resModel,
                [this.props.record.resId],
                [this.props.name]
            );
            value = binaryContent(crypted[0][this.props.name]);
        }
        // Binary values are base64 encoded since 20.0; the content is ASCII JSON
        return value ? atob(value) : false;
    }

    /**
     * Encrypt the export and download it
     */
    async onFileDownload() {
        const cryptedValue = await this._getCryptedValue();
        if (!cryptedValue) {
            this.notification.add(_t("The field is empty, there's nothing to save!"), {
                title: _t("Save As..."),
                type: "danger",
            });
        } else if (this.vault_utils.supported()) {
            const content = JSON.stringify(
                await this.exporter.export(
                    await this._getMasterKey(),
                    this.fileName,
                    cryptedValue
                )
            );

            const buffer = new ArrayBuffer(content.length);
            const arr = new Uint8Array(buffer);
            for (let i = 0; i < content.length; i++) arr[i] = content.charCodeAt(i);
            const blob = new Blob([arr]);
            await downloadFile(blob, this.fileName || "");
        }
    }
}

export const vaultExportFileField = {
    ...binaryField,
    component: VaultExportFile,
    displayName: _t("Vault export file"),
};

registry.category("fields").add("vault_export_file", vaultExportFileField);
