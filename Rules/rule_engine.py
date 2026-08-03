import pandas as pd

from basic_rules import *

class RuleEngine:

    def __init__(self):
        pass

    def apply(
        self,
        candidate: pd.DataFrame,
        product: dict,
        tonkho: pd.DataFrame,
        cham: pd.DataFrame,
    ) -> pd.DataFrame:

        candidate["score"] = 0.0

        rule_same_product(candidate)

        rule_empty_location(candidate)

        rule_replenishment(candidate, cham)

        rule_heavy_product(candidate, product)

        rule_large_volume(candidate, product)

        rule_short_expiry(candidate, product)

        rule_balance_day(candidate, tonkho)

        rule_same_category(candidate, product)

        return candidate