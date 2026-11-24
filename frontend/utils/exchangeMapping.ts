/**
 * Pure helpers for the Exchange page: form draft, validation, payload mapping
 * and rate formatting. No React, no fetch.
 */

import type { Exchange, ExchangeInput, ExchangeProvider } from "@/types/exchange";

export const PROVIDER_LABEL: Record<ExchangeProvider, string> = {
  wise: "Wise",
  remitly: "Remitly",
  instarem: "Instarem",
  bank: "Bank",
  other: "Other",
};

export const PROVIDER_OPTIONS = (Object.keys(PROVIDER_LABEL) as ExchangeProvider[]).map((value) => ({
  value,
  label: PROVIDER_LABEL[value],
}));

export interface ExchangeDraft {
  date: string;
  provider: ExchangeProvider;
  from_currency: string;
  from_amount: string;
  to_currency: string;
  to_amount: string;
  fee_amount: string;
  fee_currency: string;
  quoted_rate: string;
  /** "" for none, otherwise the asset id as a string. */
  from_asset_id: string;
  to_asset_id: string;
  from_label: string;
  to_label: string;
  notes: string;
}

export type ExchangeDraftErrors = Partial<Record<keyof ExchangeDraft, string>>;

export function todayKey(today: Date = new Date()): string {
  const m = String(today.getMonth() + 1).padStart(2, "0");
  const d = String(today.getDate()).padStart(2, "0");
  return `${today.getFullYear()}-${m}-${d}`;
}

export function emptyDraft(today: Date = new Date()): ExchangeDraft {
  return {
    date: todayKey(today),
    provider: "wise",
    from_currency: "CAD",
    from_amount: "",
    to_currency: "USD",
    to_amount: "",
    fee_amount: "",
    fee_currency: "",
    quoted_rate: "",
    from_asset_id: "",
    to_asset_id: "",
    from_label: "",
    to_label: "",
    notes: "",
  };
}

export function draftFromExchange(exchange: Exchange): ExchangeDraft {
  return {
    date: exchange.date,
    provider: exchange.provider,
    from_currency: exchange.from_currency,
    from_amount: exchange.from_amount.toFixed(2),
    to_currency: exchange.to_currency,
    to_amount: exchange.to_amount.toFixed(2),
    fee_amount: exchange.fee_amount === null ? "" : exchange.fee_amount.toFixed(2),
    fee_currency: exchange.fee_currency ?? "",
    quoted_rate: exchange.quoted_rate === null ? "" : String(exchange.quoted_rate),
    from_asset_id: exchange.from_asset_id === null ? "" : String(exchange.from_asset_id),
    to_asset_id: exchange.to_asset_id === null ? "" : String(exchange.to_asset_id),
    from_label: exchange.from_label ?? "",
    to_label: exchange.to_label ?? "",
    notes: exchange.notes ?? "",
  };
}

const MONEY = /^\d+(\.\d{1,2})?$/;
const RATE = /^\d+(\.\d{1,8})?$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;

function amountError(value: string, { required, allowZero }: { required: boolean; allowZero: boolean }) {
  const trimmed = value.trim();
  if (!trimmed) return required ? "Required" : undefined;
  if (!MONEY.test(trimmed)) return "Enter an amount with up to two decimals";
  if (!allowZero && Number(trimmed) <= 0) return "Must be greater than zero";
  return undefined;
}

export function validateDraft(draft: ExchangeDraft): ExchangeDraftErrors {
  const errors: ExchangeDraftErrors = {};
  if (!DATE.test(draft.date) || Number.isNaN(Date.parse(draft.date))) errors.date = "Pick a date";
  errors.from_amount = amountError(draft.from_amount, { required: true, allowZero: false });
  errors.to_amount = amountError(draft.to_amount, { required: true, allowZero: false });
  errors.fee_amount = amountError(draft.fee_amount, { required: false, allowZero: true });
  if (draft.from_currency === draft.to_currency) errors.to_currency = "Pick a different currency";
  const rate = draft.quoted_rate.trim();
  if (rate && (!RATE.test(rate) || Number(rate) <= 0)) errors.quoted_rate = "Enter a positive rate (up to 8 decimals)";
  if (draft.from_label.length > 200) errors.from_label = "Keep it under 200 characters";
  if (draft.to_label.length > 200) errors.to_label = "Keep it under 200 characters";
  if (draft.notes.length > 2000) errors.notes = "Keep it under 2000 characters";
  for (const key of Object.keys(errors) as (keyof ExchangeDraft)[]) if (!errors[key]) delete errors[key];
  return errors;
}

export function hasErrors(errors: ExchangeDraftErrors): boolean {
  return Object.keys(errors).length > 0;
}

const orNull = (value: string) => (value.trim() ? value.trim() : null);
const numOrNull = (value: string) => (value.trim() ? Number(value) : null);

export function draftToInput(draft: ExchangeDraft): ExchangeInput {
  const fee = numOrNull(draft.fee_amount);
  return {
    date: draft.date,
    provider: draft.provider,
    from_currency: draft.from_currency,
    from_amount: Number(draft.from_amount),
    to_currency: draft.to_currency,
    to_amount: Number(draft.to_amount),
    fee_amount: fee,
    fee_currency: fee === null ? null : draft.fee_currency || draft.from_currency,
    quoted_rate: numOrNull(draft.quoted_rate),
    from_asset_id: numOrNull(draft.from_asset_id),
    to_asset_id: numOrNull(draft.to_asset_id),
    from_label: orNull(draft.from_label),
    to_label: orNull(draft.to_label),
    notes: orNull(draft.notes),
  };
}

/** Effective rate (1 from in to) for a draft, or null while amounts are incomplete. */
export function draftEffectiveRate(draft: ExchangeDraft): number | null {
  const from = Number(draft.from_amount);
  const to = Number(draft.to_amount);
  if (!MONEY.test(draft.from_amount.trim()) || !MONEY.test(draft.to_amount.trim()) || from <= 0 || to <= 0) return null;
  return to / from;
}

/** "1 CAD = 3.9000 BRL" with 4 decimals (6 for rates below 0.01). */
export function formatRate(rate: number, from: string, to: string): string {
  const digits = rate < 0.01 ? 6 : 4;
  return `1 ${from} = ${rate.toFixed(digits)} ${to}`;
}

/** Account picker options: only asset accounts ("asset:N") can be linked. */
export function assetOptions(accounts: { id: string; name: string; currency: string; institution?: string | null }[]) {
  return accounts
    .filter((a) => a.id.startsWith("asset:"))
    .map((a) => ({
      value: a.id.slice("asset:".length),
      label: `${a.name} (${a.currency})${a.institution ? ` · ${a.institution}` : ""}`,
    }));
}

/** Display name for a leg: linked account name, then free-text label, then the currency. */
export function legName(
  assetId: number | null,
  label: string | null,
  currency: string,
  assetNames: Map<string, string>,
): string {
  if (assetId !== null && assetNames.has(String(assetId))) return assetNames.get(String(assetId))!;
  return label ?? currency;
}
