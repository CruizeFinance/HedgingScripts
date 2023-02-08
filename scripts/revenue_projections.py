class RevenueProjection(object):

    # g_dai_tvl = 28000000
    # olive_tvl = 1000000
    # retail_tvl_month_1 = 500000
    tvls = [28000000, 3000000, 500000]

    def optimistic_revenue(self):
        total_tvl = sum(self.tvls)
        avg_twin_peaks_apy = 0.1 # 10%
        apy = total_tvl * avg_twin_peaks_apy
        apy_weekly = apy/52
        vault_revenue_weekly = apy_weekly * 0.1
        revenue_yealy = vault_revenue_weekly * 52
        print(vault_revenue_weekly)

if __name__ == '__main__':
    r = RevenueProjection()
    r.optimistic_revenue()