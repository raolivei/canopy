import type { Exchange } from "@/types/exchange";
import {
  assetOptions,
  draftEffectiveRate,
  draftFromExchange,
  draftToInput,
  emptyDraft,
  formatRate,
  hasErrors,
  legName,
  todayKey,
  validateDraft,
} from "@/utils/exchangeMapping";

const filled = () => ({
  ...emptyDraft(new Date(2026, 9, 1)),
  from_currency: "CAD",
  from_amount: "1000",
  to_currency: "BRL",
  to_amount: "3900.50",
});

describe("exchangeMapping", () => {
  it("builds an empty draft dated today", () => {
    expect(todayKey(new Date(2026, 0, 5))).toBe("2026-01-05");
    expect(emptyDraft(new Date(2026, 9, 1))).toMatchObject({ date: "2026-10-01", from_currency: "CAD", to_currency: "USD" });
  });

  it("validates amounts, currencies, fee and rate", () => {
    const empty = validateDraft(emptyDraft());
    expect(empty.from_amount).toBe("Required");
    expect(empty.to_amount).toBe("Required");
    expect(hasErrors(validateDraft(filled()))).toBe(false);

    expect(validateDraft({ ...filled(), to_currency: "CAD" }).to_currency).toBe("Pick a different currency");
    expect(validateDraft({ ...filled(), from_amount: "0" }).from_amount).toBe("Must be greater than zero");
    expect(validateDraft({ ...filled(), to_amount: "1.234" }).to_amount).toMatch(/two decimals/);
    expect(validateDraft({ ...filled(), fee_amount: "0" }).fee_amount).toBeUndefined();
    expect(validateDraft({ ...filled(), fee_amount: "abc" }).fee_amount).toMatch(/two decimals/);
    expect(validateDraft({ ...filled(), quoted_rate: "-1" }).quoted_rate).toMatch(/positive rate/);
    expect(validateDraft({ ...filled(), date: "" }).date).toBe("Pick a date");
  });

  it("maps a draft to the API payload", () => {
    expect(draftToInput({ ...filled(), fee_amount: "3.99", from_asset_id: "7", to_label: " BRL account " })).toEqual({
      date: "2026-10-01",
      provider: "wise",
      from_currency: "CAD",
      from_amount: 1000,
      to_currency: "BRL",
      to_amount: 3900.5,
      fee_amount: 3.99,
      fee_currency: "CAD",
      quoted_rate: null,
      from_asset_id: 7,
      to_asset_id: null,
      from_label: null,
      to_label: "BRL account",
      notes: null,
    });
    expect(draftToInput(filled()).fee_currency).toBeNull();
  });

  it("round-trips an exchange into a draft", () => {
    const exchange = {
      id: 1,
      date: "2026-10-01",
      provider: "remitly",
      from_currency: "CAD",
      from_amount: 1000,
      to_currency: "BRL",
      to_amount: 3900,
      fee_amount: null,
      fee_currency: null,
      quoted_rate: 3.91,
      effective_rate: 3.9,
      from_asset_id: 4,
      to_asset_id: null,
      from_label: null,
      to_label: "BRL account",
      external_id: null,
      source: "manual",
      notes: null,
      benchmark: null,
      created_at: "",
      updated_at: "",
    } as Exchange;
    const draft = draftFromExchange(exchange);
    expect(draft).toMatchObject({ from_amount: "1000.00", fee_amount: "", quoted_rate: "3.91", from_asset_id: "4" });
    expect(draftToInput(draft)).toMatchObject({ provider: "remitly", to_amount: 3900, quoted_rate: 3.91, from_asset_id: 4 });
  });

  it("computes and formats the effective rate", () => {
    expect(draftEffectiveRate(filled())).toBeCloseTo(3.9005);
    expect(draftEffectiveRate({ ...filled(), to_amount: "" })).toBeNull();
    expect(formatRate(3.9005, "CAD", "BRL")).toBe("1 CAD = 3.9005 BRL");
    expect(formatRate(0.0071, "JPY", "CAD")).toBe("1 JPY = 0.007100 CAD");
  });

  it("offers only asset accounts and names legs", () => {
    const options = assetOptions([
      { id: "asset:3", name: "Wise CAD", currency: "CAD", institution: "Wise" },
      { id: "liability:2", name: "Card", currency: "CAD" },
    ]);
    expect(options).toEqual([{ value: "3", label: "Wise CAD (CAD) · Wise" }]);
    const names = new Map([["3", "Wise CAD"]]);
    expect(legName(3, "ignored", "CAD", names)).toBe("Wise CAD");
    expect(legName(null, "BRL account", "BRL", names)).toBe("BRL account");
    expect(legName(null, null, "BRL", names)).toBe("BRL");
  });
});
