from datetime import datetime
import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
from HARK.Calibration.Income.IncomeTools import (
     sabelhaus_song_var_profile,
)
import hark_portfolio_agents as hpa
from itertools import product
import json
import logging
import math
from math import exp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math
import os

timestamp_start = datetime.now().strftime("%Y-%b-%d_%H:%M")

### Configuring the agent population

dist_params = {
    'CRRA' : {'bot' : 2, 'top' : 10, 'n' : 3}, # Chosen for "interesting" results
    'DiscFac' : {'bot' : 0.936, 'top' : 0.978, 'n' : 2} # from CSTW "MPC" results
}

# Get empirical data from Sabelhaus and Song
ssvp = sabelhaus_song_var_profile()

# Assume all the agents are 40 for now.
# We will need to make more coherent assumptions about the timing and age of the population later.
# Scaling from annual to quarterly
idx_40 = ssvp['Age'].index(40)

### parameters shared by all agents
agent_parameters = {
    'aNrmInitStd' : 0.0,
    'LivPrb' : [0.98 ** 0.25],
    'PermGroFac': [1.01 ** 0.25],
    'pLvlInitMean' : 1.0, # initial distribution of permanent income
    'pLvlInitStd' : 0.0,
    'Rfree' : 1.0,
    'TranShkStd' : [ssvp['TranShkStd'][idx_40] / 2],  # Adjust non-multiplicative shock to quarterly
    'PermShkStd' : [ssvp['PermShkStd'][idx_40] ** 0.25]
}



## Configuring the parameter grid

sim_params = {
    "pop_n" : 25,
    "q" : 2,
    "r" : 2
}

data_n = 2

def run_simulation(
    agent_parameters,
    dist_params,
    n_per_class,
    a = None,
    q = None,
    r = 1,
    fm = None,
    market = None):

    # initialize population
    pop = hpa.AgentPopulation(agent_parameters, dist_params, 5)

    # Initialize the financial model
    fm = hpa.FinanceModel() if fm is None else fm

    fm.calculate_risky_expectations()
    agent_parameters.update(fm.risky_expectations())

    # Initialize the population model
    pop.init_simulation()

    attsim = hpa.AttentionSimulation(pop, fm, a = a, q = q, r = r, market = market)
    attsim.simulate()

    return attsim.sim_stats()

def sample_simulation(args):
    """
    args: attention, dividend_ror, dividend_std, mock, sample
    """
    print(f"New case: {args}")

    attention = args[0]
    dividend_ror = args[1]
    dividend_std = args[2]
    mock = args[3]
    sample = args[4]

    # Initialize the financial model
    fm = hpa.FinanceModel(
        dividend_ror = dividend_ror,
        dividend_std = dividend_std
    )

    if mock:
        market = hpa.MockMarket()
    else:
        market = hpa.MarketPNL(sample = sample)

    try:
        record = run_simulation(
            agent_parameters,
            dist_params,
            sim_params['pop_n'],
            a = attention,
            q = sim_params['q'],
            r = sim_params['r'],
            fm = fm,
            market = market
        )
        return record

    except Exception as e:
        return {
            "error" : e,
            'attention' : args[0],
            'dividend_ror' : args[1],
            'dividend_std' : args[2],
            'mock' : args[3],
            'sample' : args[4]
        }
        

import multiprocessing

pool = multiprocessing.Pool()

attention_range = [0, 0.08] # [0, 0.01, 0.03, 0.06, 0.12, 0.25, 0.5, 1]
dividend_ror_range = [.001, 0.1] # [0.001, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]
dividend_std_range = [0.01]
mock_range = [False, True]
samples = range(data_n)

cases = product(attention_range, dividend_ror_range, dividend_std_range, mock_range, samples)
total_cases = len(attention_range) * len(dividend_ror_range) * len(dividend_std_range) * len(mock_range)

print(f"Number of cases: {total_cases}")
print(f"Number of samples (data_n): {data_n}")

records = pool.map(sample_simulation, cases)
pool.close()

good_records = [r for r in records if 'error' not in r]
bad_records = [r for r in records if 'error' in r]

data = pd.DataFrame.from_records(good_records)

error_data = pd.DataFrame.from_records(bad_records)

data.to_csv(os.path.join("out",f"study-{timestamp_start}.csv"))
error_data.to_csv(os.path.join("out",f"errors-{timestamp_start}.csv"))

timestamp_end = datetime.now().strftime("%Y-%b-%d_%H:%M")

meta = {
    'start' : timestamp_start,
    'end' : timestamp_end,
    'data_n' : data_n,
    'attention_range' : attention_range,
    'dividend_ror_range' : dividend_ror_range,
    'dividend_std_range' : dividend_std_range,
    'mock_range' : mock_range
}

meta.update(sim_params)

with open(os.path.join("out",f'meta-{timestamp_start}.json'), 'w') as json_file:
    json.dump(meta, json_file)
