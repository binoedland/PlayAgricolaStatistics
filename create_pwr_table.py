import dataclasses
import glob
import pathlib
import pickle
import re

import pandas as pd
import numpy as np

import tabulate

@dataclasses.dataclass
class CardStats:

    name: str
    img_name: str

    dealt: int = 0
    drafted: int = 0
    played: int = 0

    won: int = 0
    ADP: float = None
    play_ratio: float = None
    win_ratio: float = None
    PWR: float = None
    PWR_no_log: float = None

    PWR_normalized: float = None

    def __str__(self):
        s = f'Card {self.name} dealt {self.dealt} times.\n'
        s += f'Card {self.name} drafted {self.drafted} times.\n'
        s += f'Card {self.name} played {self.played} times.\n'
        s += f'Card {self.name} won {self.won} times.\n'
        s += 'ADP: {:.2f}.\n'.format(self.ADP)
        s += 'Played given dealt: {:.2f} %.\n'.format(100.0*self.play_ratio)
        s += 'Won given played: {:.2f} %.\n'.format(100.0*self.win_ratio)
        s += 'PWR: {:.2f} %.\n'.format(self.PWR )
        return s

def read_card_statistics(pkl_file):
    with open(pkl_file, 'rb') as pickle_file:
        return pickle.load(pickle_file)

def store_card_statistics(list_of_card_stats, pkl_file):
    with open(pkl_file, 'wb') as pickle_file:
        pickle.dump(list_of_card_stats, pickle_file, pickle.HIGHEST_PROTOCOL)

def get_db_file_path():
    return pathlib.Path().cwd() / 'Data' / 'database_of_cards.dat'

def str_card_database(add_hyphens=False):
    with open(get_db_file_path()) as db_file:
        str_file = db_file.read()
        if add_hyphens:
            return str_file.replace('occ', 'occ-').replace('minor', 'minor-')
        return str_file

def get_eikgwfg4567(add_hyphens=False):
    str_card_db = str_card_database(add_hyphens=add_hyphens)
    card_list = str_card_db.split('\n')
    card_names = [card.split('\t')[-1] for card in card_list[1:]]
    return card_names

def get_card_stats(df, card_img_name):
    """
    Returns None if the sought-after stats cannot be computed.
    """
    card_df = df[df['card_id']==card_img_name]
    draft_df = card_df[card_df['drafted']==1]
    play_df = card_df[card_df['played_with_log']==1]
    ADP = draft_df['draft_pos'].mean()
    play_ratio = card_df['played_with_log'].mean()
    play_no_log = card_df[card_df['played']==1]
    play_ratio_no_log = card_df['played'].mean()
    win_ratio = play_df['win'].mean()
    PWR = (100/7.0)*play_ratio*win_ratio
    PWR_no_log = (100/7.0)*play_ratio_no_log*win_ratio

    no_times_dealt = len(card_df)
    if no_times_dealt == 0 or np.isnan(PWR) or np.isnan(ADP):
        return None

    card_name = get_real_card_names(card_img_name)

    if card_name.lower() == 'broom':
        print('Remove broom stats...')
        return None  # remove stats for Broom since it is currently bugged...

    return CardStats(name=card_name,
                     img_name=card_img_name,
                     dealt=no_times_dealt,
                     drafted=len(draft_df),
                     played=len(play_df),
                     won=play_df['win'].sum(),
                     ADP=ADP,
                     play_ratio=play_ratio,
                     win_ratio=win_ratio,
                     PWR=PWR,
                     PWR_no_log=PWR_no_log)

def make_list_of_card_stats(df, card_image_names):
    list_of_card_stats = [get_card_stats(df, img) for img in card_image_names]
    return [stats for stats in list_of_card_stats if stats is not None]

def get_real_card_names(card_image_names):
    """
    :param card_image_names: Either a list of names, or a single name.
    :return: Either a list of names, or a single name.
    """
    df_db = pd.read_csv(get_db_file_path(), sep='\t')

    input_list = [card_image_names] if isinstance(card_image_names, str) else  card_image_names

    card_names = []
    for card in input_list:
        idx_card = [idx for idx, img_name in enumerate(df_db['Image']) if card == img_name]
        if idx_card:
            assert len(idx_card) == 1
            name = df_db['Name'].iloc[idx_card[0]]
            card_names.append(name)
        else:
            card_names.append(card)

    if len(card_names) == 1:
        return card_names[0]
    return card_names


def write_pwr_to_file(list_of_card_stats, file_path, format='fancy_grid'):

    cards_sorted_by_PWR = sorted(list_of_card_stats,
                                 key=lambda card_stats: card_stats.PWR,
                                 reverse=True)

    dict_stats = {}
    dict_stats['Card'] = [card.name for card in cards_sorted_by_PWR]
    dict_stats['Dealt'] = [card.dealt for card in cards_sorted_by_PWR]
    dict_stats['Played'] = np.array([card.played for card in cards_sorted_by_PWR])
    dict_stats['Wins'] = np.array([card.won for card in cards_sorted_by_PWR])
    dict_stats['Played/Dealt[%]'] = np.round(100.0*dict_stats['Played']/dict_stats['Dealt'], 1)
    dict_stats['Won/Played[%]'] = np.round(100.0*dict_stats['Wins']/dict_stats['Played'], 1)
    dict_stats['ADP'] = [round(card.ADP, 2) for card in cards_sorted_by_PWR]
    dict_stats['PWR'] = [round(card.PWR, 1) for card in cards_sorted_by_PWR]

    table = tabulate.tabulate(dict_stats, headers='keys', tablefmt=format)  # stralign='center'
    with open(file_path, 'w') as f:
        f.write(table)


if __name__ == "__main__":

    dump_pwr_pickle = False

    if dump_pwr_pickle:  # NB: takes time...
        data_file = './Data/2020_2021_pwr.pkl'
        df_all = pd.read_pickle(data_file)
        pkl_card_names = df_all['card_id']
        df_all['card_id'] = [s.replace('occ-', 'occ').replace('minor-', 'minor') for s in pkl_card_names]

        card_names = get_eikgwfg4567(add_hyphens=False)
        card_stats = make_list_of_card_stats(df_all, card_names)
        store_card_statistics(card_stats, './Data/pwr_stats.pkl')

    else:  # read existing file... (generated when dump_pwr_pickle == True)
        card_stats = read_card_statistics('./Data/pwr_stats.pkl')
        write_pwr_to_file(card_stats, file_path='./Data/pwr.html', format='html')
