"""FIRE (Financial Independence, Retire Early) calculator.

Canopy - Personal Finance Platform

Provides:
- FIRE number calculation based on expenses and withdrawal rate
- Years to FIRE calculation with compound growth
- Net worth projections over time
- "What-if" scenario analysis
- Passive income projections
"""

import math
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from backend.services.insights_calculator import InsightsCalculator, DEFAULT_EXCHANGE_RATES


@dataclass
class FIREMetrics:
    """FIRE calculation results."""
    # Core metrics
    fire_number: Decimal  # Target net worth for FIRE
    current_net_worth: Decimal
    progress_percentage: Decimal  # How close to FIRE (%)
    
    # Timeline
    years_to_fire: Optional[float]  # Years until FIRE at current rate
    fire_date: Optional[date]  # Projected FIRE date
    
    # At FIRE
    monthly_income_at_fire: Decimal  # Safe withdrawal amount per month
    annual_income_at_fire: Decimal  # Safe withdrawal amount per year
    
    # Inputs used
    monthly_expenses: Decimal
    annual_expenses: Decimal
    safe_withdrawal_rate: Decimal  # e.g., 0.04 for 4%
    expected_return: Decimal  # e.g., 0.07 for 7%
    monthly_savings: Decimal


@dataclass
class ProjectionPoint:
    """A single point in a projection timeline."""
    year: int
    date: date
    net_worth: Decimal
    contributions: Decimal  # Cumulative contributions
    growth: Decimal  # Cumulative growth
    passive_income: Decimal  # Annual income at this net worth


@dataclass
class WhatIfScenario:
    """Results of a what-if scenario analysis."""
    name: str
    years_to_fire: Optional[float]
    fire_date: Optional[date]
    final_net_worth: Decimal
    difference_years: Optional[float]  # vs baseline


class FIRECalculator:
    """Calculator for FIRE planning and projections."""
    
    # Default values
    DEFAULT_SWR = Decimal("0.04")  # 4% safe withdrawal rate
    DEFAULT_RETURN = Decimal("0.07")  # 7% annual return
    DEFAULT_INFLATION = Decimal("0.025")  # 2.5% inflation
    
    def __init__(
        self,
        db: Optional[Session] = None,
        exchange_rates: Optional[dict[str, Decimal]] = None,
    ):
        self.db = db
        self.exchange_rates = exchange_rates or DEFAULT_EXCHANGE_RATES
    
    def _convert_to_usd(self, amount: Decimal, currency: str) -> Decimal:
        """Convert amount to USD."""
        if currency == "USD":
            return amount
        rate = self.exchange_rates.get(currency, Decimal("1"))
        return amount * rate
    
    def calculate_fire_number(
        self,
        annual_expenses: Decimal,
        safe_withdrawal_rate: Decimal = None,
    ) -> Decimal:
        """Calculate the FIRE number (target net worth).
        
        FIRE Number = Annual Expenses / Safe Withdrawal Rate
        
        Example: $43,200/year expenses / 0.04 SWR = $1,080,000 FIRE number
        """
        swr = safe_withdrawal_rate or self.DEFAULT_SWR
        if swr <= 0:
            return Decimal("0")
        return annual_expenses / swr
    
    def calculate_years_to_fire(
        self,
        current_net_worth: Decimal,
        fire_number: Decimal,
        monthly_savings: Decimal,
        annual_return: Decimal = None,
    ) -> Optional[float]:
        """Calculate years until reaching FIRE number.
        
        Uses the future value formula with regular contributions:
        FV = PV * (1 + r)^n + PMT * (((1 + r)^n - 1) / r)
        
        Solving for n requires numerical methods or logarithms.
        """
        if current_net_worth >= fire_number:
            return 0.0
        
        if monthly_savings <= 0 and current_net_worth <= 0:
            return None  # Can't reach FIRE
        
        annual_return = annual_return or self.DEFAULT_RETURN
        
        # Convert to monthly rate
        monthly_rate = float(annual_return) / 12
        
        # Use numerical approach
        current = float(current_net_worth)
        target = float(fire_number)
        monthly_contrib = float(monthly_savings)
        
        if monthly_rate == 0:
            # No growth, simple division
            if monthly_contrib <= 0:
                return None
            months = (target - current) / monthly_contrib
            return months / 12 if months > 0 else None
        
        # Iterative calculation
        months = 0
        max_months = 1200  # 100 years max
        
        while current < target and months < max_months:
            current = current * (1 + monthly_rate) + monthly_contrib
            months += 1
        
        if months >= max_months:
            return None  # Would take too long
        
        return months / 12
    
    def calculate_fire_metrics(
        self,
        current_net_worth: Decimal,
        monthly_expenses: Decimal,
        monthly_savings: Decimal,
        currency: str = "CAD",
        safe_withdrawal_rate: Decimal = None,
        expected_return: Decimal = None,
    ) -> FIREMetrics:
        """Calculate comprehensive FIRE metrics.
        
        Args:
            current_net_worth: Current total net worth
            monthly_expenses: Monthly living expenses
            monthly_savings: Monthly amount saved/invested
            currency: Currency of the expenses (will convert to USD)
            safe_withdrawal_rate: SWR (default 4%)
            expected_return: Expected annual return (default 7%)
        """
        swr = safe_withdrawal_rate or self.DEFAULT_SWR
        expected_return = expected_return or self.DEFAULT_RETURN
        
        # Convert to USD if needed
        monthly_expenses_usd = self._convert_to_usd(monthly_expenses, currency)
        monthly_savings_usd = self._convert_to_usd(monthly_savings, currency)
        
        annual_expenses = monthly_expenses_usd * 12
        
        # Calculate FIRE number
        fire_number = self.calculate_fire_number(annual_expenses, swr)
        
        # Calculate progress
        progress = (current_net_worth / fire_number * 100) if fire_number > 0 else Decimal("0")
        
        # Calculate years to FIRE
        years = self.calculate_years_to_fire(
            current_net_worth,
            fire_number,
            monthly_savings_usd,
            expected_return,
        )
        
        # Calculate FIRE date
        fire_date = None
        if years is not None:
            today = date.today()
            fire_date = date(
                today.year + int(years),
                today.month,
                today.day
            )
        
        # Income at FIRE
        annual_income = fire_number * swr
        monthly_income = annual_income / 12
        
        return FIREMetrics(
            fire_number=fire_number,
            current_net_worth=current_net_worth,
            progress_percentage=progress,
            years_to_fire=years,
            fire_date=fire_date,
            monthly_income_at_fire=monthly_income,
            annual_income_at_fire=annual_income,
            monthly_expenses=monthly_expenses_usd,
            annual_expenses=annual_expenses,
            safe_withdrawal_rate=swr,
            expected_return=expected_return,
            monthly_savings=monthly_savings_usd,
        )
    
    def project_net_worth(
        self,
        current_net_worth: Decimal,
        monthly_savings: Decimal,
        years: int = 30,
        annual_return: Decimal = None,
        safe_withdrawal_rate: Decimal = None,
    ) -> list[ProjectionPoint]:
        """Project net worth over time.
        
        Returns yearly data points for charting.
        """
        annual_return = annual_return or self.DEFAULT_RETURN
        swr = safe_withdrawal_rate or self.DEFAULT_SWR
        
        projections = []
        current = float(current_net_worth)
        cumulative_contributions = float(current_net_worth)
        monthly_rate = float(annual_return) / 12
        monthly_contrib = float(monthly_savings)
        
        today = date.today()
        
        for year in range(years + 1):
            # Calculate passive income at this net worth
            passive_income = Decimal(str(current)) * swr
            
            projections.append(ProjectionPoint(
                year=year,
                date=date(today.year + year, today.month, today.day),
                net_worth=Decimal(str(round(current, 2))),
                contributions=Decimal(str(round(cumulative_contributions, 2))),
                growth=Decimal(str(round(current - cumulative_contributions, 2))),
                passive_income=passive_income,
            ))
            
            # Project forward one year (12 months)
            for _ in range(12):
                current = current * (1 + monthly_rate) + monthly_contrib
                cumulative_contributions += monthly_contrib
        
        return projections
    
    def run_what_if_scenarios(
        self,
        current_net_worth: Decimal,
        monthly_expenses: Decimal,
        monthly_savings: Decimal,
        currency: str = "CAD",
    ) -> list[WhatIfScenario]:
        """Run common what-if scenarios.
        
        Compares:
        - Baseline
        - Increase savings by $500/month
        - Increase savings by $1000/month
        - Reduce expenses by 10%
        - Higher return (8% vs 7%)
        - Lower return (5% vs 7%)
        """
        monthly_expenses_usd = self._convert_to_usd(monthly_expenses, currency)
        monthly_savings_usd = self._convert_to_usd(monthly_savings, currency)
        annual_expenses = monthly_expenses_usd * 12
        fire_number = self.calculate_fire_number(annual_expenses)
        
        scenarios = []
        
        # Baseline
        baseline_years = self.calculate_years_to_fire(
            current_net_worth, fire_number, monthly_savings_usd
        )
        
        scenarios.append(WhatIfScenario(
            name="Baseline",
            years_to_fire=baseline_years,
            fire_date=self._years_to_date(baseline_years),
            final_net_worth=fire_number,
            difference_years=None,
        ))
        
        # Increase savings by $500/month
        years_500 = self.calculate_years_to_fire(
            current_net_worth, fire_number, monthly_savings_usd + Decimal("500")
        )
        scenarios.append(WhatIfScenario(
            name="Save $500 more/month",
            years_to_fire=years_500,
            fire_date=self._years_to_date(years_500),
            final_net_worth=fire_number,
            difference_years=self._diff_years(baseline_years, years_500),
        ))
        
        # Increase savings by $1000/month
        years_1000 = self.calculate_years_to_fire(
            current_net_worth, fire_number, monthly_savings_usd + Decimal("1000")
        )
        scenarios.append(WhatIfScenario(
            name="Save $1000 more/month",
            years_to_fire=years_1000,
            fire_date=self._years_to_date(years_1000),
            final_net_worth=fire_number,
            difference_years=self._diff_years(baseline_years, years_1000),
        ))
        
        # Reduce expenses by 10%
        reduced_expenses = annual_expenses * Decimal("0.9")
        reduced_fire = self.calculate_fire_number(reduced_expenses)
        years_reduced = self.calculate_years_to_fire(
            current_net_worth, reduced_fire, monthly_savings_usd
        )
        scenarios.append(WhatIfScenario(
            name="Reduce expenses 10%",
            years_to_fire=years_reduced,
            fire_date=self._years_to_date(years_reduced),
            final_net_worth=reduced_fire,
            difference_years=self._diff_years(baseline_years, years_reduced),
        ))
        
        # Higher return (8%)
        years_8pct = self.calculate_years_to_fire(
            current_net_worth, fire_number, monthly_savings_usd, Decimal("0.08")
        )
        scenarios.append(WhatIfScenario(
            name="8% annual return",
            years_to_fire=years_8pct,
            fire_date=self._years_to_date(years_8pct),
            final_net_worth=fire_number,
            difference_years=self._diff_years(baseline_years, years_8pct),
        ))
        
        # Lower return (5%)
        years_5pct = self.calculate_years_to_fire(
            current_net_worth, fire_number, monthly_savings_usd, Decimal("0.05")
        )
        scenarios.append(WhatIfScenario(
            name="5% annual return",
            years_to_fire=years_5pct,
            fire_date=self._years_to_date(years_5pct),
            final_net_worth=fire_number,
            difference_years=self._diff_years(baseline_years, years_5pct),
        ))
        
        return scenarios
    
    def _years_to_date(self, years: Optional[float]) -> Optional[date]:
        """Convert years from now to a date."""
        if years is None:
            return None
        today = date.today()
        return date(today.year + int(years), today.month, today.day)
    
    def _diff_years(self, baseline: Optional[float], new: Optional[float]) -> Optional[float]:
        """Calculate difference in years (negative = faster)."""
        if baseline is None or new is None:
            return None
        return new - baseline


def get_fire_summary(
    db: Session,
    monthly_expenses: Decimal = Decimal("5000"),  # Default: $5,000 CAD
    monthly_savings: Decimal = Decimal("2000"),  # Estimated savings
    currency: str = "CAD",
) -> dict:
    """Get a complete FIRE summary for the dashboard.
    
    Args:
        db: Database session
        monthly_expenses: Monthly living expenses
        monthly_savings: Monthly savings amount
        currency: Currency of expenses/savings
    """
    # Get current net worth
    insights_calc = InsightsCalculator(db)
    net_worth = insights_calc.calculate_net_worth()
    
    # Calculate FIRE metrics
    fire_calc = FIRECalculator(db)
    metrics = fire_calc.calculate_fire_metrics(
        current_net_worth=net_worth.net_worth_usd,
        monthly_expenses=monthly_expenses,
        monthly_savings=monthly_savings,
        currency=currency,
    )
    
    # Get projections (30 years)
    projections = fire_calc.project_net_worth(
        current_net_worth=net_worth.net_worth_usd,
        monthly_savings=fire_calc._convert_to_usd(monthly_savings, currency),
        years=30,
    )
    
    # Get what-if scenarios
    scenarios = fire_calc.run_what_if_scenarios(
        current_net_worth=net_worth.net_worth_usd,
        monthly_expenses=monthly_expenses,
        monthly_savings=monthly_savings,
        currency=currency,
    )
    
    return {
        "metrics": {
            "fire_number": float(metrics.fire_number),
            "current_net_worth": float(metrics.current_net_worth),
            "progress_percentage": float(metrics.progress_percentage),
            "years_to_fire": metrics.years_to_fire,
            "fire_date": metrics.fire_date.isoformat() if metrics.fire_date else None,
            "monthly_income_at_fire": float(metrics.monthly_income_at_fire),
            "annual_income_at_fire": float(metrics.annual_income_at_fire),
            "monthly_expenses": float(metrics.monthly_expenses),
            "annual_expenses": float(metrics.annual_expenses),
            "safe_withdrawal_rate": float(metrics.safe_withdrawal_rate),
            "expected_return": float(metrics.expected_return),
        },
        "projections": [
            {
                "year": p.year,
                "date": p.date.isoformat(),
                "net_worth": float(p.net_worth),
                "contributions": float(p.contributions),
                "growth": float(p.growth),
                "passive_income": float(p.passive_income),
            }
            for p in projections
        ],
        "scenarios": [
            {
                "name": s.name,
                "years_to_fire": s.years_to_fire,
                "fire_date": s.fire_date.isoformat() if s.fire_date else None,
                "final_net_worth": float(s.final_net_worth),
                "difference_years": s.difference_years,
            }
            for s in scenarios
        ],
    }
