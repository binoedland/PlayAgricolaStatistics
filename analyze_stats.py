import pandas as pd
import pickle
import re
import glob
import statistics 
import numpy as np

def open_df(filename):
    return pd.read_pickle(filename)

def read_downloaded_to_df(folder):
    files=glob.glob(folder+"/*")
    l=[]
    for f in files:
        l.append(pd.read_pickle(f))
    df=pd.concat(l,ignore_index=True)
    return df

def print_card_stats(df,card):
    card_df=df[df["card_id"]==card]
    draft_df = card_df[card_df["drafted"]==1]
    play_df = card_df[card_df["played"]==1]
    print("Card "+card +" dealt " + str(len(card_df))+" times.")
    print("Card "+card +" drafted " + str(len(draft_df))+" times.")
    print("Card "+card +" played " + str(len(play_df))+" times.")
    print("Card "+card +" won " + str(play_df["win"].sum())+" times.")  
    ADP=draft_df["draft_pos"].mean()
    print("ADP: "+str(round(ADP,2)))
    play_ratio = card_df["played"].mean()
    print("Played given dealt : "+str(round(play_ratio*100,2))+"%")
    win_ratio = play_df["win"].mean()
    print("Won given played: "+str(round(win_ratio*100,2))+"%")
    PWR = 100/7.0*play_ratio*win_ratio
    print("PWR: "+str(round(PWR,2)))
    
def get_eikgwfg4567():
    card_database=open("./Data/database_of_cards.dat").read().replace("occ","occ-").replace("minor","minor-")
    card_list=card_database.split("\n")
    card_names = [card.split("\t")[-1] for card in card_list[1:]]
    return card_names
def get_card_stats(df,card):
    card_df=df[df["card_id"]==card]
    draft_df = card_df[card_df["drafted"]==1]
    play_df = card_df[card_df["played_with_log"]==1]
    ADP=draft_df["draft_pos"].mean()
    play_ratio = card_df["played_with_log"].mean()
    play_no_log=card_df[card_df["played"]==1]
    play_ratio_no_log=card_df["played"].mean()
    win_ratio = play_df["win"].mean()
    PWR = 100/7.0*play_ratio*win_ratio
    PWR_no_log =  100/7.0*play_ratio_no_log*win_ratio
    l=[len(card_df),len(draft_df),len(play_df),play_df["win"].sum(),ADP,play_ratio,win_ratio,PWR,PWR_no_log]
    return l

def get_stats_player(df,players):
    if type(players) == str:
        players=[players]
    players=[player.lower() for player in players]
    player_games=df[df["player_name"].isin(players)]
    return player_games
def make_pwr_df(df,card_list,normalize=None):
    card_name=[]
    dealt=[]
    drafted=[]
    played=[]
    won=[]
    ADP=[]
    play_ratio=[]
    win_ratio=[]
    PWR=[]
    PWR_no_log=[]
    for card in card_list:
        l=get_card_stats(df,card)
        card_name.append(card)
        dealt.append(l[0])
        drafted.append(l[1])
        played.append(l[2])
        won.append(l[3])
        ADP.append(l[4])
        play_ratio.append(l[5])
        win_ratio.append(l[6])
        PWR.append(l[7])
        PWR_no_log.append(l[8])
    if normalize is not None:
        ref_mean=normalize["PWR"][normalize["PWR"].notna()].mean()
        ref_std=normalize["PWR"][normalize["PWR"].notna()].std()
        PWR_notnan=[p for p in PWR if np.isnan(p)==False]
        mean=statistics.mean(PWR_notnan)
        std=statistics.stdev(PWR_notnan)
        new_PWR=[]
        for p in PWR:
            if np.isnan(p) ==False:
                new_PWR.append(((p-mean)/std)*ref_std+ref_mean)
            else:
                new_PWR.append(p)
        PWR=new_PWR
    pwr_dict={"card_name":card_name,"dealt":dealt,"drafted":drafted,"played":played,"won":won,"ADP":ADP,"play_ratio":play_ratio,
              "win_ratio":win_ratio,"PWR":PWR,"PWR_no_log":PWR_no_log}
    pwr_df = pd.DataFrame(pwr_dict)
    sort_pwr_df=pwr_df.sort_values("PWR",ascending=False)
    return sort_pwr_df

def print_pwr(df,threshold=None):
    for i in list(df.index):
        card_name=df.loc[i]["card_name"]
        PWR=df.loc[i]["PWR"]
        dealt=df.loc[i]["dealt"]
        ADP=df.loc[i]["ADP"]
        drafted=df.loc[i]["drafted"]
        if threshold is not None:
            if drafted >= threshold:
                print("PWR: "+str(round(PWR,2))+" ADP: "+str(round(ADP,2)) +" "+card_name+" Drafted in "+str(drafted)+" games.")
        else:
            print("PWR: "+str(round(PWR,2))+" ADP: "+str(round(ADP,2)) +" "+card_name+" Drafted in "+str(drafted)+" games.")
def print_pwr_to_forum(df,outfile):
    f=open(outfile,"w")
    for j,i in enumerate(list(df.index)):
        card_name=df.loc[i]["card_name"]
        PWR=df.loc[i]["PWR"]
        dealt=df.loc[i]["dealt"]
        ADP=df.loc[i]["ADP"]
        played=df.loc[i]["played"]
        dealt=df.loc[i]["dealt"]
        play_ratio=str(round(df.loc[i]["play_ratio"]*100,1))
        wins=df.loc[i]["won"]
        drafted=df.loc[i]["drafted"]
        win_ratio=str(round(df.loc[i]["win_ratio"]*100,1))
        s= str(j+1)+" " +card_name+" - " + str(round(ADP,2))+ " Plays("+str(played)+"/"+str(dealt)+ " = " +play_ratio+"%) - Wins("+ str(int(wins))+"/"+str(played)+" = " +win_ratio+"%) - PWR = " +str(round(PWR,1))
        f.write(s+"\n")
    f.close()
    
if __name__ == "__main__":
    file="./Data/2020_2021_pwr.pkl"
    df=open_df(file)
    card_database=open("./Data/database_of_cards.dat").read().replace("occ","occ-").replace("minor","minor-")
    card_list=card_database.split("\n")
    card_names=get_eikgwfg4567()
    pwr=make_pwr_df(df,card_names)
    print_pwr(pwr)
    #Uncomment this line to make a file ready to post in forum
    #print_pwr_to_forum(pwr,"forum_stats.txt")