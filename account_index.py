from flask import Flask, redirect
import json
import datetime

from steemapi.steemnoderpc import SteemNodeRPC

# Memoize results for each user
with open('hindex_dict.dat', 'r') as f:
    hindex_dict = eval(f.read())

app = Flask(__name__)

@app.route("/")
def homepage():
    return('Go to /account_name to view their metadata webpage')

@app.route("/<account_name>")
def determine_user_index(account_name):
    #rpc = SteemNodeRPC("wss://steemit.com/wspa")
    
    try:
        [h_index, post_titles, sp_payouts] = hindex_dict[account_name][str(datetime.date.today())]
        publish_date = str(datetime.date.today())
    except:
        rpc = SteemNodeRPC("ws://localhost:8090")
        post_payouts, post_titles = author_rewards(rpc, account_name)
        
        sp_payouts = vest_conversion(rpc, post_payouts)
        
        h_index = 0
        for pos, val in enumerate(sp_payouts):
            if val > pos:
                h_index = pos + 1
            else:
                break
                
        publish_date = str(datetime.date.today())
        
        if account_name not in hindex_dict:
            hindex_dict[account_name] = {}
        hindex_dict[account_name][publish_date] = [h_index, post_titles, sp_payouts]
        with open('hindex_dict.dat','w') as f:
            f.write(str(hindex_dict))
     
     
    return('H-index: ' + str(h_index) + '<br>Most popular post: ' + post_titles[0] + ', at a value of ' + str(sp_payouts[0]) + ' Steem Power.' + '<br><br>(Cached on ' + publish_date + ')')
    
def vest_conversion(rpc, post_payouts):
    total_vests = rpc.get_dynamic_global_properties()['total_vesting_shares']
    total_sp = rpc.get_dynamic_global_properties()['total_vesting_fund_steem']
    sp_conversion = float(total_sp.split(' ')[0]) / float(total_vests.split(' ')[0])
    
    sp_payouts = [sp_conversion * post_reward for post_reward in post_payouts]
    
    return sp_payouts

def author_rewards(rpc, account_name):

    #try:
    last_tx, curr_tx, curr_post = -1, -1, 0
    account_data, account_block, post_titles, post_payout = [], [], [], []
    while last_tx == curr_tx:
        curr_tx = curr_tx + 1
        account_block = rpc.get_account_history(account_name,curr_tx,0)
        last_tx = account_block[0][0]
        if account_block[0][1]['op'][0] == 'comment_reward' and account_block[0][1]['op'][1]['author'] == account_name:
            curr_post = curr_post + 1
            post_titles.append(account_block[0][1]['op'][1]['permlink'])
            post_payout.append(account_block[0][1]['op'][1]['vesting_payout'])
            print(str(post_titles[-1]) + ' - found ' + account_name + '\'s post: #' + str(curr_post) + '!')
            
    payout_array = [float(p.split(' ')[0]) for p in post_payout]
    
    zipped = zip(payout_array, post_titles)
    zipped = sorted(zipped, reverse=True)
    
    payout_array, post_titles = zip(*zipped)
    
    return(payout_array, post_titles)
    
    #except:
        #return('Something went wrong.  Perhaps ' + account_name + ' hasn\'t set their url metadata?')

def account_meta(account_name):
    rpc = SteemNodeRPC("wss://steemit.com/wspa")

    #try:    
        #account_meta = json.loads(rpc.get_account(account_name)['json_metadata'])
   
        #account_url = account_meta['url']
   
    last_tx, curr_tx = -1, -1
    account_data, account_block, account_titles, account_links = [], [], [], []
    while last_tx == curr_tx:
        curr_tx = curr_tx + 1
        account_block = rpc.get_account_history(account_name,curr_tx,0)
        last_tx = account_block[0][0]
        if account_block[0][1]['op'][0] == 'comment' and account_block[0][1]['op'][1]['author'] == account_name:
            #account_data.append(account_block)
            account_links.append(account_block[0][1]['op'][1]['permlink'])
            account_titles.append(account_block[0][1]['op'][1]['title'])
            print(str(account_titles[-1]) + ' - found your post!')
        
        
    accountset = set(account_titles)
    return(accountset)
    
    #except:
        #return('Something went wrong.  Perhaps ' + account_name + ' hasn\'t set their url metadata?')

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=5000)
    #app.run()
