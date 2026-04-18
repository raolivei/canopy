"""Tax Rules Engine for the Neural Economic Growth Advisor.

Canopy - Personal Finance Platform

Hardcoded, versioned tax data for Canada and USA (2025/2026).
No external API calls — all data is embedded and auditable.

Covers:
- Federal + provincial/state income tax brackets
- Registered account contribution limits (RRSP, TFSA, FHSA, 401k, IRA)
- Capital gains tax rates
- Cross-border treaty considerations (US-CA Article XVIII)

IMPORTANT: This is for planning purposes only, not tax advice.
Tax laws change annually. Verify with a tax professional.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class TaxBracket:
    """A single marginal tax bracket."""
    min_income: Decimal
    max_income: Optional[Decimal]  # None = no upper bound
    rate: Decimal                  # e.g. Decimal("0.205") for 20.5%


@dataclass
class TaxResult:
    """Result of a tax calculation."""
    tax_owed: Decimal
    effective_rate: Decimal         # tax_owed / gross_income
    marginal_rate: Decimal          # rate of the top bracket reached
    federal_tax: Decimal
    provincial_state_tax: Decimal
    total_deductions: Decimal       # e.g. basic personal amounts deducted
    net_income: Decimal             # gross - tax_owed


@dataclass
class ContributionLimits:
    """Annual contribution room for registered accounts."""
    year: int
    country: str

    # Canada
    rrsp_limit: Optional[Decimal] = None          # Lower of 18% of income OR dollar limit
    rrsp_dollar_cap: Optional[Decimal] = None     # Annual dollar cap
    tfsa_limit: Optional[Decimal] = None          # Annual TFSA room
    fhsa_limit: Optional[Decimal] = None          # Annual FHSA room
    fhsa_lifetime: Optional[Decimal] = None       # FHSA lifetime limit

    # USA
    k401_limit: Optional[Decimal] = None          # 401(k) elective deferral
    k401_catch_up: Optional[Decimal] = None       # Extra if age >= 50
    ira_limit: Optional[Decimal] = None           # IRA / Roth IRA combined
    ira_catch_up: Optional[Decimal] = None        # Extra if age >= 50
    hsa_individual: Optional[Decimal] = None      # HSA (individual plan)
    hsa_family: Optional[Decimal] = None          # HSA (family plan)


@dataclass
class CapitalGainsTaxResult:
    """Result of a capital gains tax calculation."""
    gross_gains: Decimal
    taxable_gains: Decimal           # After inclusion rate / exclusions
    tax_owed: Decimal
    effective_rate: Decimal          # tax_owed / gross_gains
    inclusion_rate: Decimal          # Fraction of gains that is taxable (CA)
    long_term_rate: Optional[Decimal] = None   # US LTCG rate applied


# ---------------------------------------------------------------------------
# Tax data tables (2025 values; add 2026 when CRA/IRS publish)
# ---------------------------------------------------------------------------

# Canada — Federal brackets 2025
CA_FEDERAL_BRACKETS_2025: list[TaxBracket] = [
    TaxBracket(Decimal("0"),       Decimal("57375"),  Decimal("0.15")),
    TaxBracket(Decimal("57375"),   Decimal("114750"), Decimal("0.205")),
    TaxBracket(Decimal("114750"),  Decimal("177882"), Decimal("0.26")),
    TaxBracket(Decimal("177882"),  Decimal("253414"), Decimal("0.29")),
    TaxBracket(Decimal("253414"),  None,              Decimal("0.33")),
]

CA_FEDERAL_BASIC_PERSONAL_2025 = Decimal("16129")   # Basic personal amount

# Canada — Ontario provincial brackets 2025
CA_ON_BRACKETS_2025: list[TaxBracket] = [
    TaxBracket(Decimal("0"),       Decimal("51446"),  Decimal("0.0505")),
    TaxBracket(Decimal("51446"),   Decimal("102894"), Decimal("0.0915")),
    TaxBracket(Decimal("102894"),  Decimal("150000"), Decimal("0.1116")),
    TaxBracket(Decimal("150000"),  Decimal("220000"), Decimal("0.1216")),
    TaxBracket(Decimal("220000"),  None,              Decimal("0.1316")),
]
CA_ON_BASIC_PERSONAL_2025 = Decimal("11865")

# Canada — British Columbia provincial brackets 2025
CA_BC_BRACKETS_2025: list[TaxBracket] = [
    TaxBracket(Decimal("0"),       Decimal("45654"),  Decimal("0.0506")),
    TaxBracket(Decimal("45654"),   Decimal("91310"),  Decimal("0.077")),
    TaxBracket(Decimal("91310"),   Decimal("104835"), Decimal("0.105")),
    TaxBracket(Decimal("104835"),  Decimal("127299"), Decimal("0.1229")),
    TaxBracket(Decimal("127299"),  Decimal("172602"), Decimal("0.147")),
    TaxBracket(Decimal("172602"),  Decimal("240716"), Decimal("0.168")),
    TaxBracket(Decimal("240716"),  None,              Decimal("0.205")),
]
CA_BC_BASIC_PERSONAL_2025 = Decimal("11981")

# Canada — Alberta provincial brackets 2025
CA_AB_BRACKETS_2025: list[TaxBracket] = [
    TaxBracket(Decimal("0"),       Decimal("148269"), Decimal("0.10")),
    TaxBracket(Decimal("148269"),  Decimal("177922"), Decimal("0.12")),
    TaxBracket(Decimal("177922"),  Decimal("237230"), Decimal("0.13")),
    TaxBracket(Decimal("237230"),  Decimal("355845"), Decimal("0.14")),
    TaxBracket(Decimal("355845"),  None,              Decimal("0.15")),
]
CA_AB_BASIC_PERSONAL_2025 = Decimal("21003")

# USA — Federal brackets 2025 (single filer)
US_FEDERAL_BRACKETS_2025_SINGLE: list[TaxBracket] = [
    TaxBracket(Decimal("0"),       Decimal("11925"),  Decimal("0.10")),
    TaxBracket(Decimal("11925"),   Decimal("48475"),  Decimal("0.12")),
    TaxBracket(Decimal("48475"),   Decimal("103350"), Decimal("0.22")),
    TaxBracket(Decimal("103350"),  Decimal("197300"), Decimal("0.24")),
    TaxBracket(Decimal("197300"),  Decimal("250525"), Decimal("0.32")),
    TaxBracket(Decimal("250525"),  Decimal("626350"), Decimal("0.35")),
    TaxBracket(Decimal("626350"),  None,              Decimal("0.37")),
]

# USA — Federal brackets 2025 (married filing jointly)
US_FEDERAL_BRACKETS_2025_MFJ: list[TaxBracket] = [
    TaxBracket(Decimal("0"),       Decimal("23850"),  Decimal("0.10")),
    TaxBracket(Decimal("23850"),   Decimal("96950"),  Decimal("0.12")),
    TaxBracket(Decimal("96950"),   Decimal("206700"), Decimal("0.22")),
    TaxBracket(Decimal("206700"),  Decimal("394600"), Decimal("0.24")),
    TaxBracket(Decimal("394600"),  Decimal("501050"), Decimal("0.32")),
    TaxBracket(Decimal("501050"),  Decimal("751600"), Decimal("0.35")),
    TaxBracket(Decimal("751600"),  None,              Decimal("0.37")),
]

US_STANDARD_DEDUCTION_SINGLE_2025 = Decimal("15000")
US_STANDARD_DEDUCTION_MFJ_2025    = Decimal("30000")

# USA — State income tax (simplified flat/top rate for planning)
# A full bracket table per state is beyond scope; use effective planning rate.
US_STATE_TAX_RATES: dict[str, Decimal] = {
    "CA": Decimal("0.093"),   # California top marginal (simplified)
    "NY": Decimal("0.0685"),  # New York
    "TX": Decimal("0.00"),    # Texas (no income tax)
    "FL": Decimal("0.00"),    # Florida (no income tax)
    "WA": Decimal("0.00"),    # Washington (no income tax)
    "OR": Decimal("0.099"),   # Oregon
    "WI": Decimal("0.0765"),  # Wisconsin
    "IL": Decimal("0.0495"),  # Illinois (flat)
    "MA": Decimal("0.05"),    # Massachusetts (flat)
    "CO": Decimal("0.044"),   # Colorado (flat)
}

# Contribution limits
CA_CONTRIBUTION_LIMITS: dict[int, ContributionLimits] = {
    2025: ContributionLimits(
        year=2025,
        country="CA",
        rrsp_dollar_cap=Decimal("32490"),
        tfsa_limit=Decimal("7000"),
        fhsa_limit=Decimal("8000"),
        fhsa_lifetime=Decimal("40000"),
    ),
    2026: ContributionLimits(
        year=2026,
        country="CA",
        rrsp_dollar_cap=Decimal("32490"),   # Updated when CRA publishes
        tfsa_limit=Decimal("7000"),
        fhsa_limit=Decimal("8000"),
        fhsa_lifetime=Decimal("40000"),
    ),
}

US_CONTRIBUTION_LIMITS: dict[int, ContributionLimits] = {
    2025: ContributionLimits(
        year=2025,
        country="US",
        k401_limit=Decimal("23500"),
        k401_catch_up=Decimal("7500"),
        ira_limit=Decimal("7000"),
        ira_catch_up=Decimal("1000"),
        hsa_individual=Decimal("4300"),
        hsa_family=Decimal("8550"),
    ),
    2026: ContributionLimits(
        year=2026,
        country="US",
        k401_limit=Decimal("24000"),       # Estimated; updated when IRS publishes
        k401_catch_up=Decimal("7500"),
        ira_limit=Decimal("7000"),
        ira_catch_up=Decimal("1000"),
        hsa_individual=Decimal("4400"),
        hsa_family=Decimal("8750"),
    ),
}


# ---------------------------------------------------------------------------
# Province/State bracket lookup
# ---------------------------------------------------------------------------

_CA_PROVINCE_BRACKETS: dict[str, list[TaxBracket]] = {
    "ON": CA_ON_BRACKETS_2025,
    "BC": CA_BC_BRACKETS_2025,
    "AB": CA_AB_BRACKETS_2025,
}

_CA_PROVINCE_BASIC_PERSONAL: dict[str, Decimal] = {
    "ON": CA_ON_BASIC_PERSONAL_2025,
    "BC": CA_BC_BASIC_PERSONAL_2025,
    "AB": CA_AB_BASIC_PERSONAL_2025,
}


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------

class TaxRulesEngine:
    """Hardcoded tax rules for Canada and USA.

    All monetary values are in the local currency of the country
    (CAD for Canada, USD for USA).
    """

    # US-CA treaty: 15% withholding on dividends paid to non-residents
    US_CA_DIVIDEND_WITHHOLDING = Decimal("0.15")

    # Canada capital gains inclusion rates (post-June 2024 budget)
    CA_CAPITAL_GAINS_INCLUSION_BELOW = Decimal("0.50")    # First $250k
    CA_CAPITAL_GAINS_INCLUSION_ABOVE = Decimal("0.6667")  # Above $250k
    CA_CAPITAL_GAINS_THRESHOLD = Decimal("250000")

    def _apply_brackets(
        self,
        taxable_income: Decimal,
        brackets: list[TaxBracket],
    ) -> tuple[Decimal, Decimal]:
        """Apply progressive bracket tax. Returns (tax_owed, marginal_rate)."""
        tax = Decimal("0")
        marginal = Decimal("0")

        for bracket in brackets:
            if taxable_income <= 0:
                break
            if bracket.max_income is None:
                slab = taxable_income
            else:
                slab = min(taxable_income, bracket.max_income - bracket.min_income)
            tax += slab * bracket.rate
            marginal = bracket.rate
            taxable_income -= slab

        return tax, marginal

    def calculate_tax(
        self,
        country: str,
        province_or_state: Optional[str],
        gross_income: Decimal,
        year: int = 2025,
        filing_status: str = "single",
    ) -> TaxResult:
        """Calculate combined income tax for a given country/jurisdiction.

        Args:
            country: "CA" or "US"
            province_or_state: Province (ON, BC, AB) or US state code
            gross_income: Annual gross income in local currency
            year: Tax year
            filing_status: "single" or "mfj" (married filing jointly, US only)
        """
        if country == "CA":
            return self._calculate_canada_tax(
                gross_income, province_or_state, year
            )
        elif country == "US":
            return self._calculate_us_tax(
                gross_income, province_or_state, year, filing_status
            )
        else:
            # Generic fallback: estimate 25% effective rate
            estimated_tax = gross_income * Decimal("0.25")
            return TaxResult(
                tax_owed=estimated_tax,
                effective_rate=Decimal("0.25"),
                marginal_rate=Decimal("0.25"),
                federal_tax=estimated_tax,
                provincial_state_tax=Decimal("0"),
                total_deductions=Decimal("0"),
                net_income=gross_income - estimated_tax,
            )

    def _calculate_canada_tax(
        self,
        gross_income: Decimal,
        province: Optional[str],
        year: int,
    ) -> TaxResult:
        # Basic personal amount reduces taxable income
        bpa_federal = CA_FEDERAL_BASIC_PERSONAL_2025
        federal_taxable = max(Decimal("0"), gross_income - bpa_federal)

        federal_tax, fed_marginal = self._apply_brackets(
            federal_taxable, CA_FEDERAL_BRACKETS_2025
        )
        # BPA credit: bpa * 15% (lowest federal rate)
        federal_tax = max(Decimal("0"), federal_tax - bpa_federal * Decimal("0.15"))

        # Provincial tax
        prov = (province or "ON").upper()
        prov_brackets = _CA_PROVINCE_BRACKETS.get(prov, CA_ON_BRACKETS_2025)
        prov_bpa = _CA_PROVINCE_BASIC_PERSONAL.get(prov, CA_ON_BASIC_PERSONAL_2025)
        prov_taxable = max(Decimal("0"), gross_income - prov_bpa)
        prov_tax, prov_marginal = self._apply_brackets(prov_taxable, prov_brackets)
        prov_rate = prov_brackets[0].rate if prov_brackets else Decimal("0.0505")
        prov_tax = max(Decimal("0"), prov_tax - prov_bpa * prov_rate)

        total_tax = federal_tax + prov_tax
        effective = (total_tax / gross_income) if gross_income > 0 else Decimal("0")
        combined_marginal = fed_marginal + prov_marginal

        return TaxResult(
            tax_owed=total_tax,
            effective_rate=effective,
            marginal_rate=combined_marginal,
            federal_tax=federal_tax,
            provincial_state_tax=prov_tax,
            total_deductions=bpa_federal + prov_bpa,
            net_income=gross_income - total_tax,
        )

    def _calculate_us_tax(
        self,
        gross_income: Decimal,
        state: Optional[str],
        year: int,
        filing_status: str,
    ) -> TaxResult:
        # Standard deduction
        if filing_status == "mfj":
            std_ded = US_STANDARD_DEDUCTION_MFJ_2025
            brackets = US_FEDERAL_BRACKETS_2025_MFJ
        else:
            std_ded = US_STANDARD_DEDUCTION_SINGLE_2025
            brackets = US_FEDERAL_BRACKETS_2025_SINGLE

        federal_taxable = max(Decimal("0"), gross_income - std_ded)
        federal_tax, fed_marginal = self._apply_brackets(federal_taxable, brackets)

        # State tax (simplified flat/top rate for planning)
        st = (state or "").upper()
        state_rate = US_STATE_TAX_RATES.get(st, Decimal("0.05"))
        state_tax = gross_income * state_rate

        total_tax = federal_tax + state_tax
        effective = (total_tax / gross_income) if gross_income > 0 else Decimal("0")

        return TaxResult(
            tax_owed=total_tax,
            effective_rate=effective,
            marginal_rate=fed_marginal + state_rate,
            federal_tax=federal_tax,
            provincial_state_tax=state_tax,
            total_deductions=std_ded,
            net_income=gross_income - total_tax,
        )

    def get_contribution_limits(
        self,
        country: str,
        year: int = 2025,
        annual_earned_income: Optional[Decimal] = None,
        age: Optional[int] = None,
    ) -> ContributionLimits:
        """Get registered account contribution limits for a given year.

        For Canada, RRSP limit = min(18% of previous year income, dollar cap).
        RRSP room is also affected by pension adjustments (ignored here).
        """
        if country == "CA":
            limits = CA_CONTRIBUTION_LIMITS.get(year, CA_CONTRIBUTION_LIMITS[2025])
            # Calculate RRSP limit based on income
            if annual_earned_income and annual_earned_income > 0:
                income_based = annual_earned_income * Decimal("0.18")
                limits.rrsp_limit = min(income_based, limits.rrsp_dollar_cap)
            else:
                limits.rrsp_limit = limits.rrsp_dollar_cap
            return limits

        elif country == "US":
            limits = US_CONTRIBUTION_LIMITS.get(year, US_CONTRIBUTION_LIMITS[2025])
            # Catch-up contributions for age 50+
            if age and age >= 50:
                limits.k401_limit = (limits.k401_limit or Decimal("0")) + (limits.k401_catch_up or Decimal("0"))
                limits.ira_limit = (limits.ira_limit or Decimal("0")) + (limits.ira_catch_up or Decimal("0"))
            return limits

        # Generic empty limits
        return ContributionLimits(year=year, country=country)

    def calculate_capital_gains_tax(
        self,
        country: str,
        province_or_state: Optional[str],
        gross_gains: Decimal,
        other_income: Decimal = Decimal("0"),
        year: int = 2025,
        long_term: bool = True,
    ) -> CapitalGainsTaxResult:
        """Calculate capital gains tax.

        Canada: inclusion rate applied, then taxed as regular income.
        USA: separate long-term / short-term rates.
        """
        if country == "CA":
            return self._canada_capital_gains(
                gross_gains, other_income, province_or_state, year
            )
        elif country == "US":
            return self._us_capital_gains(
                gross_gains, other_income, province_or_state, year, long_term
            )
        else:
            estimated = gross_gains * Decimal("0.20")
            return CapitalGainsTaxResult(
                gross_gains=gross_gains,
                taxable_gains=gross_gains,
                tax_owed=estimated,
                effective_rate=Decimal("0.20"),
                inclusion_rate=Decimal("1.0"),
            )

    def _canada_capital_gains(
        self,
        gross_gains: Decimal,
        other_income: Decimal,
        province: Optional[str],
        year: int,
    ) -> CapitalGainsTaxResult:
        # Post-June 2024 budget: 50% inclusion for first $250k, 66.67% above
        if gross_gains <= self.CA_CAPITAL_GAINS_THRESHOLD:
            taxable = gross_gains * self.CA_CAPITAL_GAINS_INCLUSION_BELOW
            inclusion = self.CA_CAPITAL_GAINS_INCLUSION_BELOW
        else:
            below_threshold = self.CA_CAPITAL_GAINS_THRESHOLD * self.CA_CAPITAL_GAINS_INCLUSION_BELOW
            above_threshold = (gross_gains - self.CA_CAPITAL_GAINS_THRESHOLD) * self.CA_CAPITAL_GAINS_INCLUSION_ABOVE
            taxable = below_threshold + above_threshold
            inclusion = taxable / gross_gains

        # Tax the included gains as income on top of other_income
        total_income = other_income + taxable
        full_result = self._calculate_canada_tax(total_income, province, year)
        base_result = self._calculate_canada_tax(other_income, province, year)
        tax_on_gains = full_result.tax_owed - base_result.tax_owed
        effective = (tax_on_gains / gross_gains) if gross_gains > 0 else Decimal("0")

        return CapitalGainsTaxResult(
            gross_gains=gross_gains,
            taxable_gains=taxable,
            tax_owed=tax_on_gains,
            effective_rate=effective,
            inclusion_rate=inclusion,
        )

    def _us_capital_gains(
        self,
        gross_gains: Decimal,
        other_income: Decimal,
        state: Optional[str],
        year: int,
        long_term: bool,
    ) -> CapitalGainsTaxResult:
        total_income = other_income + gross_gains

        if not long_term:
            # Short-term: taxed as ordinary income
            result = self._calculate_us_tax(total_income, state, year, "single")
            base = self._calculate_us_tax(other_income, state, year, "single")
            tax_on_gains = result.tax_owed - base.tax_owed
            return CapitalGainsTaxResult(
                gross_gains=gross_gains,
                taxable_gains=gross_gains,
                tax_owed=tax_on_gains,
                effective_rate=(tax_on_gains / gross_gains) if gross_gains > 0 else Decimal("0"),
                inclusion_rate=Decimal("1.0"),
                long_term_rate=None,
            )

        # Long-term federal LTCG rates (2025)
        if total_income <= Decimal("48350"):
            ltcg_rate = Decimal("0.00")
        elif total_income <= Decimal("533400"):
            ltcg_rate = Decimal("0.15")
        else:
            ltcg_rate = Decimal("0.20")

        federal_gains_tax = gross_gains * ltcg_rate

        # Net Investment Income Tax (NIIT) 3.8% over $200k
        if total_income > Decimal("200000"):
            niit = gross_gains * Decimal("0.038")
        else:
            niit = Decimal("0")

        # State tax still applies to LTCG for most states
        st = (state or "").upper()
        state_rate = US_STATE_TAX_RATES.get(st, Decimal("0.05"))
        state_gains_tax = gross_gains * state_rate

        total_tax = federal_gains_tax + niit + state_gains_tax
        effective = (total_tax / gross_gains) if gross_gains > 0 else Decimal("0")

        return CapitalGainsTaxResult(
            gross_gains=gross_gains,
            taxable_gains=gross_gains,
            tax_owed=total_tax,
            effective_rate=effective,
            inclusion_rate=Decimal("1.0"),
            long_term_rate=ltcg_rate,
        )

    def estimate_tax_drag(
        self,
        country: str,
        province_or_state: Optional[str],
        annual_gains: Decimal,
        annual_income: Decimal,
        year: int = 2025,
    ) -> Decimal:
        """Estimate annual tax drag on investment growth (as a fraction).

        Used by the Growth Advisor to model after-tax compounding.
        Returns the fraction of gains consumed by tax (e.g. 0.15 = 15%).
        """
        if annual_gains <= 0:
            return Decimal("0")
        result = self.calculate_capital_gains_tax(
            country, province_or_state, annual_gains, annual_income, year
        )
        return result.effective_rate

    def cross_border_rrsp_note(self) -> str:
        """Return the key US-CA treaty note on RRSP treatment."""
        return (
            "Under Article XVIII(7) of the US-Canada Tax Treaty, "
            "RRSP growth is generally not taxable in the US until withdrawn. "
            "An election (Form 8891 / simplified via Form 1040) is required. "
            "Consult a cross-border tax professional."
        )

    def roth_relocation_note(self) -> str:
        """Return the note on Roth IRA when relocating from US to Canada."""
        return (
            "Roth IRA is not recognized as a tax-free account under Canadian tax law. "
            "Growth inside a Roth IRA is taxable in Canada unless a treaty election "
            "is made annually (RC268). Maximize Roth contributions before relocating "
            "to Canada to lock in US tax-free growth. Consult a cross-border CPA."
        )
