// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {
    Component,
    onMounted,
    onPatched,
    proxy,
    signal,
    untrack,
    useListener,
} from "@odoo/owl";
import {useBus, useService} from "@web/core/utils/hooks";
import VaultMixin from "./vault_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {getActiveHotkey} from "@web/core/hotkeys/hotkey_utils";
import {registry} from "@web/core/registry";

export class VaultField extends VaultMixin(Component) {
    static template = "vault.FieldVault";

    input = signal.ref();
    span = signal.ref();

    setup() {
        super.setup();

        this.action = useService("action");
        this.state = proxy({
            decrypted: false,
            decryptedValue: "",
        });
        // Not rendered: kept outside of the reactive state
        this.isDirty = false;
        this.lastSetValue = null;

        useListener(this.input, "input", (ev) => this.onInput(ev));
        useListener(this.input, "keydown", (ev) => this.onKeydown(ev));

        // Decrypt the value into the input after each render
        const syncInput = () => {
            const inputEl = untrack(this.input);
            const isInvalid = this.props.record
                ? this.props.record.isFieldInvalid(this.props.name)
                : false;
            if (inputEl && !this.isDirty && !isInvalid) {
                Promise.resolve(this.getValue()).then((val) => {
                    if (!untrack(this.input)) return;
                    if (val) inputEl.value = val;
                    else if (val !== "")
                        this.props.record.setInvalidField(this.props.name);
                });
                this.lastSetValue = inputEl.value;
            }
        };
        onMounted(syncInput);
        onPatched(syncInput);

        const {model} = this.props.record;
        useBus(model.bus, "WILL_SAVE_URGENTLY", () => this.commitChanges(true));
        useBus(model.bus, "NEED_LOCAL_CHANGES", (ev) =>
            ev.detail.proms.push(this.commitChanges())
        );
        useBus(model.bus, "ENCRYPT_FIELDS", () => {
            this.state.decrypted = false;
            this.showValue();
        });
    }

    /**
     * Get the decrypted value or a placeholder
     *
     * @returns the decrypted value or a placeholder
     */
    get value() {
        return this.props.record.data[this.props.name];
    }

    /**
     * Generate a new secret
     *
     * @param {Object} ev
     */
    async _onGenerateValue(ev) {
        ev.stopPropagation();

        const password = await this.vault_utils.generate_pass();
        if (password) await this.storeValue(password);
    }

    /**
     * Toggle between visible and invisible secret
     *
     * @param {Object} ev
     */
    async _onShowValue(ev) {
        ev.stopPropagation();

        this.state.decrypted = !this.state.decrypted;
        if (this.state.decrypted) {
            this.state.decryptedValue = await this._decrypt(this.value);
        } else {
            this.state.decryptedValue = "";
        }

        await this.showValue();
    }

    /**
     * Copy the decrypted secret to the clipboard
     *
     * @param {Object} ev
     */
    async _onCopyValue(ev) {
        ev.stopPropagation();

        const value = await this._decrypt(this.value);
        await navigator.clipboard.writeText(value);
    }

    /**
     * Send the secret to an inbox of an user
     *
     * @param {Object} ev
     */
    async _onSendValue(ev) {
        ev.stopPropagation();

        await this.sendValue(this.value, "");
    }

    /**
     * Get the decrypted value or a placeholder
     *
     * @returns the decrypted value or a placeholder
     */
    get formattedValue() {
        if (!this.value) return "";
        if (this.state.decrypted) return this.state.decryptedValue || "*******";
        return "*******";
    }

    /**
     * Decrypt the value of the field
     *
     * @returns decrypted value
     */
    async getValue() {
        return await this._decrypt(this.value);
    }

    /**
     * Update the value shown to the user
     */
    async showValue() {
        // The span is rendered from the reactive state (t-out, never as HTML):
        // writing to the DOM here would detach the node rendered by Owl
    }

    /**
     * Handle input event and set the state to dirty
     *
     * @param {Object} ev
     */
    onInput(ev) {
        ev.stopPropagation();

        this.isDirty = ev.target.value !== this.lastSetValue;
        if (this.isDirty)
            this.props.record.model.bus.trigger("FIELD_IS_DIRTY", this.isDirty);
    }

    /**
     * Commit the changes of the input field to the record
     *
     * @param {Boolean} urgent
     */
    async commitChanges(urgent) {
        const inputEl = untrack(this.input);
        if (!inputEl) return;

        this.isDirty = inputEl.value !== this.lastSetValue;
        if (this.isDirty || urgent) {
            this.isDirty = false;

            const val = inputEl.value || false;
            if (val !== (this.lastSetValue || false)) {
                this.lastSetValue = inputEl.value;
                this.state.decryptedValue = inputEl.value;
                await this.storeValue(val);
                this.props.record.model.bus.trigger("FIELD_IS_DIRTY", this.isDirty);
            }
        }
    }

    /**
     * Handle keyboard events and trigger changes
     *
     * @param {Object} ev
     */
    onKeydown(ev) {
        ev.stopPropagation();

        const hotkey = getActiveHotkey(ev);
        if (["enter", "tab", "shift+tab"].includes(hotkey)) this.commitChanges(false);
    }
}

export const vaultField = {
    component: VaultField,
    displayName: _t("Vault Field"),
    supportedTypes: ["char"],
};

registry.category("fields").add("vault_field", vaultField);
