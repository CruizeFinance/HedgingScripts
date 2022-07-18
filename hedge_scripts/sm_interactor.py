import web3


class SmInteractor:
    def __init__(self, config):

        infura_node_as_http = config['infura_node_as_http']
        pool_address = config['pool_parameters']['pool_address']
        pool_abi = config['pool_parameters']['pool_abi']
        web3_provider = web3.Web3.HTTPProvider(infura_node_as_http)
        w3_object = web3.Web3(web3_provider)

        # Conectamos con los contratos
        self.pool_contract = w3_object.eth.contract(address=pool_address, abi=pool_abi)

        self.weth_address = config['weth_address']
        self.usdc_address = config['usdc_address']
        
    def get_rates(self):
        usdc_reserve_data = self.pool_contract.functions['getReserveData'](self.usdc_address).call()
        # usdc_liquidity_index = usdc_reserve_data[1] / 10 ** 18
        # usdc_variable_borrow_index = usdc_reserve_data[2] / 10 ** 18
        # usdc_liquidity_rate = usdc_reserve_data[3] / 10 ** 27
        usdc_variable_borrow_rate = usdc_reserve_data[4] / 10 ** 27
        usdc_stable_borrow_rate = usdc_reserve_data[5] / 10 ** 27
        weth_reserve_data = self.pool_contract.functions['getReserveData'](self.weth_address).call()
        # weth_liquidity_index = weth_reserve_data[1] / 10 ** 18
        # weth_variable_borrow_index = weth_reserve_data[2] / 10 ** 18
        # weth_liquidity_rate = weth_reserve_data[3] / 10 ** 27
        weth_variable_borrow_rate = weth_reserve_data[4] / 10 ** 27
        weth_stable_borrow_rate = weth_reserve_data[5] / 10 ** 27
        rates = {"usdc": {
            "borrow_rates": {
                "variable": usdc_variable_borrow_rate,
                "stable": usdc_stable_borrow_rate
            }},
            "weth": {
            "borrowing_rates": {
                "variable": weth_variable_borrow_rate,
                "stable": weth_stable_borrow_rate
            }}
        }
        return rates
