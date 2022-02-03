class SmartTreasury(object):
    def __init__(self, usdc_pool, cruize_pool, lp_usdc, cruize_price=1):
        self.usdc_pool = usdc_pool
        self.cruize_pool = cruize_pool
        self.cruize_price = cruize_price
        self.lp_usdc = lp_usdc

    def get_updated_treasury_distribution(self):
        cruize_removed = float(self.lp_usdc / self.cruize_price)
        self.cruize_pool -= cruize_removed
        total_pool_size = float(self.usdc_pool + (self.cruize_pool * self.cruize_price))
        updated_cruize_pool = float((0.8 * total_pool_size) / self.cruize_price)
        updated_usdc_pool = round(float(0.2 * total_pool_size))
        print("updated_usdc_pool: ", total_pool_size)

        adjusted_treasury = {
            "cruize_tokens": updated_cruize_pool,
            "usdc_tokens": updated_usdc_pool,
            "current_treasury_size": updated_cruize_pool + updated_usdc_pool,
            "lp_users_cruize": cruize_removed,
        }
        return adjusted_treasury


if __name__ == "__main__":
    smart_treasury = SmartTreasury(6000, 8000, 400, 4)
    print(smart_treasury.get_updated_treasury_distribution())
