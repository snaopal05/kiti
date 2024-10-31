import os
import json
import requests
import asyncio
import time
from datetime import datetime
from urllib.parse import unquote
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

class KittyClient:
    def __init__(self):
        self.base_url = "https://kitty-api.bfp72q.com"
        self.session = requests.Session()
        self.headers = {
            "accept-language": "en,en-GB;q=0.9,en-US;q=0.8",
            "user-agent": "Mozilla/5.0 (Linux; Android 13; SM-P610) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6618.139 Mobile Safari/537.36",
            "content-type": "application/json",
            "accept": "*/*",
            "origin": "https://kitty-web.bfp72q.com",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://kitty-web.bfp72q.com/"
        }

    async def login(self, init_data):
        endpoint = f"{self.base_url}/api/login/tg"
        payload = {"init_data": init_data}
        
        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[-] Login failed: {str(e)}{Style.RESET_ALL}")
            return None

    async def get_invites(self, token, start_id="", size=20):
        """Get list of available invites"""
        endpoint = f"{self.base_url}/api/invite/list"
        payload = {
            "token": token,
            "start_id": start_id,
            "size": size
        }
        
        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[-] Failed to get invites: {str(e)}{Style.RESET_ALL}")
            return None

    async def claim_invite(self, token, invite_id):
        """Claim invite reward"""
        endpoint = f"{self.base_url}/api/invite/reward"
        payload = {
            "token": token,
            "invite_id": invite_id
        }
        
        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[-] Failed to claim invite {invite_id}: {str(e)}{Style.RESET_ALL}")
            return None

    async def get_scene_info(self, token, floor_level):
        """Retrieve available eggs for claiming on specified floor level"""
        endpoint = f"{self.base_url}/api/scene/info"
        headers = {**self.headers, "authorization": token}
        payload = {"token": token, "floor": floor_level}
        
        try:
            response = self.session.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[-] Failed to get scene info for floor {floor_level}: {str(e)}{Style.RESET_ALL}")
            return None

    async def claim_egg_reward(self, token, egg_uid):
        endpoint = f"{self.base_url}/api/scene/egg/reward"
        headers = {**self.headers, "authorization": token}
        
        try:
            response = self.session.post(endpoint, json={"token": token, "egg_uid": egg_uid}, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[-] Claim failed for egg UID {egg_uid}: {str(e)}{Style.RESET_ALL}")
            return None

    async def get_balance(self, token):
        """Retrieve account balance information"""
        endpoint = f"{self.base_url}/api/user/assets"
        headers = {**self.headers, "authorization": token}
        payload = {"token": token}

        try:
            response = self.session.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[-] Failed to retrieve balance: {str(e)}{Style.RESET_ALL}")
            return None

    async def process_invites(self, token):
        """Process and claim available invites"""
        try:
            print(f"\n{Fore.CYAN}[*] Processing invites...{Style.RESET_ALL}")
            
            # Get list of invites
            invites_response = await self.get_invites(token)
            if not invites_response or 'data' not in invites_response:
                print(f"{Fore.YELLOW}[!] No invites available{Style.RESET_ALL}")
                return
            
            # Process each invite
            claimed_count = 0
            for invite in invites_response['data']:
                if claimed_count >= 20:  # Limit to 20 claims per day
                    print(f"{Fore.YELLOW}[!] Reached daily claim limit (20){Style.RESET_ALL}")
                    break
                    
                invite_id = invite['id']
                claim_response = await self.claim_invite(token, invite_id)
                
                if claim_response and claim_response.get('code') == 0:
                    claimed_count += 1
                    print(f"{Fore.GREEN}[+] Successfully claimed invite {invite_id} ({claimed_count}/20){Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}[!] Failed to claim invite {invite_id}{Style.RESET_ALL}")
                
                # Add small delay between claims
                await asyncio.sleep(1)
            
            print(f"{Fore.CYAN}[*] Claimed {claimed_count} invites{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}[-] Error processing invites: {str(e)}{Style.RESET_ALL}")

class Timer:
    def __init__(self, interval=60):  # Set interval to 1 minute = 60 seconds
        self.interval = interval

async def process_account(init_data, account_number):
    """Process a single account using its init_data"""
    print(f"\n{Fore.CYAN}[+] Processing Account #{account_number}{Style.RESET_ALL}")
    
    try:
        # Initialize client and authenticate
        client = KittyClient()
        auth_response = await client.login(init_data)
        
        if not auth_response or 'data' not in auth_response:
            print(f"{Fore.RED}[-] Login failed{Style.RESET_ALL}")
            return False

        # Extract token
        token = auth_response['data']['token']['token']
        
        # Process invites first
        await client.process_invites(token)
        
        # Retrieve and display balance
        print(f"\n{Fore.CYAN}[*] Checking balance...{Style.RESET_ALL}")
        balance_response = await client.get_balance(token)
        if balance_response and 'data' in balance_response:
            diamond = balance_response['data']['diamond']['amount']
            kitty = balance_response['data']['kitty']['amount']
            usdt = balance_response['data']['usdt']['amount']
            print(f"{Fore.GREEN}Diamond : {diamond}")
            print(f"Kitty   : {kitty}")
            print(f"USDT    : {usdt}{Style.RESET_ALL}")
        
        # Process eggs
        print(f"\n{Fore.CYAN}[*] Processing eggs...{Style.RESET_ALL}")
        for floor_level in [1, 2]:
            scene_info = await client.get_scene_info(token, floor_level)
            if scene_info and 'data' in scene_info:
                for scene in scene_info['data']:
                    eggs = scene.get('eggs', [])
                    if eggs:
                        for egg in eggs:
                            egg_uid = egg.get('uid')
                            if egg_uid:
                                claim_response = await client.claim_egg_reward(token, egg_uid)
                                if claim_response and 'data' in claim_response:
                                    amount = claim_response['data'].get('amount', 0)
                                    print(f"{Fore.GREEN}[+] Claimed {amount} from egg {egg_uid} on floor {floor_level}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}[!] No eggs available in scene {scene['id']} on floor {floor_level}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[!] No scenes found on floor {floor_level}{Style.RESET_ALL}")
        
        return True

    except Exception as e:
        print(f"{Fore.RED}[-] Error: {str(e)}{Style.RESET_ALL}")
        return False

async def main():
    """Main program execution"""
    timer = Timer()

    while True:
        try:
            print(f"\n{Fore.YELLOW}{'='*50}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[+] Starting execution at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")

            # Load accounts data
            if not os.path.exists("data.txt"):
                print(f"{Fore.RED}[-] data.txt not found!{Style.RESET_ALL}")
                return

            with open("data.txt", "r") as file:
                init_data_list = [line.strip() for line in file if line.strip()]

            # Process each account from data.txt
            for index, init_data in enumerate(init_data_list, start=1):
                print(f"\n{Fore.CYAN}[*] Processing account {index}/{len(init_data_list)}{Style.RESET_ALL}")
                success = await process_account(init_data, index)
                
                if success:
                    print(f"{Fore.GREEN}[+] Account {index} processed successfully{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}[-] Failed to process account {index}{Style.RESET_ALL}")
                
                # Wait one minute between processing each account
                print(f"{Fore.YELLOW}[*] Waiting {timer.interval} seconds before next account...{Style.RESET_ALL}")
                await asyncio.sleep(timer.interval)
                
            print(f"\n{Fore.CYAN}[+] All accounts processed, waiting {timer.interval} seconds before next cycle{Style.RESET_ALL}")
            await asyncio.sleep(timer.interval)  # Wait one minute before starting the next cycle

        except Exception as e:
            print(f"{Fore.RED}[-] Error in main loop: {str(e)}{Style.RESET_ALL}")
            await asyncio.sleep(timer.interval)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
    