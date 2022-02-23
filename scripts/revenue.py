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
        trading_transaction_ratio=0.1,
        transactions=0,
        transactions_per_day=5,
    ):
        self.cruize_price = cruize_price
        self.staked_asset_price = staked_asset_price
        self.dip_days = dip_days
        self.staked_eth_size = staked_eth_size
        self.cover_pool = cover_pool
        self.unit_price_of_asset = unit_price_of_asset
        self.tuner = tuner
        self.trading_transaction_ratio = trading_transaction_ratio
        self.transactions = transactions
        self.transactions_per_day = transactions_per_day

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
        print("UEMP: ", self.unit_price_of_asset, users_eth_market_price)
        price_difference = price_floor - users_eth_market_price
        print("PD: ", price_difference)
        fee_percentage = (
            (price_difference / (price_difference + (365 / self.dip_days)))
            * 100
            * self.tuner
        )

        fee = price_difference * (fee_percentage / 100)
        fee_percentage_on_price_difference = (fee / price_difference) * 100
        user_received = price_floor
        # protocol_spent = user_received
        protocol_spent = user_received - self.unit_price_of_asset
        protocol_retained = price_floor - user_received
        current_cover_pool = self.cover_pool - protocol_spent

        fee_object = self.get_fee_data(
            required_fee=fee + price_difference,
            transactions_per_day=self.transactions_per_day,
            trading_transaction_ratio=self.trading_transaction_ratio,
        )
        revenue_data = {
            "protocol_retained_usdc": protocol_retained,
            "protocol_spent_usdc": protocol_spent,
            "user_received_usd": user_received,
            "fee_percentage_on_price_difference": fee_percentage_on_price_difference,
            "current_cover_pool_usdc": current_cover_pool,
        }
        revenue_data.update(fee_object)
        return revenue_data

    def get_fee_data(
        self,
        required_fee,
        eth_yield_apy=0.0366,
        trader_fee=0.003,
        trading_transaction_ratio=0.1,
        transactions=0,
        transactions_per_day=5,
    ):
        """
        @params:
        required_fee: Fee (to be accumulated via LP fees) that a user owes to the protocol.
        eth_yield_apy: Yield Generated on 1 unit of ETH on AAVE lending protocol
        trader_fee: 0.3% (0.003) is the optimal trader fee for trading on any open uniswap dex pool
        trading_transaction_ratio: The size of the transaction a trader is making from the dex pool.
            Eg: Trader extracts 100 cruize tokens out of the pool for trading purposes.
        transactions_per_day: Number of transactions occurring on the open dex pool
        apy_fee_ratio: %age of apy that the protocol takes as a fee.


        Logic:
        1. Specify a user_lp_size or users proportion in the open dex pool
        2. Specify a dex_pool size. As more users hedge and provide cruize-eth or cruize-usdc to the open dex pool,
            the dex pool size increases.
        3. Calculate user_portion_in_dex_pool based on the current pool size.
        4. Calculate trading_transaction_size (trading_transaction_ratio * dex_pool).
        5. Accumulate trader fee generated per transaction until the required_fee is accumulated.
            increment count of transactions to check how many transactions will be required.
        6. Calculate fee accumulated via the yield (apy_fee) generated on the users hedged asset.
        7. Calculate the total_fee_accumulated.
        8. Generate the required fee object and return it.

        returns: {'total_trading_fee_accumulated': 31.656510000047245,
                  'total_apy_fee_accumulated': 1.098,
                  'total_fee_accumulated': 32.75451000004725,
                  'transactions': 351739,
                  'days': 703.478}
        """
        # cr_yield_apy = 10 / 100
        # usdc_yield_apy = 15 / 100
        apy_fee_ratio = 10 / 100

        user_lp_size = self.staked_eth_size * self.staked_asset_price
        dex_pool = self.staked_eth_size * self.staked_asset_price * 50000
        user_portion_in_dex_pool = user_lp_size / dex_pool
        trading_transaction_size = dex_pool * trading_transaction_ratio

        total_trading_fee_accumulated = 0
        if not transactions or transactions == 0:
            while total_trading_fee_accumulated <= required_fee:
                total_trading_fee_accumulated += (
                    trading_transaction_size * trader_fee * user_portion_in_dex_pool
                )
                transactions += 1
        else:
            trading_fee_per_transaction = trading_transaction_size * trader_fee
            total_trading_fee_accumulated = transactions * trading_fee_per_transaction

        # Compute fee on hedged asset's APY
        apy = eth_yield_apy * self.staked_eth_size * self.staked_asset_price
        apy_fee = apy * apy_fee_ratio


        total_fee_accumulated = total_trading_fee_accumulated + apy_fee
        fee_object = {
            "total_trading_fee_accumulated": total_trading_fee_accumulated,
            "total_apy_fee_accumulated": apy_fee,
            "total_fee_accumulated": total_fee_accumulated,
            "transactions": transactions,
            "days": transactions / transactions_per_day,
        }
        return fee_object


if __name__ == "__main__":
    from pprint import pprint

    r = Revenue(
        cruize_price=1,
        staked_asset_price=100000,
        dip_days=15,
        staked_eth_size=1,
        cover_pool=100000,
        unit_price_of_asset=65000,
        tuner=0.1,
        trading_transaction_ratio=0.1,
        transactions_per_day=5,
    )
    pprint(r.calculate_revenue())
    # r.calculate_revenue_via_trader_fee()
