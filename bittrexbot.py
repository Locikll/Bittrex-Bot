'''
Bittrex Python Bot
Written by @locikll for NextGenCrypto


Dependencies: p3_bittrex (pip install p3_bittrex) , Python 3
'''
from bittrex import Bittrex
from collections import OrderedDict
from pathlib import Path
import pickle
import sys, os

#{ EDITABLE VARs


apikey='808ec1cdd703409281e843dd5b5fe231'
apisecret='2da9b297e2c149b282b77308282cc47c'

#Wait for order completion (1 for true, 0 for false)
orderwait = 1

#Bid and Ask Fees are both 0.25% commission.
bidFee = 0.0025
askFee = 0.0025

#Amount Retained (%), 0.1 = 10% (BASE LINE for Currencies Not in the specified dictionary)
retainednorm = 0.1 

#Retain specific currencies at different rates, adding new currencies by retainspec['CURRENCY'] = value
retainspec = OrderedDict()
retainspec['STEEM'] = 0.02

#Return on Investment desired, 1.3 = 30% ROI
ROI = 1.3  

SelltoCurrency = 'BTC'

# Minimum trade order in BTC according to https://support.bittrex.com/hc/en-us/articles/202605394-Updates-to-Minimum-Trade-Sizes
Minimumtradeorder = 0.0005

#Path to directory where currencyretain file is stored (for memory), '' means current directory
PATH = ''

# EDITABLE VARIABLES STOP }


def blockPrint():
    sys.stdout = open(os.devnull,'w')
def enablePrint():
    sys.stdout = sys.__stdout__


#remaining = OrderedDict()

def mainrun():
    
    if Path(PATH+'currencyretain.pickle').is_file():
        remaining = pickle.load(open(PATH+'currencyretain.pickle','rb'))
        
    else:
        remaining = OrderedDict()    


    BTX = Bittrex(key=apikey,secret=apisecret)
    
    blockPrint()
    
    balances = BTX.get_balances()['result']
    orders = BTX.get_open_orders()['result']
    
    enablePrint()

    waitingon = []


    for ORDS in orders:
        EX = ORDS["Exchange"]
        TYPE = ORDS["OrderType"]
        
        if (SelltoCurrency in EX) and ('BUY' in TYPE):
            continue
        
        elif (orderwait==1) and (SelltoCurrency not in EX):
            EX = EX.replace(SelltoCurrency+'-','')
            EX = EX.replace('-'+SelltoCurrency,'')
            
            if EX not in EX:
                waitingon.append(EX)
                         
        else:
            continue 
    
    for BAL in balances:
        
        
        Currency = BAL["Currency"]
        Available = BAL["Available"]
        
        if Currency in retainspec.keys():
            retained = retainspec[Currency]
        else:
            retained = retainednorm

      
        if Currency in remaining.keys():
            CurrencyHold = remaining[Currency]
            Available = Available - CurrencyHold
        else:
            CurrencyHold = 0.00
        
        
        if (Currency not in waitingon) and (Currency != SelltoCurrency) and ( (Available + CurrencyHold) > (CurrencyHold + Minimumtradeorder) ):
            
            
            Quantitytosell = (Available-(retained*Available))
            
            blockPrint()
            price = BTX.get_market_history(SelltoCurrency+'-'+Currency)['result'][0]["Price"]
            enablePrint()
            
            #Take into account the initial fee
            zerofeeamount = ( price ) / (1-bidFee)
            
            Netprice = (zerofeeamount*ROI) / (1-askFee)
            
            if (Quantitytosell*price) > Minimumtradeorder:
                
                BTX.sell_limit(SelltoCurrency+'-'+Currency,Quantitytosell,Netprice)
                
                #Make sure to 'Hold' the amount remaining until it goes above this amount.
                remaining[Currency] = retained*Available + CurrencyHold
            
                pickle_out = open(PATH+'currencyretain.pickle','wb')
                pickle.dump(remaining,pickle_out)
                pickle_out.close()                 
                
            else:
                print("Minimum Trade order is: "+ str(Minimumtradeorder) + " " + SelltoCurrency + ", You tried to sell: " + str(Quantitytosell*price) + " " + SelltoCurrency + " Worth.")
            
                        
if __name__=="__main__":
    while True:
        try:
            mainrun()
        except Exception as e:
            print(e)
  