import edifice as ed
from edifice import Label, TextInput, View, Button, Dropdown, Window, ScrollView, Slider, Timer, CheckBox, IconButton
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
import json
import os
import csv
from multiprocessing.pool import ThreadPool
from time import sleep, localtime, strftime
import asyncio
import webbrowser


class MyApp(ed.Component):

    def __init__(self):
        super().__init__()
        self.column_style = {
            "width": 340,
            "height": 220
        }
        self.mission = "1"
        self.mission_alt = "1"
        self.selected_tier = "10x"
        self.slider_value = 0
        self.start = False
        self.hunter_stats = None
        self.first_load = Timer(lambda: self.first_load_func())
        self.balances = None
        self.gas_text = 0
        self.matic_price = 0
        self.retry = True
        self.retry_times = 5
        self.retry_times_style = {"width":20, "margin-left":3, "margin-right":3}
        self.mission_result = []
        self.info_dict = {}
        self.test = ""
        self.final_result = ""
        self.wrote_csv = False
        self.active_hunter = 0
        self.active_hunter_tier = 0
        self.play_highest = True
        self.play_highest_selected = True
        self.stop_playing = False
        self.mission_log = []
        self.session_log = []
        self.session_played = {"time":0, "total_played":0, "hunters_bought":0, "gpul_spent":0, "gbnt_earned":0, "f":0, "ms":0, "s":0, "gs":0}
        self.alive = False
        ####
        self.rpc_url = "https://polygon-rpc.com/"
        self.chainId = "0x89"
        self.router_address = Web3.toChecksumAddress("0xa5e0829caced8ffdd4de3c43696c57f7d7a678ff")
        self.router_abi = "PCS"
        ####
        filepath = os.path.join(os.path.realpath(os.getcwd()), "bins")
        self.filepath_sessions = os.path.join(os.path.realpath(os.getcwd()), "sessions")
        self.configFile = filepath + "\\config.json"
        self.pcsABI = filepath + "\\psc_abi.json"
        self.balanceABI = filepath + "\\balance_abi.json"
        self.bhABI = filepath + "\\bh_abi.json"
        self.missionsList = filepath + "\\missions_list.json"
        self.completedMissionsList = filepath + "\\completed_missions.json"
        self.missionCompleteABI = filepath + "\\mission_completed_abi.json"

        with open(self.configFile) as f:
            self.config = json.load(f)
        with open(self.pcsABI) as f:
            self.pcs_abi = json.load(f)
        with open(self.balanceABI) as f:
            self.balance_check_abi = json.load(f)
        with open(self.bhABI) as f:
            self.bh_abi = json.load(f)
        with open(self.missionsList) as f:
            self.missions_list = json.load(f)
        with open(self.completedMissionsList) as f:
            self.completed_missions = json.load(f)
        with open(self.missionCompleteABI) as f:
            self.mission_complete_abi = json.load(f)

        self.router_abi = self.pcs_abi

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer = 0)

        self.router_contract = self.w3.eth.contract(
            address=self.router_address, abi=self.router_abi)

        self.private_key = self.config["PRIVATE_KEY"]
        try:
            self.account = Account.from_key(self.private_key)
        except:
            self.account = None

        # Stablecoin address
        self.stable_address = Web3.toChecksumAddress(
            "0x2791bca1f2de4661ed88a30c99a7a9449aa84174")
        self.native_address = Web3.toChecksumAddress(
            "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270")

        self.gpul_address = Web3.toChecksumAddress(
            "0x40ed0565eCFB14eBCdFE972624ff2364933a8cE3")
        self.gbnt_address = Web3.toChecksumAddress(
            "0x8c9aaca6e712e2193acccbac1a024e09fb226e51")

        self.bh_address = Web3.toChecksumAddress(
            "0xB743285D3254C3c3Ad00338DC6464a75a8da5f51")
        self.bh_contract = self.w3.eth.contract(
            address=self.bh_address, abi=self.bh_abi)
        self.mission_complete_contract = self.w3.eth.contract(
            address=self.bh_address, abi=self.mission_complete_abi)

    def first_load_func(self):
        print("Started")
        hunter = self.get_hunter()
        balances = self.get_balances()
        matic_price = self.get_matic_price()
        self.first_load.stop()

        self.set_state(first_load=False, hunter_stats=hunter, balances=balances, matic_price=matic_price)

    async def get_stats(self):
        hunter = self.get_hunter()
        balances = self.get_balances()
        matic_price = self.get_matic_price()
        self.set_state(hunter_stats=hunter, balances=balances, matic_price=matic_price)

    async def start_playing(self, e):
        self.set_state(start=True)
        info_dict = self.info_dict
        hunter_id = info_dict['hunter_id']
        selected_tier = info_dict['selected_tier']
        mission_id = info_dict['mission_id']
        selected_mission_id = info_dict['selected_mission_id']
        gas_cost = info_dict['gas_cost']
        retry = info_dict['retry']
        start_time = strftime("%Y-%m-%d %H_%M", localtime())
        session_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
        label_style = {"width":200, "align":"top"}
        if not self.wrote_csv:
            with open(self.filepath_sessions + f"\\{start_time}.csv", 'a', newline='') as c:
                writer = csv.writer(c)
                headers = ['date', 'mission number', 'result', 'gpul spent', 'gbnt earned']
                writer.writerow(headers)
            self.set_state(wrote_csv=True)
        count = 1
        session_log = []
        session_played = {"time":session_time, "total_played":0, "hunters_bought":0, "gpul_spent":0, "gbnt_earned":0, "f":0, "ms":0, "s":0, "gs":0}
        self.set_state(session_played=session_played)
        while True:
            result_list = []
            if not self.alive:
                self.set_state(alive=False)
                buy_new_label = Label("Buying new hunter...", style=label_style)
                result_list.append(buy_new_label)
                session_log.append(buy_new_label)
                self.set_state(mission_result=result_list, session_log=session_log)
                hunter_id = await self.buy_new_hunter(selected_tier, gas_cost, True)
                if retry:
                    hunter_retry_count = 0
                    while type(hunter_id) is str:
                        hunter_retry_count += 1
                        result_list.append(Label(f"Failed to buy hunter! Retrying... ({hunter_retry_count} of {int(self.retry_times)})", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                        session_log.append(Label(f"Failed to buy hunter! Retrying... ({hunter_retry_count} of {int(self.retry_times)})", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                        self.set_state(mission_result=result_list, session_log=session_log)
                        hunter_id = await self.buy_new_hunter(selected_tier, gas_cost, True)
                        await asyncio.sleep(2)
                        if hunter_retry_count == self.retry_times:
                            result_list.append(Label(f"Maximum retries reached, stopping!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                            session_log.append(Label(f"Maximum retries reached, stopping!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                            return
                elif not retry and type(hunter_id) is str:
                    result_list.append(Label(f"Failed to buy hunter! Stopping!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                    session_log.append(Label(f"Failed to buy hunter! Stopping!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                    self.set_state(mission_result=result_list, session_log=session_log)
                    return
                result_list.append(Label(f"Hunter bought! ID: {hunter_id}", style=label_style))
                result_list.append(Label("\n"))
                session_log.append(Label(f"Hunter bought! ID: {hunter_id}", style=label_style))
                session_log.append(Label("\n"))
                session_played['hunters_bought'] += 1
                self.set_state(mission_result=result_list, session_log=session_log, active_hunter=hunter_id, alive=True,
                               session_played=session_played)
            else:
                self.set_state(alive=True)
                self.set_state(active_hunter=hunter_id)
            active_hunter = self.bh_contract.functions.getHunterById(self.active_hunter).call()
            active_tier = active_hunter[1]
            for i in range(1, 13):
                can_play = self.bh_contract.functions.canPlay(int(self.active_hunter), int(i))
                if can_play:
                    highest_mission = i
                else:
                    pass
            if active_tier != selected_tier:
                if self.play_highest:
                    mission_id = highest_mission
                elif mission_id <= highest_mission:
                    mission_id = mission_id
                else:
                    mission_id = highest_mission
            else:
                if self.play_highest_selected:
                    mission_id = highest_mission
                elif selected_mission_id <= highest_mission:
                    mission_id = selected_mission_id
                else:
                    mission_id = highest_mission

            balances = self.get_balances()
            balance_get_count = 0
            while balances[0] == 0 and balance_get_count < 5:
                balances = self.get_balances()
                balance_get_count += 1
                await asyncio.sleep(1)
            gpul = balances[0]
            matic = balances[2]
            if float(gpul) < self.completed_missions[f"{mission_id}"]:
                result_list.append(Label(f"Not enough GPUL to play!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                session_log.append(Label(f"Not enough GPUL to play!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                self.set_state(mission_result=result_list, session_log=session_log)
                break
            if float(matic) < float(gas_cost):
                result_list.append(Label(f"Not enough MATIC to play!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                session_log.append(Label(f"Not enough MATIC to play!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                self.set_state(mission_result=result_list, session_log=session_log)
                break
            await asyncio.sleep(3)
            result_list.append(Label(f"Starting mission! ({count})", style=label_style))
            session_log.append(Label(f"Starting mission! ({count})", style=label_style))
            self.set_state(mission_result=result_list, session_log=session_log)
            mission = await self.sendHunterForMission(self.active_hunter, mission_id, gas_cost, True)
            if retry:
                mission_retry_count = 0
                while type(mission) is str:
                    mission_retry_count += 1
                    result_list.append(Label(f"Failed to start mission! Retrying...", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                    session_log.append(Label(f"Failed to start mission! Retrying...", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                    self.set_state(mission_result=result_list, session_log=session_log)
                    mission = await self.sendHunterForMission(self.active_hunter, mission_id, gas_cost, True)
                    await asyncio.sleep(2)
                    if mission_retry_count == self.retry_times:
                        result_list.append(Label(f"Maximum retries reached, stopping!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                        session_log.append(Label(f"Maximum retries reached, stopping!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                        return
            elif not retry and type(mission) is str:
                result_list.append(Label(f"Failed to start mission! Stopping!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                session_log.append(Label(f"Failed to start mission! Stopping!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                self.set_state(mission_result=result_list, session_log=session_log)
                return
            mission_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
            result_list.append(Label(f"Mission in progress...", style=label_style))
            session_log.append(Label(f"Mission in progress...", style=label_style))
            self.set_state(mission_result=result_list, session_log=session_log)
            await asyncio.sleep(0.3)
            await self.track_mission_progress(hunter_id)
            mission_result = self.final_result
            log = mission_result['logs'][2]
            processed_log = self.mission_complete_contract.events['MissionCompleted']().processLog(log)
            result = processed_log['args']['result']
            completed_mission_id = processed_log['args']['mission']
            if result == 1:
                reward_mult = 0
                result_list.append(Label(f"Mission Failed! Hunter has died.", style=[label_style, {'color':"rgba(249, 31, 31, 0.84)"}]))
                result_list.append(Label("\n"))
                session_log.append(Label(f"Mission Failed! Hunter has died.", style=[label_style, {'color':"rgba(249, 31, 31, 0.84)"}]))
                session_log.append(Label("\n"))
                session_played['f'] += 1
                self.set_state(mission_result=result_list, session_log=session_log, alive=False)
            elif result == 2:
                reward_mult = 0.5
                result_list.append(Label(f"Mediocre success.", style=[label_style, {'color':"rgba(5, 192, 5, 0.44)"}]))
                result_list.append(Label("\n"))
                session_log.append(Label(f"Mediocre success.", style=[label_style, {'color':"rgba(5, 192, 5, 0.44)"}]))
                session_log.append(Label("\n"))
                session_played['ms'] += 1
                self.set_state(mission_result=result_list, session_log=session_log)
            elif result == 3:
                reward_mult = 1
                result_list.append(Label(f"Success.", style=[label_style, {'color':"rgba(5, 192, 5, 0.64)"}]))
                result_list.append(Label("\n"))
                session_log.append(Label(f"Success.", style=[label_style, {'color':"rgba(5, 192, 5, 0.64)"}]))
                session_log.append(Label("\n"))
                session_played['s'] += 1
                self.set_state(mission_result=result_list, session_log=session_log)
            else:
                reward_mult = 2
                result_list.append(Label(f"Great success!", style=[label_style, {'color':"rgba(5, 192, 5, 0.84)"}]))
                result_list.append(Label("\n"))
                session_log.append(Label(f"Great success!", style=[label_style, {'color':"rgba(5, 192, 5, 0.84)"}]))
                session_log.append(Label("\n"))
                session_played['gs'] += 1
                self.set_state(mission_result=result_list, session_log=session_log)

            with open(self.filepath_sessions + f"\\{start_time}.csv", 'a', newline='') as c:
                gpul_spent = self.completed_missions[f"{completed_mission_id}"]
                gbnt_earned = float(gpul_spent) * float(reward_mult) * 0.92
                writer = csv.writer(c)
                row = [mission_time, count, result, gpul_spent, gbnt_earned]
                writer.writerow(row)
                session_played['gpul_spent'] += float(gpul_spent)
                session_played['gbnt_earned'] += float(gbnt_earned)
                session_played['total_played'] += 1
                self.set_state(session_played=session_played)

            if self.stop_playing:
                result_list.append(Label(f"Stopped!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                session_log.append(Label(f"Stopped!", style=[label_style, {'color':"rgba(249, 31, 31, 0.58)"}]))
                self.set_state(mission_result=result_list, session_log=session_log, stop_playing=False)
                break
            count += 1
            await asyncio.sleep(1)

        await self.get_stats()

    def get_hunter(self):
        user_stats = self.bh_contract.functions.getUserByAddress(self.account.address).call()
        token_id = user_stats[0]
        hunter_stats = self.bh_contract.functions.getHunterById(token_id).call()
        tier = hunter_stats[1]
        level = hunter_stats[2]
        mission_success = hunter_stats[12]
        rarity = hunter_stats[3]
        tier_rarity = {}
        for i in range(1, 4):
            if tier == i:
                tier_rarity["active"] = rarity
            else:
                xp_for_type = self.bh_contract.functions.exHuntersXpByType(self.account.address, i).call()
                if xp_for_type < 3750:
                    tier_rarity[i] = 1
                elif xp_for_type < 11250:
                    tier_rarity[i] = 2
                elif xp_for_type < 22500:
                    tier_rarity[i] = 3
                elif xp_for_type >= 22500:
                    tier_rarity[i] = 4

        if tier == 1:
            tier = "10x"
        elif tier == 2:
            tier = "50x"
        elif tier == 3:
            tier = "100x"

        return {"id":token_id, "tier": tier, "level": level, "rarity": tier_rarity, "mission_success": mission_success}

    def get_matic_price(self):
        amount_in = Web3.toWei(1, 'ether')
        # Get current price of BNB in USDC
        usdc_out = self.router_contract.functions.getAmountsOut(
            amount_in, [self.native_address, self.stable_address]).call()[1]
        usdc_out = Web3.fromWei(usdc_out, "mwei")
        matic_price = "{:0.4f}".format(usdc_out)

        return matic_price

    async def stop_play(self, e):
        result_list = self.mission_result
        session_log = self.session_log
        if not self.stop_playing:
            self.set_state(stop_playing=True)
            result_list.append(Label(f"Stopping after current action...", style={'width':200, 'color':"rgba(249, 31, 31, 0.58)"}))
            session_log.append(Label(f"Stopping after current action...", style={'width':200, 'color':"rgba(249, 31, 31, 0.58)"}))
            self.set_state(mission_result=result_list, session_log=session_log)

    async def sendHunterForMission(self, hunter_id, mission_id, gas_cost, send):
        if send:
            max_gas = self.w3.toWei(float(gas_cost) / 800000, "ether")
            #if max_gas < 32000000000:
            #    max_gas = 32000000000

            play_mission_abi = self.bh_contract.encodeABI('sendHunterForMission',
                                                          args=(int(hunter_id), int(mission_id)))

            rawTransaction = {
                "from": self.account.address,
                "to": self.bh_address,
                "nonce": Web3.toHex(self.w3.eth.getTransactionCount(self.account.address)),
                'gas': 800000,
                'maxFeePerGas': self.w3.toHex(max_gas),
                'maxPriorityFeePerGas': self.w3.toHex(max_gas),
                "data": play_mission_abi,
                "chainId": self.chainId,
            }
            signed_txn = self.w3.eth.account.sign_transaction(rawTransaction, self.private_key)
            try:
                raw_txn_sent = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            except:
                return "Transaction failed to send"
            await asyncio.sleep(0.1)
            txn_receipt = self.w3.eth.wait_for_transaction_receipt(raw_txn_sent, timeout=60)
            print("txn receipt", txn_receipt)
            if not txn_receipt["status"] == 1:
                return "Transaction failed on the blockchain"
            return hunter_id

        else:
            return False

    def transaction_loop(self, block, sleep_interval):
        while True:
            try:
                transactions = self.w3.eth.get_block(block)['transactions']
                for i in transactions:
                    txn = self.w3.toHex(i)
                    receipt = self.w3.eth.get_transaction_receipt(txn)
                    if receipt['logs'][0]['address'] == self.bh_address:
                        self.set_state(final_result=receipt)
                        break
                    else:
                        pass
                return None
            except:
                pass
            sleep(sleep_interval)

    async def track_mission_progress(self, hunter_id=0):
        progress_count = 0
        while True:
            in_progress = self.bh_contract.functions.hunterInMission(hunter_id, self.account.address).call()
            if in_progress == 0:
                if progress_count < 10:
                    progress_count += 1
                else:
                    break
            await asyncio.sleep(1)

        start_block = self.w3.eth.get_block_number()
        results = []
        pool = ThreadPool(processes=10)
        for count in range(-8, 40):
            block = start_block+count
            result = pool.apply_async(self.transaction_loop, (block, 0.1))
            results.append(result)

        while type(self.final_result) is str:
            await asyncio.sleep(1)

        return

    async def buy_new_hunter(self, hunter_tier, gas_cost, send):
        if send:
            max_gas = self.w3.toWei(float(gas_cost) / 800000, "ether")
            if hunter_tier == "10x":
                hunter_tier = 1
            elif hunter_tier == "50x":
                hunter_tier = 2
            elif hunter_tier == "100x":
                hunter_tier = 3
            buy_hunter_abi = self.bh_contract.encodeABI('buyToken',
                                                        args=[int(hunter_tier)])
            rawTransaction = {
                "from": self.account.address,
                "to": self.bh_address,
                "nonce": Web3.toHex(self.w3.eth.getTransactionCount(self.account.address)),
                'gas': 800000,
                'maxFeePerGas': self.w3.toHex(max_gas),
                'maxPriorityFeePerGas': self.w3.toHex(max_gas),
                "data": buy_hunter_abi,
                "chainId": self.chainId,
            }
            try:
                signed_txn = self.w3.eth.account.sign_transaction(rawTransaction, self.private_key)
                raw_txn_sent = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                txn_receipt = self.w3.eth.wait_for_transaction_receipt(raw_txn_sent, timeout=240)
            except:
                return "Transaction failed on the blockchain"
            print("txn receipt", txn_receipt)
            if not txn_receipt["status"] == 1:
                return "Transaction failed on the blockchain"
            token_id = 0
            while token_id == 0:
                user_stats = self.bh_contract.functions.getUserByAddress(self.account.address).call()
                token_id = user_stats[0]
            return token_id
        else:
            return True

    def get_balances(self):
        # GPUL #
        balance_check_gpul = self.w3.eth.contract(
            address=self.gpul_address, abi=self.balance_check_abi)
        gpul_balance = balance_check_gpul.functions.balanceOf(self.account.address).call({'from': self.gpul_address})
        gpul_balance = Web3.fromWei(gpul_balance, "ether")
        gpul_balance = "{:0.2f}".format(gpul_balance)

        # GBNT #
        balance_check_gbnt = self.w3.eth.contract(
            address=self.gbnt_address, abi=self.balance_check_abi)
        gbnt_balance = balance_check_gbnt.functions.balanceOf(self.account.address).call({'from': self.gbnt_address})
        gbnt_balance = Web3.fromWei(gbnt_balance, "ether")
        gbnt_balance = "{:0.2f}".format(gbnt_balance)

        # MATIC #
        matic_balance = self.w3.eth.getBalance(self.account.address)
        matic_balance = Web3.fromWei(matic_balance, "ether")
        matic_balance = "{:0.2f}".format(matic_balance)

        return [gpul_balance, gbnt_balance, matic_balance]

    def render(self):
        if self.first_load is not False and self.account:
            self.first_load.start(100)
        hunter_stats = self.hunter_stats
        column_style = {
            "width": 340,
            "height": 180,
            "align": "top"
        }
        if hunter_stats is None:
            sleep(1)
            hunter_id = 0
            hunter_tier = "10x"
            hunter_level = 0
            hunter_rarity = 1
            hunter_success = 0
            balances = [0, 0, 0]
            matic_price = 0
            rarity_dict = {}
            selected_mission_id = 1
            mission_id = 1
            play_cost = 0
            max_plays = 0
            alive = False
        else:
            hunter_id = hunter_stats['id']
            hunter_tier = hunter_stats['tier']
            hunter_level = hunter_stats['level']
            rarity_dict = hunter_stats['rarity']
            try:
                hunter_rarity = rarity_dict['active']
                alive = True
            except KeyError:
                hunter_rarity = 1
                hunter_tier = "10x"
                alive = False
            hunter_success = hunter_stats['mission_success']
            selected_mission_id = 1
            balances = self.balances
            matic_price = self.matic_price

        available_missions_active = ["1. Eradicate Space Bugs","2. Take Down the Drug Cartel","3. Search And Rescue","4. Steal Artifact"]
        del available_missions_active[int(hunter_rarity):5]

        for i in range(1, hunter_rarity+1):
            if str(i) in self.mission:
                mission = self.missions_list[0][f"MISSION_{i}"][0]
                if hunter_tier == "10x":
                    mission_id = mission['IDs'][0]
                elif hunter_tier == "50x":
                    mission_id = mission['IDs'][1]
                elif hunter_tier == "100x":
                    mission_id = mission['IDs'][2]
                try:
                    multiplier = int(hunter_tier.split("x")[0]) / 10
                except AttributeError:
                    multiplier = 1
                play_cost = int(mission["PRICE"])*multiplier
                max_plays = float(balances[0])//float(play_cost)

        if self.slider_value > max_plays:
            self.set_state(slider_value=0)

        if alive:
            if max_plays > 0:
                column_style['height'] = int(column_style['height'])+90
            if not self.alive:
                self.set_state(alive=True)
            if self.selected_tier != hunter_tier:
                active_mission_label = Label(f"Select Mission ({hunter_tier}):", style={"margin-left": 5, "width":115})
            else:
                active_mission_label = Label(f"Select Mission:", style={"margin-left": 5, "width":80})
            if self.play_highest:
                active_mission_selection = CheckBox(checked=self.play_highest, text="Always play highest available mission.",
                                                    on_click=lambda e: self.set_state(play_highest=not self.play_highest))
            else:
                active_mission_selection = View(layout="column")(
                    Dropdown(options=available_missions_active,
                            style={"width": 170}, on_select=lambda e: self.set_state(mission=e)),
                    CheckBox(checked=self.play_highest, text="Always play highest available mission.",
                             on_click=lambda e: self.set_state(play_highest=not self.play_highest))
                )
                column_style['height'] = int(column_style['height'])+20
            hunter_status = Label("Alive!", style={"color":"green", "font-weight":500, "font-size":12})
            available_missions_active_row = View(layout="row", style={"align": "top", "margin-left": 10, "margin-top":5})(
                active_mission_label,
                active_mission_selection
            )
        if not alive:
            hunter_status = Label("Dead!", style={"color":"red", "font-weight":500, "font-size":12})
            hunter_tier = "None"
            available_missions_active_row = ""

        if hunter_tier == self.selected_tier:
            tier_label = ""
            available_missions_row = ""

        elif hunter_tier != self.selected_tier:
            if not alive:
                tier_label = View(layout="row", style={"margin-left":10, "background-color":"rgb(255, 251, 219)",
                                                       "border-top":"1px solid orange", "border-bottom":"1px solid orange"})(
                    Label(f'Your hunter is dead!\n'
                          f'The selected tier ({self.selected_tier}) will be bought.', style={"margin":5, "font-size":10}))
            else:
                tier_label = View(layout="row", style={"margin-left":10, "background-color":"rgb(255, 251, 219)",
                                                       "border-top":"1px solid orange", "border-bottom":"1px solid orange"})(
                    Label(f'Selected Hunter Tier is different than current active hunter!\n'
                          f'On next death, selected tier ({self.selected_tier}) will be bought.', style={"margin":5, "font-size":10}))
            column_style['height'] = int(column_style['height'])+60

            tier_list = ["10x", "50x", "100x"]

            for i in tier_list:
                if i == self.selected_tier:
                    try:
                        selected_rarity = rarity_dict[tier_list.index(i)+1]
                    except KeyError:
                        selected_rarity = 1


            for i in range(1, selected_rarity+1):
                if str(i) in self.mission_alt:
                    selected_mission = self.missions_list[0][f"MISSION_{i}"][0]
                    if self.selected_tier == "10x":
                        selected_mission_id = selected_mission['IDs'][0]
                    elif self.selected_tier == "50x":
                        selected_mission_id = selected_mission['IDs'][1]
                    elif self.selected_tier == "100x":
                        selected_mission_id = selected_mission['IDs'][2]
                    selected_multiplier = int(self.selected_tier.split("x")[0]) / 10
                    selected_play_cost = int(selected_mission["PRICE"])*selected_multiplier
                    selected_max_plays = float(balances[0])//float(selected_play_cost)

            available_missions_selected = ["1. Eradicate Space Bugs", "2. Take Down the Drug Cartel", "3. Search And Rescue", "4. Steal Artifact"]
            del available_missions_selected[int(selected_rarity):5]

            if self.play_highest_selected:
                mission_selection = CheckBox(checked=self.play_highest_selected, text="Always play highest available mission.",
                                                    on_click=lambda e: self.set_state(play_highest_selected=not self.play_highest_selected))
            else:
                mission_selection = View(layout="column")(
                    Dropdown(options=available_missions_selected,
                             style={"width": 170}, on_select=lambda e: self.set_state(mission_alt=e)),
                    CheckBox(checked=self.play_highest_selected, text="Always play highest available mission.",
                             on_click=lambda e: self.set_state(play_highest_selected=not self.play_highest_selected))
                )
                column_style['height'] = int(column_style['height'])+20

            available_missions_row = View(layout="row", style={"align": "top", "margin-left": 10, "margin-top":5})(
                Label(f"Select Mission ({self.selected_tier}):", style={"margin-left": 5, "width":115}),
                mission_selection,
            )
            if self.mission_alt not in available_missions_selected:
                try:
                    self.set_state(mission_alt="1. Eradicate Space Bugs")
                except AttributeError:
                    pass

        if self.start:
            start_window = Window(title="Mission Stats", on_close=lambda e: self.set_state(start=False, wrote_csv=False))(
                View(layout="column", style={"align":"top", "width":320, "border":"1px solid"})(
                    Label("Session Stats", style={"align":"center", "font-size":15, "border":"1px solid"}),
                    View(layout="column", style={"align":"center"})(
                        Label(f"Time started: {self.session_played['time']}", style={"align":"center", "margin":4, "font-size":12}),
                        View(layout="row", style={"align":"center"})(
                            View(layout="column", style={"width":110, "border":"1px solid gray"})(
                                Label(f"Missions played: {self.session_played['total_played']}", style={"margin-top":3, "font-size":11}),
                                Label(f"Hunters bought: {self.session_played['hunters_bought']}", style={"margin-top":3, "font-size":11}),
                                Label(f"GPUL spent: {self.session_played['gpul_spent']}", style={"margin-top":3, "font-size":11}),
                                Label(f"GBNT earned: {self.session_played['gbnt_earned']}", style={"margin-top":3, "font-size":11})
                            ),
                            Label("", style={"margin-left":5, "margin-right":5}),
                            View(layout="column", style={"width":110, "border":"1px solid gray"})(
                                Label(f"Failed: {self.session_played['f']}", style={"margin-top":3, "font-size":11}),
                                Label(f"Mediocre success: {self.session_played['ms']}", style={"margin-top":3, "font-size":11}),
                                Label(f"Success: {self.session_played['s']}", style={"margin-top":3, "font-size":11}),
                                Label(f"Great success: {self.session_played['gs']}", style={"margin-top":3, "font-size":11})
                            ),
                        ),
                        Label("Current Status:", style={"margin-top":10, "align":"center", "font-size":14, "border":"1px solid"}),
                        ScrollView(layout="column", style={"align":"top", "height":70, "width":240})(self.mission_result),
                        Label("Mission Log:", style={"align":"center", "font-size":14, "border":"1px solid"}),
                        ScrollView(layout="column", style={"align":"top", "margin":5, "height":140, "width":240})(self.session_log),
                        Button(title="STOP", on_click=self.stop_play)
                    )
                )
            )
        elif not self.start:
            start_window = ""

        try:
            float(self.gas_text)
            gas_text = str(self.gas_text)
            matic_input = {"align":"top", "margin-right": 5, "width":90}
            matic_cost = f"{int(self.slider_value)*float(gas_text)}"
        except ValueError:
            gas_text = self.gas_text
            matic_input = {"align":"top", "margin-right": 5, "background-color": "rgb(255, 209, 209)", "width":90}
            matic_cost = 0
            start_button = Button(f"Invalid gas input!", style={"width":338, "height":30})

        info_dict = {"alive": alive,
                     "mission_id": mission_id,
                     "selected_mission_id": selected_mission_id,
                     "hunter_id": hunter_id,
                     "gas_cost": gas_text,
                     "hunter_tier": hunter_tier,
                     "selected_tier": self.selected_tier,
                     "retry": self.retry,
                     "mission_amount": self.slider_value}

        if self.info_dict != info_dict:
            try:
                self.set_state(info_dict=info_dict)
            except AttributeError:
                pass

        if matic_cost != 0:
            start_button = Button(f"START", style={"width":338, "height":30}, on_click=self.start_playing)

        if float(matic_cost) > float(balances[2]):
            start_button = Button(f"Not enough MATIC for gas!", style={"width":338, "height":30})

        if not alive:
            try:
                max_plays = selected_max_plays
            except UnboundLocalError:
                max_plays = 0
        if max_plays == 0:
            slider = ""
            start_button = Button(f"Not enough GPUL to play this mission!", style={"width":338, "height":30})
        elif max_plays > 0:
            total_gpul = int(self.slider_value)*int(play_cost)
            times_to_play = int(self.slider_value)
            if self.selected_tier != hunter_tier:
                if hunter_tier == "None":
                    slider_or_text = [Slider(value=self.slider_value, min_value=0, tool_tip=str(self.slider_value), max_value=max_plays,
                                             dtype=int, style={"min-width":110, "width":110, "height":20}, on_change=lambda e: self.set_state(slider_value=e)),
                                      Button("MAX", style={"margin-left":5, "width":37, "height":20}, on_click=lambda e: self.set_state(slider_value=max_plays))
                                      ]
                    total_matic = Label(f"Total MATIC cost: {'{:0.4f}'.format(float(matic_cost))}", style={"margin-top":5, "width":150})
                    total_matic_usd = Label(f"(${'{:0.2f}'.format(float(matic_cost)*float(matic_price))})", style={"font-size":10,"width":150})
                    column_style['height'] = int(column_style['height'])+65
                else:
                    max_plays = selected_max_plays
                    times_to_play = "?"
                    if self.slider_value > max_plays:
                        self.set_state(slider_value=selected_max_plays)
                    if not alive:
                        total_gpul = int(self.slider_value)*int(selected_play_cost)
                        times_to_play = int(self.slider_value)
                    else:
                        total_gpul = "?"
                    slider_or_text = Label("Will play as many as possible based on available GPUL and MATIC.\n"
                                           "Hard to estimate due to not knowing amount of deaths needed "
                                           "for new hunter purchase.", style={"font-size":10, "background-color":"rgb(255, 251, 219)",
                                                                              "border":"1px solid orange"})
                    total_matic = Label("Will stop if you run out of MATIC to pay for new hunters or missions.", style={"font-size":10, "background-color":"rgb(255, 251, 219)",
                                                                           "border":"1px solid orange"})
                    total_matic_usd = ""
                    column_style['height'] = int(column_style['height'])+55
            else:
                slider_or_text = [Slider(value=self.slider_value, min_value=0, tool_tip=str(self.slider_value), max_value=max_plays,
                                        dtype=int, style={"min-width":110, "width":110, "height":20}, on_change=lambda e: self.set_state(slider_value=e)),
                                  Button("MAX", style={"margin-left":5, "width":37, "height":20}, on_click=lambda e: self.set_state(slider_value=max_plays))
                                  ]
                total_matic = Label(f"Total MATIC cost: {'{:0.4f}'.format(float(matic_cost))}", style={"margin-top":5, "width":150})
                total_matic_usd = Label(f"(${'{:0.2f}'.format(float(matic_cost)*float(matic_price))})", style={"font-size":10,"width":150})
            if max_plays == 0:
                slider = ""
                start_button = Button(f"Not enough GPUL to play this mission!", style={"width":338, "height":30})
            else:
                slider = View(layout="row", style={"margin-left": 10, "margin-top":10})(
                    View(layout="column", style={"background-color":"rgb(255, 255, 255)", "border":"1px solid rgb(226, 226, 226)", "width":170})(
                        Label(f"How many times to play:* ({times_to_play})", style={"margin-left": 5, "margin-top":5, "width":170}),
                        View(layout="row", style={"align": "left", "margin-left": 10, "margin-top":5})(
                            slider_or_text
                            ),
                        View(layout="row", style={"align": "left", "margin-left": 5, "width":150})(
                                Label(f"Total GPUL cost: {total_gpul}", style={"margin-top":5, "margin-bottom":5, "width":150}),
                            ),
                        View(layout="row", style={"align": "left", "margin-left": 5, "width":150})(
                            Label(f"*assuming no deaths", style={"margin-top":1, "margin-bottom":1, "width":150, "font-size":9}),
                            ),
                        ),
                    View(layout="column", style={"background-color":"rgb(255, 255, 255)", "border":"1px solid rgb(226, 226, 226)", "width":150})(
                        Label(f"Gas price (MATIC):", style={"margin-left": 5, "width":130}),
                        View(layout="row", style={"align":"top", "margin-left": 5, "margin-top":5})(
                            TextInput(text=gas_text, cursor="text",
                                      style=matic_input,
                                      on_change=lambda e: self.set_state(gas_text=e)),
                            Button("REC", style={"width":37, "height":20}, on_click=lambda e: self.set_state(gas_text=0.035))),
                        View(layout="row", style={"align": "left", "margin-left": 5, "width":150})(
                            total_matic
                        ),
                        View(layout="row", style={"align": "left", "margin-left": 5, "width":150})(
                            total_matic_usd
                        ))

                )

        if self.retry:
            retry_times = [TextInput(text=f"{self.retry_times}", style=self.retry_times_style, cursor="text", on_change=lambda e:self.set_state(retry_times=e))]
            try:
                retries = int(self.retry_times)
                if retries < 1:
                    raise Exception
            except:
                retry_times.append(Label("Must be number higher than 0!"))
                start_button = Button(f"Invalid Retry Input!", style={"width":338, "height":30})
                column_style['height'] = int(column_style['height'])+10
            retry_col = View(layout="row", style={"width":120, "align":"left"})(
                retry_times
            )

        else:
            retry_col = ""

        if self.config['PRIVATE_KEY'] == "PUT KEY HERE":
            key_setup = Label("No private key detected!\nClick cog button to set it up ->\nRestart required after!", style={"margin": 1, "font-size":12, "font-weight":500, 'color':"rgba(249, 31, 31, 0.78)"})
        else:
            key_setup = [Label(f"Hunter is", style={"margin": 1, "font-size":12}),
            hunter_status]

        return Window(title="PolyPulsar Auto-Player")(View(layout="column", style=column_style)(
                View(layout="column", style={"align": "top", "border-bottom": "1px solid", "border-top": "1px solid"})(
                    View(layout="row", style={"align": "center"})(
                        View(layout="row", style={"align": "center", "width":320, "margin-left":20})(
                        key_setup),
                        View(layout="row", style={"align": "right"})(
                        IconButton(name="cog", size=17, style={"width": 22, "height": 22},
                                   on_click=lambda e: webbrowser.open(self.configFile)),)
                    ),
                    View(layout="row", style={"align": "center"})(
                        Label(f"Tier: {hunter_tier}", style={"margin": 5}),
                        Label(f"Level: {hunter_level}", style={"margin": 5}),
                        Label(f"Missions won: {hunter_success}", style={"margin": 5}),
                    ),
                ),
                View(layout="row", style={"align": "center", "margin": 5, "border-bottom": "1px solid"})(
                    Label(f"GPUL: {balances[0]}", style={"width": 110}),
                    Label(f"MATIC: {balances[2]}", style={"width": 110}),
                    Label(f"GBNT: {balances[1]}"),
                ),
                View(layout="column")(
                    View(layout="row", style={"align": "top", "margin": 10})(
                        Label(f"Hunter Tier:", style={"margin-left": 5, "width":80}),
                        Dropdown(options=["10x","50x","100x"], style={"width":50}, on_select=lambda e: self.set_state(selected_tier=e)),
                        CheckBox(checked=self.retry, text="Auto-retry", style={"margin-left": 15}, on_change=lambda e: self.set_state(retry=not self.retry), tool_tip="Enable to automatically buy new hunters and keep playing the selected mission."),
                        retry_col,
                    ),
                    tier_label
                ),
                available_missions_active_row,
                available_missions_row,
                slider,
                View(layout="row", style={"align": "left", "width":340, "margin-top":10})(
                    start_button,
                ),
            start_window
            )
        )




if __name__ == "__main__":
    ed.App(MyApp()).start()