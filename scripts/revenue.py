class Revenue(object):
    def __init__(
        self,
        cruize_price,
        staked_asset_price,
        dip_days,
        staked_eth_size,
        cover_pool,
        unit_price_of_asset,
        tuner=None,
    ):
        self.cruize_price = cruize_price
        self.staked_asset_price = staked_asset_price
        self.dip_days = dip_days
        self.staked_eth_size = staked_eth_size
        self.cover_pool = cover_pool
        self.unit_price_of_asset = unit_price_of_asset
        self.tuner = tuner

    def _adjust_tuner(self):
        if self.dip_days <= 90:
            self.tuner = 0.6
        elif 90 < self.dip_days <= 182:
            self.tuner = 0.8
        else:
            self.tuner = 1

    def calculate_revenue(self):
        if not self.tuner:
            self._adjust_tuner()
        price_floor = 0.85 * self.staked_asset_price * self.staked_eth_size
        print("PF: ", price_floor)
        users_eth_market_price = self.unit_price_of_asset * self.staked_eth_size
        print("UEMP: ", users_eth_market_price)
        price_difference = price_floor - users_eth_market_price
        print("PD: ", price_difference)
        fee_percentage = (
            (price_difference / (price_difference + (365 / self.dip_days)))
            * 100
            * self.tuner
        )

        fee = price_difference * (fee_percentage / 100)
        fee_percentage_on_price_difference = (fee / price_difference) * 100
        user_received = price_floor - fee
        # protocol_spent = user_received
        protocol_spent = user_received - self.unit_price_of_asset
        protocol_retained = price_floor - user_received
        current_cover_pool = self.cover_pool - protocol_spent

        revenue_data = {
            "protocol_retained_usdc": protocol_retained,
            "protocol_spent_usdc": protocol_spent,
            "user_received_usd": user_received,
            "user_fee_usd": fee,
            "fee_percentage_on_price_difference": fee_percentage_on_price_difference,
            "current_cover_pool_usdc": current_cover_pool,
        }
        return revenue_data


if __name__ == "__main__":
    from pprint import pprint

    r = Revenue(1, 100000, 15, 1, 100000, 65000)
    pprint(r.calculate_revenue())
