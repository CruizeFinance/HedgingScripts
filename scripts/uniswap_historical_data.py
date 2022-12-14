from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from pprint import pprint
import pandas as pd

class UniswapHistoricalData(object):
    def __init__(self):
        self.aave_sub_graph_url = (
            "https://gateway.thegraph.com/api/884fed2091150d4d643b1415d340cfba/subgraphs/id/ELUcwgpm14LKPLrBRuVvPvNKHQ9HvwmtKgKSH6123cr7"
        )

    def fetch_sub_graph_query(self, liquidity_pool_id):
        sub_graph_query = """
            {
              liquidityPools(where: {id: "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"}) {
                name
                fees {
                  id
                  feeType
                  feePercentage
                }
                symbol
                totalValueLockedUSD
                cumulativeVolumeUSD
                cumulativeTotalRevenueUSD
                cumulativeSupplySideRevenueUSD
                cumulativeProtocolSideRevenueUSD
                swaps(where: {timestamp_gt: "1668408932"}) {
                  id
                  amountIn
                  amountInUSD
                  amountOut
                  amountOutUSD
                  tokenIn {
                    name
                    symbol
                  }
                  tokenOut {
                    name
                    symbol
                  }
                  timestamp
                }
              }
            }
        """
        return sub_graph_query

    def fetch_data(self, pool_id):
        graph = self.fetch_sub_graph_query(pool_id)
        query = gql(graph)
        transport = RequestsHTTPTransport(
            url=self.aave_sub_graph_url,
            verify=True,
            retries=3,
        )
        client = Client(transport=transport)

        response_dict = client.execute(query)
        return response_dict

    def create_csv(self, data):
        pprint(data)
        # Uncomment this to get pool data without swaps of that pool.
        historical_data = pd.DataFrame(
            data['liquidityPools'],
            columns=[
                "timestamp",
                "cumulativeProtocolSideRevenueUSD",
                "cumulativeSupplySideRevenueUSD",
                "cumulativeTotalRevenueUSD",
                "cumulativeVolumeUSD",
                "fees",
                "name",
            ],
        )
        historical_data.to_csv('/Users/prithvirajmurthy/Desktop/blockchain/cruize/scripts/scripts/Uniswap: {} Pool Data.csv'.format('ETH-USDC'))

        # Uncomment this to get swaps data of a certain Pool
        historical_swaps_data = pd.DataFrame(
            data['liquidityPools'][0]['swaps'],
            columns=[
                "id",
                "amountIn",
                "amountInUSD",
                "amountOut",
                "amountOutUSD",
                "timestamp",
                "tokenIn",
                "tokenOut",
            ],
        )
        historical_swaps_data.to_csv(
            '/Users/prithvirajmurthy/Desktop/blockchain/cruize/scripts/scripts/Uniswap {} Pool Swaps.csv'.format(
                'ETH-USDC'))


if __name__ == "__main__":
    a = UniswapHistoricalData()
    data = a.fetch_data(["0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"])
    a.create_csv(data)
