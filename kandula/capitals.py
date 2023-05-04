import time

from kandula import logging
from kandula.steps import RLStep
from kandula.qtable import QTable
from kandula.Q_learning import QL
from typing import List, Dict

from random import randint
from functools import reduce
import visdom
import numpy as np
import torch
import itertools
import json
import random
from nltk import word_tokenize



with open("resources/country_capital.json", "r") as fc:
    capitals: List = json.load(fc)
capitals_dict = {}
country_index = {}
index_country = {}
i=1
for jl in capitals:
    capitals_dict[jl["country"]] = jl["capital"]
    country_index[jl["country"]] = i
    index_country[i] = jl["country"]
    i+=1


def gen_rand_country():
    country, _ = random.choice(list(capitals_dict.items()))
    return country

class MyRlStep(RLStep):

    def get_state(self):
        country = gen_rand_country()
        state = [country_index[country]]
        return state
    
    def get_reward(self, state, action):
        s = reduce((lambda x: x), state)
        reward = 1 if capitals_dict[index_country[s]] == action else 0
        return reward


def evaluate_my_rl_agent(state_space, actions, q_table):
    # Create all combinations
    elements = [[i for i in range(1, l+1)] for l in state_space]
    all_possible_states = list(itertools.product(*elements))
    
    error = 0

    for s in all_possible_states:
        country = index_country[s[0]]
        actual_capital = capitals_dict[country]
        state_index = q_table.get_state_index(s)
        action_index = torch.argmax(q_table.q_table[state_index]).item()
        rl_prediction = q_table.actions[action_index]
        if actual_capital != rl_prediction:
            error += 1

    error_perc = error*100/len(all_possible_states)
    # print(f"country: {country} - actual: {actual_capital} - predicted: {rl_prediction} - error: {error} - error%: {error_perc}")
    return error_perc


if __name__ == "__main__":


    logging.info('Creating required objects')
    mrls = MyRlStep()
    state_space = [248]
    actions = [v for _, v in capitals_dict.items()]

    qt = QTable(state_space=state_space, actions=actions)
    ql = QL(qtable=qt, rl_step=mrls)

    logging.info('Initializing plot...')
    viz = visdom.Visdom()
    win = viz.line(
        X=np.array([0]), Y=np.array([0]))

    logging.info('Training the model...')
    num_epochs = 2000000
    for e in range(1, num_epochs):
        q_table = ql.train()
        if e % 1000 == 0:
            eval_results = evaluate_my_rl_agent(state_space, actions, q_table)
            viz.line(
                X=np.array([e]),
                Y=np.array([eval_results]),
                win=win,
                name='Error',
                update='append')

    while True:
        country = ""
        query = input ("Enter your quey: ")
        try:
            tokens = word_tokenize(query)
            for t in tokens:
                if t in capitals_dict:
                    country = t
        except Exception as E:
            logging.error(E)
            continue
        try:
            state_index = q_table.get_state_index([country_index[country]])
            action_index = torch.argmax(q_table.q_table[state_index]).item()
            res = q_table.actions[action_index]
            print(f'Capital of {country} is {res}')
        except:
            logging.error('Make sure the country name is written correctly, and is capitalized.')
    

    
        
