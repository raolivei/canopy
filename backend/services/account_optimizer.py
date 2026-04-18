"""Account Optimizer for the Neural Economic Growth Advisor.

Canopy - Personal Finance Platform

Given a user's financial profile and existing assets, generates
an ordered contribution priority ladder for tax efficiency.

Priority logic:
- Canada: Employer match -> RRSP (high bracket) -> TFSA -> FHSA (if eligible) -> Non-reg
- USA: Employer match -> 401(k) -> Roth IRA (if eligible) -> Taxable
- Cross-border relocation flags: Roth before leaving US, RRSP treaty protection

All dollar amounts are in the user's income_currency from their profile.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from backend.db.models.financial_profile import AdvisorGoal, EmploymentType, VisaType
from backend.services.tax_rules_engine import TaxRulesEngine


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class AccountRecommendation:
    """A single entry in the contribution priority ladder."""
    rank: int
    account_type: str          # e.g. "RRSP", "TFSA", "401k", "Roth IRA"
    annual_amount: Decimal     # Recommended annual contribution
    annual_limit: Decimal      # Max allowed by law
    tax_benefit: str           # "pre-tax", "tax-free growth", "taxable"
    tax_savings_estimate: Decimal  # Estimated tax saved vs contributing to taxable
    reason: str                # Human-readable rationale
    action: str                # Specific action step
    priority: str              # "essential", "high", "medium", "low"
    is_cross_border_note: bool = False
    cross_border_note: Optional[str] = None


@dataclass
class OptimizationResult:
    """Complete account optimization result."""
    total_available_to_invest: Decimal
    total_tax_sheltered_capacity: Decimal
    recommendations: list[AccountRecommendation] = field(default_factory=list)
    unallocated_amount: Decimal = Decimal("0")
    total_estimated_tax_savings: Decimal = Decimal("0")
    summary: str = ""
    cross_border_alerts: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Optimizer
# ---------------------------------------------------------------------------

class AccountOptimizer:
    """Generates tax-optimized contribution ladders."""

    # RRSP optimization threshold: if marginal rate >= this, RRSP preferred over TFSA
    RRSP_PREFERRED_MARGINAL_RATE = Decimal("0.26")

    def __init__(self, tax_engine: Optional[TaxRulesEngine] = None):
        self.tax = tax_engine or TaxRulesEngine()

    def optimize(
        self,
        country: str,
        province_or_state: Optional[str],
        annual_gross_income: Decimal,
        monthly_savings: Decimal,
        employment_type: str,
        visa_type: Optional[str],
        goals: Optional[list[str]],
        current_age: Optional[int],
        year: int = 2025,
    ) -> OptimizationResult:
        """Generate ordered contribution recommendations.

        Args:
            country: "CA" or "US"
            province_or_state: Province (ON, BC...) or US state
            annual_gross_income: Gross annual income in local currency
            monthly_savings: Available monthly savings to invest
            employment_type: "employee", "contractor", "self_employed"
            visa_type: Visa/immigration status
            goals: List of AdvisorGoal values
            current_age: User's age (for catch-up limits)
            year: Tax year for limits
        """
        goals = goals or []
        annual_savings = monthly_savings * 12

        tax_result = self.tax.calculate_tax(
            country, province_or_state, annual_gross_income, year
        )
        limits = self.tax.get_contribution_limits(
            country, year, annual_gross_income, current_age
        )

        if country == "CA":
            return self._optimize_canada(
                annual_gross_income, annual_savings, employment_type,
                visa_type, goals, current_age, year, tax_result, limits,
                province_or_state
            )
        elif country == "US":
            return self._optimize_usa(
                annual_gross_income, annual_savings, employment_type,
                visa_type, goals, current_age, year, tax_result, limits,
                province_or_state
            )
        else:
            return self._optimize_generic(annual_savings)

    def _optimize_canada(
        self,
        income, annual_savings, employment_type, visa_type, goals,
        age, year, tax_result, limits, province
    ) -> OptimizationResult:
        recommendations = []
        remaining = annual_savings
        rank = 1
        marginal = tax_result.marginal_rate
        cross_border_alerts = []

        # RRSP limit
        rrsp_limit = limits.rrsp_limit or Decimal("0")
        tfsa_limit = limits.tfsa_limit or Decimal("0")
        fhsa_limit = limits.fhsa_limit or Decimal("0")

        # 1. RRSP vs TFSA decision based on marginal rate
        if marginal >= self.RRSP_PREFERRED_MARGINAL_RATE:
            # High earner: RRSP first (deduction at high rate, withdraw at low rate)
            rrsp_contribution = min(remaining, rrsp_limit)
            tax_savings = rrsp_contribution * marginal
            recommendations.append(AccountRecommendation(
                rank=rank,
                account_type="RRSP",
                annual_amount=rrsp_contribution,
                annual_limit=rrsp_limit,
                tax_benefit="pre-tax",
                tax_savings_estimate=tax_savings,
                reason=(
                    f"Your marginal tax rate is {float(marginal*100):.1f}% — "
                    "RRSP contributions reduce taxable income at this high rate. "
                    "Withdrawals in retirement typically occur at a lower rate."
                ),
                action=f"Contribute ${rrsp_contribution:,.0f} to your RRSP this year "
                       f"(room: ${rrsp_limit:,.0f}).",
                priority="essential" if rrsp_contribution > 0 else "medium",
            ))
            remaining -= rrsp_contribution
            rank += 1

            # TFSA next
            tfsa_contribution = min(remaining, tfsa_limit)
            recommendations.append(AccountRecommendation(
                rank=rank,
                account_type="TFSA",
                annual_amount=tfsa_contribution,
                annual_limit=tfsa_limit,
                tax_benefit="tax-free growth",
                tax_savings_estimate=tfsa_contribution * Decimal("0.10"),
                reason=(
                    "TFSA growth and withdrawals are fully tax-free. "
                    "Ideal for medium-term savings and flexible access."
                ),
                action=f"Contribute ${tfsa_contribution:,.0f} to your TFSA "
                       f"(annual room: ${tfsa_limit:,.0f}).",
                priority="high",
            ))
            remaining -= tfsa_contribution
            rank += 1
        else:
            # Lower earner: TFSA first (marginal rate too low for RRSP deduction to shine)
            tfsa_contribution = min(remaining, tfsa_limit)
            recommendations.append(AccountRecommendation(
                rank=rank,
                account_type="TFSA",
                annual_amount=tfsa_contribution,
                annual_limit=tfsa_limit,
                tax_benefit="tax-free growth",
                tax_savings_estimate=tfsa_contribution * Decimal("0.10"),
                reason=(
                    f"Your marginal rate is {float(marginal*100):.1f}% — "
                    "TFSA is preferred when the RRSP deduction benefit is modest. "
                    "Tax-free growth compounds without future withdrawal tax."
                ),
                action=f"Contribute ${tfsa_contribution:,.0f} to your TFSA "
                       f"(annual room: ${tfsa_limit:,.0f}).",
                priority="essential",
            ))
            remaining -= tfsa_contribution
            rank += 1

            rrsp_contribution = min(remaining, rrsp_limit)
            if rrsp_contribution > 0:
                tax_savings = rrsp_contribution * marginal
                recommendations.append(AccountRecommendation(
                    rank=rank,
                    account_type="RRSP",
                    annual_amount=rrsp_contribution,
                    annual_limit=rrsp_limit,
                    tax_benefit="pre-tax",
                    tax_savings_estimate=tax_savings,
                    reason=(
                        "RRSP still provides a tax deduction and tax-deferred growth. "
                        "Useful for building retirement income and smoothing taxes."
                    ),
                    action=f"Contribute ${rrsp_contribution:,.0f} to your RRSP.",
                    priority="medium",
                ))
                remaining -= rrsp_contribution
                rank += 1

        # FHSA if home purchase is a goal
        if AdvisorGoal.HOME_PURCHASE in goals or AdvisorGoal.FHSA_ELIGIBLE in goals:
            fhsa_contribution = min(remaining, fhsa_limit)
            if fhsa_contribution > 0:
                tax_savings = fhsa_contribution * marginal
                recommendations.append(AccountRecommendation(
                    rank=rank,
                    account_type="FHSA",
                    annual_amount=fhsa_contribution,
                    annual_limit=fhsa_limit,
                    tax_benefit="pre-tax + tax-free withdrawal",
                    tax_savings_estimate=tax_savings,
                    reason=(
                        "FHSA combines RRSP deductibility with TFSA-style tax-free "
                        "withdrawal for a first home. Best of both worlds — use it fully "
                        f"to build toward your home purchase goal."
                    ),
                    action=f"Open and contribute ${fhsa_contribution:,.0f} to your FHSA "
                           f"(annual room: ${fhsa_limit:,.0f}, lifetime: $40,000).",
                    priority="essential",
                ))
                remaining -= fhsa_contribution
                rank += 1

        # Non-registered (remaining)
        if remaining > 0:
            recommendations.append(AccountRecommendation(
                rank=rank,
                account_type="Non-Registered",
                annual_amount=remaining,
                annual_limit=remaining,
                tax_benefit="taxable",
                tax_savings_estimate=Decimal("0"),
                reason=(
                    "After maxing registered accounts, non-registered investing "
                    "provides flexibility. Prioritize tax-efficient ETFs to minimize "
                    "annual distributions."
                ),
                action=f"Invest remaining ${remaining:,.0f} in a non-registered account. "
                       "Use broad-market ETFs with low turnover.",
                priority="low",
            ))
            remaining = Decimal("0")
            rank += 1

        # Cross-border alerts
        if AdvisorGoal.RELOCATION_US in goals:
            cross_border_alerts.append(
                "Planning to relocate to the US: RRSP can be kept and remains "
                "tax-deferred in the US under the US-CA tax treaty (Article XVIII). "
                "TFSA gains become taxable in the US — consider strategic withdrawals "
                "before departure or consult a cross-border CPA."
            )
            cross_border_alerts.append(self.tax.cross_border_rrsp_note())

        total_sheltered = sum(
            r.annual_amount for r in recommendations
            if r.account_type not in ("Non-Registered",)
        )
        total_tax_savings = sum(r.tax_savings_estimate for r in recommendations)

        return OptimizationResult(
            total_available_to_invest=annual_savings,
            total_tax_sheltered_capacity=total_sheltered,
            recommendations=recommendations,
            unallocated_amount=remaining,
            total_estimated_tax_savings=total_tax_savings,
            summary=self._ca_summary(recommendations, annual_savings, marginal),
            cross_border_alerts=cross_border_alerts,
        )

    def _optimize_usa(
        self,
        income, annual_savings, employment_type, visa_type, goals,
        age, year, tax_result, limits, state
    ) -> OptimizationResult:
        recommendations = []
        remaining = annual_savings
        rank = 1
        marginal = tax_result.marginal_rate
        cross_border_alerts = []

        k401_limit = limits.k401_limit or Decimal("0")
        ira_limit = limits.ira_limit or Decimal("0")

        # Roth IRA income phase-out check (simplified: < $161k single, < $240k MFJ)
        roth_eligible = income < Decimal("161000")

        # 1. 401(k) — primary pre-tax vehicle for employees
        if employment_type in (EmploymentType.EMPLOYEE.value, "employee"):
            k401_contribution = min(remaining, k401_limit)
            if k401_contribution > 0:
                tax_savings = k401_contribution * marginal
                recommendations.append(AccountRecommendation(
                    rank=rank,
                    account_type="401(k)",
                    annual_amount=k401_contribution,
                    annual_limit=k401_limit,
                    tax_benefit="pre-tax",
                    tax_savings_estimate=tax_savings,
                    reason=(
                        f"401(k) contributions reduce your taxable income at your "
                        f"{float(marginal*100):.1f}% marginal rate. "
                        "Many employers match — always capture the full match first."
                    ),
                    action=f"Contribute ${k401_contribution:,.0f} to your 401(k) "
                           f"(2025 limit: ${k401_limit:,.0f}). "
                           "Ensure you capture any employer match.",
                    priority="essential",
                ))
                remaining -= k401_contribution
                rank += 1
        elif employment_type in (EmploymentType.SELF_EMPLOYED.value, "self_employed",
                                  EmploymentType.CONTRACTOR.value, "contractor"):
            # Solo 401(k) or SEP-IRA for self-employed
            solo_limit = min(remaining, Decimal("69000"))  # 2025 solo 401k limit
            if solo_limit > 0:
                recommendations.append(AccountRecommendation(
                    rank=rank,
                    account_type="Solo 401(k) / SEP-IRA",
                    annual_amount=min(remaining, solo_limit),
                    annual_limit=solo_limit,
                    tax_benefit="pre-tax",
                    tax_savings_estimate=min(remaining, solo_limit) * marginal,
                    reason=(
                        "Self-employed workers can shelter significantly more via "
                        "Solo 401(k) (up to $69,000 for 2025, including employer contribution). "
                        "SEP-IRA is simpler to administer."
                    ),
                    action=f"Open a Solo 401(k) or SEP-IRA. Contribute up to "
                           f"${min(remaining, solo_limit):,.0f}.",
                    priority="essential",
                ))
                remaining -= min(remaining, solo_limit)
                rank += 1

        # 2. Roth IRA (if income-eligible)
        ira_contribution = min(remaining, ira_limit)
        if ira_contribution > 0:
            if roth_eligible:
                recommendations.append(AccountRecommendation(
                    rank=rank,
                    account_type="Roth IRA",
                    annual_amount=ira_contribution,
                    annual_limit=ira_limit,
                    tax_benefit="tax-free growth",
                    tax_savings_estimate=ira_contribution * Decimal("0.15"),
                    reason=(
                        "Roth IRA grows and is withdrawn tax-free. "
                        "Excellent for long-term wealth — especially valuable if you "
                        "expect higher taxes in retirement."
                    ),
                    action=f"Contribute ${ira_contribution:,.0f} to a Roth IRA "
                           f"(2025 limit: ${ira_limit:,.0f}).",
                    priority="high",
                ))
            else:
                recommendations.append(AccountRecommendation(
                    rank=rank,
                    account_type="Traditional IRA (Backdoor Roth)",
                    annual_amount=ira_contribution,
                    annual_limit=ira_limit,
                    tax_benefit="tax-deferred / backdoor Roth conversion",
                    tax_savings_estimate=Decimal("0"),
                    reason=(
                        "Income too high for direct Roth contribution. "
                        "Use the backdoor Roth strategy: contribute to non-deductible "
                        "Traditional IRA, then immediately convert to Roth."
                    ),
                    action=f"Execute backdoor Roth: contribute ${ira_contribution:,.0f} "
                           "to Traditional IRA (after-tax), then convert to Roth.",
                    priority="high",
                ))
            remaining -= ira_contribution
            rank += 1

        # 3. HSA if applicable (assume high-deductible health plan)
        hsa_limit = limits.hsa_individual or Decimal("4300")
        hsa_contribution = min(remaining, hsa_limit)
        if hsa_contribution > 0:
            recommendations.append(AccountRecommendation(
                rank=rank,
                account_type="HSA",
                annual_amount=hsa_contribution,
                annual_limit=hsa_limit,
                tax_benefit="triple tax-advantaged",
                tax_savings_estimate=hsa_contribution * marginal,
                reason=(
                    "HSA is the only triple tax-advantaged account: "
                    "contributions pre-tax, growth tax-free, withdrawals tax-free for medical. "
                    "After 65 you can withdraw for any purpose (like a Traditional IRA)."
                ),
                action=f"If on a HDHP, contribute ${hsa_contribution:,.0f} to your HSA.",
                priority="medium",
            ))
            remaining -= hsa_contribution
            rank += 1

        # 4. Taxable brokerage
        if remaining > 0:
            recommendations.append(AccountRecommendation(
                rank=rank,
                account_type="Taxable Brokerage",
                annual_amount=remaining,
                annual_limit=remaining,
                tax_benefit="taxable",
                tax_savings_estimate=Decimal("0"),
                reason=(
                    "After maxing tax-advantaged accounts, invest in a taxable brokerage. "
                    "Long-term capital gains rates are favorable (0–20%)."
                ),
                action=f"Invest remaining ${remaining:,.0f} in low-turnover, "
                       "tax-efficient index ETFs (VTI, VXUS).",
                priority="low",
            ))
            remaining = Decimal("0")
            rank += 1

        # Cross-border alerts for US residents with CA goals
        if AdvisorGoal.RELOCATION_CA in goals:
            cross_border_alerts.append(self.tax.roth_relocation_note())
            cross_border_alerts.append(
                "Maximize Roth IRA before relocating to Canada. "
                "Roth gains after becoming a Canadian resident may be taxable in Canada "
                "unless treaty elections are made annually (RC268)."
            )

        total_sheltered = sum(
            r.annual_amount for r in recommendations
            if r.account_type not in ("Taxable Brokerage",)
        )
        total_tax_savings = sum(r.tax_savings_estimate for r in recommendations)

        return OptimizationResult(
            total_available_to_invest=annual_savings,
            total_tax_sheltered_capacity=total_sheltered,
            recommendations=recommendations,
            unallocated_amount=remaining,
            total_estimated_tax_savings=total_tax_savings,
            summary=self._us_summary(recommendations, annual_savings, marginal),
            cross_border_alerts=cross_border_alerts,
        )

    def _optimize_generic(self, annual_savings: Decimal) -> OptimizationResult:
        return OptimizationResult(
            total_available_to_invest=annual_savings,
            total_tax_sheltered_capacity=Decimal("0"),
            recommendations=[
                AccountRecommendation(
                    rank=1,
                    account_type="General Investment Account",
                    annual_amount=annual_savings,
                    annual_limit=annual_savings,
                    tax_benefit="taxable",
                    tax_savings_estimate=Decimal("0"),
                    reason="No country-specific rules available. Invest in low-cost index funds.",
                    action="Invest in broadly diversified, low-cost index ETFs.",
                    priority="medium",
                )
            ],
            summary="Generic investment recommendation (no country-specific tax rules).",
        )

    def _ca_summary(
        self,
        recs: list[AccountRecommendation],
        total: Decimal,
        marginal: Decimal,
    ) -> str:
        sheltered = sum(r.annual_amount for r in recs if r.account_type != "Non-Registered")
        pct = (sheltered / total * 100) if total > 0 else Decimal("0")
        types = [r.account_type for r in recs if r.account_type != "Non-Registered"]
        return (
            f"${sheltered:,.0f} ({float(pct):.0f}%) of your annual savings can be sheltered "
            f"in tax-advantaged accounts ({', '.join(types)}). "
            f"At your {float(marginal*100):.1f}% marginal rate, this approach saves "
            f"approximately ${sum(r.tax_savings_estimate for r in recs):,.0f}/year in taxes."
        )

    def _us_summary(
        self,
        recs: list[AccountRecommendation],
        total: Decimal,
        marginal: Decimal,
    ) -> str:
        sheltered = sum(r.annual_amount for r in recs if r.account_type != "Taxable Brokerage")
        pct = (sheltered / total * 100) if total > 0 else Decimal("0")
        types = [r.account_type for r in recs if r.account_type != "Taxable Brokerage"]
        return (
            f"${sheltered:,.0f} ({float(pct):.0f}%) of your annual savings can be sheltered "
            f"via {', '.join(types)}. "
            f"Estimated annual tax savings: ${sum(r.tax_savings_estimate for r in recs):,.0f}."
        )
