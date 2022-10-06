import pandas as pd
from dydx3 import Client as Client_dydx


class DydxClient(object):
    def __init__(self, config):
        self.dydx_margin_parameters = {}
        self.host = config["host"]
        self.client = Client_dydx(self.host)
        # self.dydx_instance = dydx_class

    def get_dydx_parameters(self, dydx_class_instance):
        # We bring the necessary parameters
        market = self.client.public.get_markets()
        dydx_info = pd.DataFrame.from_dict(market.data).T
        dydx_ETH_USD_data = dydx_info["ETH-USD"][0]
        self.dydx_margin_parameters["incrementalInitialMarginFraction"] = float(
            dydx_ETH_USD_data["incrementalInitialMarginFraction"]
        )

        self.dydx_margin_parameters["initialMarginFraction"] = float(
            dydx_ETH_USD_data["initialMarginFraction"]
        )
        self.dydx_margin_parameters["maintenanceMarginFraction"] = float(
            dydx_ETH_USD_data["maintenanceMarginFraction"]
        )
        self.dydx_margin_parameters["oraclePrice"] = float(
            dydx_ETH_USD_data["oraclePrice"]
        )
        self.dydx_margin_parameters["next_funding_at"] = dydx_ETH_USD_data[
            "nextFundingAt"
        ]
        self.dydx_margin_parameters["next_funding_rate"] = float(
            dydx_ETH_USD_data["nextFundingRate"]
        )

        # initial_margin_requirement
        self.dydx_margin_parameters["Initial_Margin_Requirement"] = abs(
            dydx_class_instance.short_size
            * self.dydx_margin_parameters["oraclePrice"]
            * self.dydx_margin_parameters["initialMarginFraction"]
        )
        self.dydx_margin_parameters[
            "Total_Initial_Margin_Requirement"
        ] = self.dydx_margin_parameters["Initial_Margin_Requirement"]

        # maintenance_margin_requirement
        self.dydx_margin_parameters["Maintenance_Margin_Requirement"] = abs(
            dydx_class_instance.short_size
            * self.dydx_margin_parameters["oraclePrice"]
            * self.dydx_margin_parameters["maintenanceMarginFraction"]
        )
        self.dydx_margin_parameters[
            "Total_Maintenance_Margin_Requirement"
        ] = self.dydx_margin_parameters["Maintenance_Margin_Requirement"]

        # total_account_value
        self.dydx_margin_parameters["total_account_value"] = (
                dydx_class_instance.short_collateral + dydx_class_instance.short_notional
        )
        self.dydx_margin_parameters["Free_collateral"] = (
            self.dydx_margin_parameters["total_account_value"]
            - self.dydx_margin_parameters["Total_Maintenance_Margin_Requirement"]
        )
        if self.dydx_margin_parameters["Total_Maintenance_Margin_Requirement"] != 0:
            self.dydx_margin_parameters[
                "liquidation_price"
            ] = self.dydx_margin_parameters["oraclePrice"] * (
                1
                + (
                    self.dydx_margin_parameters["maintenanceMarginFraction"]
                    * self.dydx_margin_parameters["total_account_value"]
                    / self.dydx_margin_parameters[
                        "Total_Maintenance_Margin_Requirement"
                    ]
                )
            )
        else:
            self.dydx_margin_parameters["liquidation_price"] = 0
