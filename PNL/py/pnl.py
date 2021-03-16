#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 29 2020

@author: Mark Flood
"""

#import pandas as pd
import seaborn as sns
import os
import time
import sys
import logging
import csv
import multiprocessing as mp

import pyNetLogo as pnl

import util as UTIL

import random

LOG=None
LM=None

def run_NLsims(CFG, SEED=1):
    global LOG
    global LM
    
    tic0 = time.process_time()
    
    SEED = random.randrange(10000000)

    sns.set_style('white')
    sns.set_context('talk')

    if 'pythondir' in CFG['DEFAULT']:
        sys.path.append(CFG['DEFAULT']['pythondir'])

    # Set up logging
    sid = f"{SEED}"
    #sid = f"{CFG['pnl']['nLiqSup']}_{CFG['pnl']['nMktMkr']}"
    LOG = logging.getLogger(sid)
    LOG.setLevel(CFG['pnl']['loglevel'])
    logfile = CFG['pnl']['logfilepfx']+sid+'.'+CFG['pnl']['logfilesfx']
    logfile = os.path.join(CFG['pnl']['logdir'], logfile)
    log_fh = logging.FileHandler(logfile, mode='w')
    log_fh.setLevel(CFG['pnl']['loglevel'])
    log_fh.setFormatter(logging.Formatter(CFG['pnl']['logformat']))
    LOG.addHandler(log_fh)
    LOG.warning(f'Sim ID (SEED): {sid}')

    # Log the configuration dictionary
    UTIL.log_config(LOG, CFG, 'pnl')

    # Locate the NetLogo executable and create a pyNetLogo link to it
    LOG.warning('NetLogoLink: '+CFG['pnl']['NLhomedir'])
    LOG.warning('NetLogoLink version: '+str(CFG['pnl']['NLver']))
    LM = pnl.NetLogoLink(gui=False,
                         netlogo_home=CFG['pnl']['NLhomedir'],
                         netlogo_version=str(CFG['pnl']['NLver']))

    # Find the NetLogo script for our LiquidityModel, and load it
    LM_file = os.path.join(CFG['pnl']['NLmodeldir'], CFG['pnl']['NLfilename'])
    LOG.warning('NL model: '+LM_file)
    LM.load_model(LM_file)
    LOG.warning('NL model loaded')

    # Feed the parameter choices for this parallel run to our model
    set_NLvar("SEED", f"{SEED}")
    set_NLvar("#_LiqSup", f"{CFG['pnl']['nLiqSup']}")
    set_NLvar("#_LiqDem", f"{CFG['pnl']['nLiqDem']}")
    set_NLvar("#_MktMkr", f"{CFG['pnl']['nMktMkr']}")

#    broker_buy_limit = broker_buy_limit if broker_buy_limit else CFG['pnl']['BkrBuy_Limit']
    set_NLvar("BkrBuy_Limit", f"{CFG['pnl']['BkrBuy_Limit']}")

#    broker_sell_limit = broker_sell_limit if broker_sell_limit else CFG['pnl']['BkrSel_Limit']
    set_NLvar("BkrSel_Limit", f"{CFG['pnl']['BkrSel_Limit']}")

    set_NLvar("LiqBkr_OrderSizeMultiplier", 
              f"{CFG['pnl']['LiqBkr_OrderSizeMultiplier']}")
    set_NLvar("PeriodtoEndExecution", f"{CFG['pnl']['PeriodtoEndExecution']}")

    # Run the setup function for the NL model
    LOG.warning('NL model -- setup begin')
    LM.command('setup')
    LOG.warning('NL model -- setup end')

    # new and local only right now:
#    LM.command(f"set endBurninTime {CFG['pnl']['LMtickswarmups']}")
    set_NLvar("endBurninTime", f"{CFG['pnl']['LMtickswarmups']}")

    # Run the warmup iterations for the NL model
    LOG.warning('NL model -- warmups begin: '+str(CFG['pnl']['LMtickswarmups']))
    LM.repeat_command('go', int(CFG['pnl']['LMtickswarmups']))
    LOG.warning('NL model -- warmups end')

    # ==========================================================================
    # ====================== TIME-SERIES LOGS ==================================
    # ==========================================================================
     # JCL 3/16/21 Cutting out reports to try and get speed ups
#    csvflushinterval = int(CFG['pnl']['csvflushinterval'])

    # JCL 3/16/21 Cutting out reports to try and get speed ups
#    AOfile = CFG['pnl']['LMallorderpfx']+sid+'.'+CFG['pnl']['LMallordersfx']
#    AOfile = os.path.join(CFG['pnl']['logdir'], AOfile)
#    LOG.warning('Opening all-order (audit) log:'+AOfile)
#    AOcsvf = open(AOfile, mode='w')
#    AOcsvw = csv.writer(AOcsvf, delimiter='\t')
#    AOcsvw.writerow(["Tick","OrderID","OrderTime","OrderPrice","OrderTraderID",
#                     "OrderQuantity","OrderBA","TraderWhoType"])

    TRfile = CFG['pnl']['LMtransactpfx']+sid+'.'+CFG['pnl']['LMtransactsfx']
    TRfile = os.path.join(CFG['pnl']['logdir'], TRfile)
    LOG.warning('Opening transaction log:'+TRfile)
    TRcsvf = open(TRfile, mode='w')
    TRcsvw = csv.writer(TRcsvf, delimiter='\t')
    TRcsvw.writerow(["Tick","TrdID","TrdPrice","TrdTime","TrdQuant",
                     "TrdWhoBid","TrdWhoAsk","TrdWhoBidType","TrdWhoAskType"])

    # JCL 3/16/21 Cutting out reports to try and get speed ups
#    IVfile = CFG['pnl']['LMinventorypfx']+sid+'.'+CFG['pnl']['LMinventorysfx']
#    IVfile = os.path.join(CFG['pnl']['logdir'], IVfile)
#    LOG.warning('Opening inventory log:'+IVfile)
#    IVcsvf = open(IVfile, mode='w')
#    IVcsvw = csv.writer(IVcsvf, delimiter='\t')
#    IVcsvw.writerow(["Tick","TraderID","TraderWhoType","SharesOwned"])

    # JCL 3/16/21 Cutting out reports to try and get speed ups
#    FACT_TraderNumber=1
#    FACT_TypeOfTrader=2
#    FACT_SharesOwned =3

    # Run the simulation for fullrun ticks, recording as we go
    stateCheck()
    LOG.warning('NL model -- simruns begin: '+str(CFG['pnl']['LMtickssimruns']))
    for tik in range(int(CFG['pnl']['LMtickssimruns'])):
        LM.command('go')

        #if tik > 100
        # JCL 3/16/21 Cutting out reports to try and get speed ups
        if (tik > (int(CFG['pnl']['LMtickssimruns'])-10)):
            try:
                ticks = int(LM.report('ticks'))
                LOG.info(f' -- Ticks: {ticks}')
            except:
                print(f'past end grab, tik: ',tik)

        # ================== ALL ORDER LOG =====================================
        # JCL 3/16/21 Cutting out reports to try and get speed ups
#        ct_allorders = int(LM.report('length allOrders'))
#        LOG.debug(f'     -- ct_allorders: {ct_allorders}')
#        print(f'ticks={ticks}, ct_allorders={ct_allorders}:')
#        for i in range(ct_allorders):
#            try:
#                print(f'    i={i}')
#                rdr0 = int(LM.report(f'prop_allOrders {i} "OrderID"'))
#                rdr1 = float(LM.report(f'prop_allOrders {i} "OrderTime"'))
#                rdr2 = float(LM.report(f'prop_allOrders {i} "OrderPrice"'))
#                rdr3 = int(LM.report(f'prop_allOrders {i} "OrderTraderID"'))
#                rdr4 = float(LM.report(f'prop_allOrders {i} "OrderQuantity"'))
#                rdr5 = str(LM.report(f'prop_allOrders {i} "OrderB/A"'))
                # rdr6 = int(LM.report(f'prop_allOrders {i} "TraderWho"'))
#                rdr7 = str(LM.report(f'prop_allOrders {i} "TraderWhoType"'))
#                AOcsvw.writerow([ticks,rdr0,rdr1,rdr2,rdr3,rdr4,rdr5,  rdr7])
#                print(f'       OrderID={rdr0},OrderTime={rdr1},OrderPrice={rdr2},OrderTraderID={rdr3},OrderQuantity={rdr4},OrderB/A={rdr5},TraderWhoType={rdr7}')
#            except:
#                pass
#        LOG.debug(f'     -- Completed allorders for tick: {tik}')


        # ================== TRANSACTION LOG =====================================
        # JCL 3/16/21 Cutting out reports and only print at the end to try and get speed ups
        if (tik > (int(CFG['pnl']['LMtickssimruns'])-10)):
            try:
                ct_transactions = int(LM.report('length list_transactions'))
                # JCL 3/16/21 Cutting out reports to try and get speed ups
        #        LOG.debug(f'     -- ct_transactions: {ct_transactions}')
                for i in range(ct_transactions):
                    try:
                        trd0 = int(LM.report(f'prop_list_transactions {i} "TrdID"'))
                        trd1 = float(LM.report(f'prop_list_transactions {i} "TrdPrice"'))
                        trd2 = float(LM.report(f'prop_list_transactions {i} "TrdTime"'))
                        trd3 = int(LM.report(f'prop_list_transactions {i} "TrdQuant"'))
                        trd4 = float(LM.report(f'prop_list_transactions {i} "TrdWhoBid"'))
                        trd5 = str(LM.report(f'prop_list_transactions {i} "TrdWhoAsk"'))
                        trd6 = int(LM.report(f'prop_list_transactions {i} "TrdWhoBidType"'))
                        trd7 = str(LM.report(f'prop_list_transactions {i} "TrdWhoAskType"'))
                        TRcsvw.writerow([ticks,trd0,trd1,trd2,trd3,trd4,trd5,trd6,trd7])
                    except:
                        pass
                    # JCL 3/16/21 Cutting out reports to try and get speed ups            
            #        LOG.debug(f'     -- Completed transactions for tick: {tik}')
            except:
                pass
        # =================== INVENTORY LOG ====================================
        # JCL 3/16/21 Cutting out reports to try and get speed ups
#        ct_lsttrders = int(LM.report('length list_traders'))
#        for i in range(ct_lsttrders):
#            tdr0 = int(LM.report(f'prop_list_traders {i} {FACT_TraderNumber}'))
#            tdr1 = str(LM.report(f'prop_list_traders {i} {FACT_TypeOfTrader}'))
#            tdr2 = float(LM.report(f'prop_list_traders {i} {FACT_SharesOwned}'))
#            IVcsvw.writerow([ticks,tdr0,tdr1,tdr2])
#        LOG.debug(f'     -- Completed lsttrders for tick: {tik}')

        if (tik > (int(CFG['pnl']['LMtickssimruns'])-21)):
            try:
#        if ((ticks % csvflushinterval) == 0):
#            AOcsvf.flush()
#            IVcsvf.flush()
                TRcsvf.flush()
            except:
                pass

        # JCL 3/16/21 Cutting out reports to try and get speed ups
#    LOG.warning('Closing all-order (audit) log:'+AOfile)
#    AOcsvf.close()
#    LOG.warning('Closing inventory log:'+IVfile)
#    IVcsvf.close()
    LOG.warning('Closing transaction log:'+TRfile)
    TRcsvf.close()

    LOG.warning('=============== END OF NetLogo RUN ==========================')

    toc0 = time.process_time()
    print(f'Elapsed (sys clock), run {SEED}: ', toc0-tic0)

def set_NLvar(varname,value):
    LOG.debug(f"SETTING: {varname}:={value}")
    LM.command(f"set {varname} {value}")

def log_NLvar(varname):
    value = LM.report(f"{varname}")
    LOG.debug(f"REPORTING: {varname}=={value}")

def stateCheck():
    LOG.debug('----------------------- LM STATE ------------------------------')
    log_NLvar("SEED")
    log_NLvar("ticks")
    log_NLvar("#_LiqSup")
    log_NLvar("#_LiqDem")
    log_NLvar("#_MktMkr")
    log_NLvar("BkrBuy_Limit")
    log_NLvar("BkrSel_Limit")
    log_NLvar("LiqBkr_OrderSizeMultiplier")
    log_NLvar("PeriodtoEndExecution")
    log_NLvar("endBurninTime")
    
    log_NLvar("AgentFile")
    log_NLvar("DepthFile")
    log_NLvar("FrcSal_QuantSale")
    log_NLvar("LiqDem_TradeLength")
    log_NLvar("LiqSup_TradeLength")
    log_NLvar("liquidity_Supplier_Arrival_Rate")
    log_NLvar("liquiditySupplierOrderSizeMultipler")
    log_NLvar("liquidity_Demander_Arrival_Rate")
    log_NLvar("liquidityDemanderOrderSizeMultipler")
    log_NLvar("marketMakerOrderSizeMultipler")
    log_NLvar("market_Makers_Arrival_Rate")
    log_NLvar("MarketMakerInventoryLimit")
    log_NLvar("MktMkr_TradeLength")
    log_NLvar("PercentPriceChangetoOrderSizeMultiple")
    log_NLvar("PeriodtoStartExecution")
    log_NLvar("PeriodtoEndExecution")
    log_NLvar("ProbabilityBuyofLiqyuidityDemander")
    log_NLvar("timeseries")
    log_NLvar("timeseriesvalue")
    LOG.debug('---------------------------------------------------------------')


def main(argv=None):
    """A main function for command line execution

    This function parses the command line, loads the configuration, and 
    invokes the local functions:

         * run_NLsims(config)

    Parameters
    ----------
    argv : dict
        The collection of arguments submitted on the command line
    """
    print("Hello World")
    config = UTIL.parse_command_line(argv, __file__)

    NLruncount = int(config['pnl']['NLruncount'])
    parallelcores = int(config['DEFAULT']['parallelcores'])
    nTickWarmUp = int(config['pnl']['LMtickswarmups'])
    pcount = int(NLruncount/parallelcores)
    pcountLeftOver = NLruncount%parallelcores
    print("pcount: ", pcount, ", pcountLeftOver: ", pcountLeftOver,", nTickWarmUp: ",nTickWarmUp)

    if (pcount > 0):
        for i in range(pcount):
            pool = mp.Pool(processes=parallelcores)
            for j in range(parallelcores):
                pool.apply_async(run_NLsims, (config, j))
            pool.close()
            pool.join()
            print("End of batch: ",i)
    if (pcountLeftOver > 0):
        for i in range(pcountLeftOver):
            run_NLsims(config, i)   
    
    print("End of simulatin run!")


#    pcount = min(int(config['DEFAULT']['parallelcores']), 
#                          os.cpu_count(), NLruncount)
#    if (pcount > 0):
#        pool = mp.Pool(processes=pcount)
#        for i in range(NLruncount):
#            pool.apply_async(run_NLsims, (config, i))
#        pool.close()
#        pool.join()
#    else:
#        for i in range(NLruncount):
#            run_NLsims(config, i)

    #try:
#    run_NLsims(config)
    #except Exception as e:
    #    print('Exception: ', e)

# This tests whether the module is being run from the command line
if __name__ == "__main__":
    main()