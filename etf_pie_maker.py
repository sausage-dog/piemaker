import pandas as pd
import numpy as np
import requests
import math
import time

t121_page = "https://www.trading212.com/en/Trade-Equities"


weight_types = ["Percent Of Fund", "weight","weighting", "% of net assets","% of funds", "% of fund" ]
ticker_types = ["ticker", "security ticker", "identifier","Issuer Ticker", "Holding Ticker"]
name_types = ["company","security","security name","name","holding", "description","SecurityDescription"]
currencies = ["EUR","DKK","GBP","CHF","USD","JPY", "SEK", "KRW", "RMB", "PLN", "AUD", "CAD", "HUF", "RUB", "TWD", "HKB", "NZD", "SGD", "BRL"]

class Pie(object):
    def __init__(self): 
        self.securities = []
        self.number_of_securities = [None]
        self.sum_of_security_weighing = [None]

class Holding(object):
    
    def __init__(self, etf_num, tick): 
        global number_of_etfs
        self.t212_frac = None
        self.weights = [None] * etf_num           
        self.etf_weights = [None] * etf_num    
        self.mean = 0
        self.scaling_factor = None
        self.scaled_mean = None
        self.name = None
        self.tick = tick                

    def AddWeight(self, weight, ETF_indx):
        self.weights[ETF_indx] = float(weight)

    def ScaledWeight(self, scaling_factor):
        self.scaling_factor = scaling_factor
        self.scaled_mean = round(((self.mean / float(scaling_factor)) * 2)) / 2

    def AddETFScales(self, index, etf_weight):        
        self.etf_weights[index] = etf_weight        

    def Mean(self):
        sum_weight = 0
        sum_full = 0

        for idx, weight in enumerate(self.weights):
            if weight is not None:                
                sum_weight = sum_weight + weight*(self.etf_weights[idx])
                sum_full = sum_full + 1

        self.mean = sum_weight/sum_full

def FindTicker(columns):    
    for column in columns:
        for ticker in ticker_types:
            if "fund" not in str(column).lower():
                if ticker.lower() in str(column).lower():                    
                    return column
    return None

def FindWeight(columns):
    for column in columns:
        for weight in weight_types:                   
            if weight.lower() in str(column).lower():                
                return column
    return None

def FindName(columns):
    for column in columns:
        for name in name_types:    
            if "ticker" not in str(column).lower() and str(column).lower()  != "Security Id".lower():   
                if name.lower() in str(column).lower():                
                    return column
    return None

#### add isa check
def FindTickerFractional(ticker, sec_page, ISA):      

    ticker_entry =  sec_page.find("\"Instrument\">"+str(ticker)+"</di")   

    if ticker_entry != -1:

        subs = sec_page[ticker_entry:ticker_entry+650]  

        ## if there is a company entry
        if subs.find("data-label=\"Company\">") != -1:                

            if ISA and subs.find("data-label=\"Market name\">NON-ISA") != -1:                
                return False

            quant_start = subs.find("Min traded quantity")            
            fractional_value = subs[quant_start:quant_start+30]       

            ## find >
            frac_start = fractional_value.find('>')
            frac_end = fractional_value.find('<')
            frac_number = float(fractional_value[frac_start+1:frac_end])            

            if frac_number < 1:
                return True
    
    return False


def GetColumns(df):
    columns = []

    for col in df.columns:
        columns.append(col)

    return columns

def StripPercent(weight):    
    newstr = None
    if '%' in weight:
        newstr = weight.replace("%","")
    else:
        newstr = weight
    return newstr

def GetFiles(file_paths):

    excells = []

    for file_path in file_paths:
        excells.append(pd.read_excel(io=file_path, sheet_name=None))

    return excells

def AddUserSecurities(settings, holdings_list, holdings_list_final, user_etf_index):

    ## load custom
    for user_sec in settings.user_securities:
        
        ## add check if not final
        if user_sec[2]:
            sec = Holding(user_etf_index+1, user_sec[0])
            sec.AddETFScales(user_etf_index, 1) 
            holdings_list.append(sec)
            holdings_list[-1].AddWeight(user_sec[1], user_etf_index)   

        else:
            holdings_list_final.append([user_sec[0], float(user_sec[1])])

    return holdings_list, holdings_list_final    

## load up all securities from an excell file
def LoadETF(settings, etf_pd, etf_index, total_etf, holdings_list, holdings_list_final, etf_weight):

    ## get usefull columns names
    doc_columns = GetColumns(etf_pd)
    ticker_name = FindTicker(doc_columns)    
    weight_name = FindWeight(doc_columns)
    name_name = FindName(doc_columns)

    settings.error_string[0] = ""

    if ticker_name == None:
        settings.error_string[0] = "Failed to find ticker column name in etf: " + settings.etf_locations[etf_index][0] + '\n'        

    if weight_name == None:
        settings.error_string[0] = settings.error_string[0] + "Failed to find weight column name in etf: " + settings.etf_locations[etf_index][0]
        
    if len(settings.error_string[0]) > 0:
        return False

    ## see what weird percentages they used
    sum_weights = 0

    ## pre holding list
    pre_holdings_list = []
    
    for index, row in etf_pd.iterrows():            

        ## check if not null entry 
        if str(row[ticker_name]) != "nan":

            ratio = float(StripPercent(str(row[weight_name]))) 

            ## to string
            sec_string = str(row[ticker_name]) 

            ## remove after space countrey code
            sec_name = sec_string.split(" ", 1)[0]

            ## check it's not a currency
            if sec_name not in currencies:

                ## check if it's not in final list
                if sec_name not in [row[0] for row in holdings_list_final]:                    

                    ## if not already preseet make a ticker entry
                    if not any(tick.tick == sec_name for tick in holdings_list):                                                  
                        sec = Holding(total_etf,sec_name)     

                        if name_name != None:
                            ## if name has been found
                            sec.name = row[name_name]

                        pre_holdings_list.append(sec)                
                                        
                    for holding in pre_holdings_list:
                        if holding.tick == sec_name:                                   
                            holding.AddWeight(ratio,etf_index)
                            holding.AddETFScales(etf_index, etf_weight)    
                            sum_weights = sum_weights + ratio    

    ## if sums add to 1 and not 100, scale by 100
    if round(sum_weights) == 1:        
        for h in pre_holdings_list:
            h.AddWeight(h.weights[etf_index] * 100, etf_index)

    ## add to the list being returned
    for pre in pre_holdings_list:
        holdings_list.append(pre)

    return holdings_list


## loop over spreadsheets specified by the user
def LoadETFsSecurities(holdings_list, holdings_list_final, settings, number_of_etfs, etf_weights):

    ## load excell files
    for etf_index, etf in enumerate(settings.etf_locations):    

        try:
            xl = pd.ExcelFile(etf[1])            
            s = xl.parse(xl.sheet_names[0])
        except:
            xl = pd.read_csv(etf[1], skiprows=0,sep='\t')            
            s = xl 
        
        etf.append(s)
        etf_weights.append(etf[2])        

        ## load securities
        holdings_list = LoadETF(settings, etf[3],etf_index, number_of_etfs, holdings_list, holdings_list_final, etf_weights[etf_index])

        if holdings_list == False:
            return False, False

    return holdings_list, etf_weights


def FilterT212Securities(holdings_list, holdings_list_final, settings):

    ## if ISA fractional selected 
    if settings.only_ISA_212_frac[0] or settings.only_212_frac[0]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"}
        response212 = requests.get(t121_page,timeout=2.50, headers=headers)
        holdings_list = [sec for sec in holdings_list if FindTickerFractional(sec.tick, response212.text, settings.only_ISA_212_frac[0])]
        holdings_list_final = [sec for sec in holdings_list_final if FindTickerFractional(sec[0], response212.text, settings.only_ISA_212_frac[0])]

    return holdings_list,holdings_list_final


def CalculateMeanInitials(holdings_list):

    ## calculate with pre final values and means
    means_sum = 0
    
    ## call mean on each security instance
    for idx, value in enumerate(holdings_list):   
        value.Mean()     
        means_sum = means_sum + value.mean

    return means_sum/100


## remove those that do not fit in the aggregate total
def TrimExcessSecurities(settings, holdings_list, holdings_list_final):

    initial_secs = len(holdings_list)
    print("Length of securities: ",initial_secs)
    final_secs = 0

    max_allowed = settings.split_between_pies[0] * 50

    ## securities that are non zero and final
    for sec in holdings_list_final:
        if sec[1] != 0:
            final_secs = final_secs + 1

    current_total = final_secs + initial_secs

    if current_total > max_allowed:

        ## trim excess
        excess = current_total - max_allowed
        print("excess: ",excess)
        holdings_list = holdings_list[:len(holdings_list) - excess]

        print("Removed: ", excess," securities")

    print("Length of securities: ",len(holdings_list))
    return holdings_list

## finds number and total percentage
def FindFinalSum(holdings_list_final):

    final_secs_count = 0
    final_sum = 0
    for sec_final in holdings_list_final:
        if sec_final[1] != 0:
            final_secs_count = final_secs_count + 1
            final_sum = final_sum + sec_final[1]

    return final_secs_count, final_sum

        
def CalculateDistribution(settings, holdings_list, holdings_list_final):   

    ## get data relating to final security weights
    total_final_sec, final_weight_sum = FindFinalSum(holdings_list_final)    

    ## get sum of all the means
    initial_means_sum = CalculateMeanInitials(holdings_list)    

    ## find scaling ratio      
    scaling_factor = initial_means_sum / ((100 - final_weight_sum) / 100)    

    for sec in holdings_list:        
        sec.ScaledWeight(scaling_factor)        

    holdings_list = [sec for sec in holdings_list if sec.scaled_mean >= 0.5]   

    ## return with all means scaled accordingly
    return holdings_list   


def SortMean(holdings_list):    

    holdings_list.sort(key=lambda holding: holding.mean, reverse=True)
    return holdings_list
    
## remove if securities with weights below 0.25, or less if more pies since they get scaled anyway
def FilterBelowThreshold(holdings_list, settings):

    if settings.remove_below_half_percent[0]:
        holdings_list = [sec for sec in holdings_list if sec.mean > 0.25]      

    return holdings_list  

## combinen securities from user and from excells
def JoinLists(holdings_list, holdings_list_final):

    final_security_list = []

    # ## loop over initials
    for sec_init in holdings_list:
        final_security_list.append([sec_init.tick, sec_init.scaled_mean, sec_init.name])

    # loop over finals
    for sec_fin in holdings_list_final:
        if sec_fin[1] > 0:
            final_security_list.append([sec_fin[0], sec_fin[1]])               

    final_security_list.sort(key=lambda x: x[1], reverse=True)

    return final_security_list


def DivideAmongstPies(joint_list, settings):

    ## lower from the max if possible
    pie_num = math.ceil(len(joint_list) / 50)

    ## list size of pie specified
    pie_array = [[] for i in range(pie_num)]

    ## percentages per pie
    pie_ratio = 100 / pie_num

    print("\n\nrecieved ",len(joint_list)," securities")

    ## number of splits
    pie_true = len(joint_list) / 50

    if settings.split_between_pies == 1:
        pie_array[0] = joint_list
    else:

        sec_counter = 0
        current_pie = 0
        break_out_counter = 0        

        while sec_counter < len(joint_list):
            
            ## try only if less than the pie ratio and less than max securities number
            if sum([row[1] for row in pie_array[current_pie]]) + joint_list[sec_counter][1] <= pie_ratio and len(pie_array[current_pie]) < 50:
                
                pie_array[current_pie].append(joint_list[sec_counter])                

                ## next security
                sec_counter = sec_counter + 1

            ## next pie
            if current_pie < pie_num - 1:
                current_pie = current_pie + 1
            else:
                current_pie = 0 

            if break_out_counter < pie_num * len(joint_list):
                break_out_counter = break_out_counter + 1
            else:
                break

    failed_to_add = len(joint_list) - sec_counter    
    total_ratios = 0    

    ## make new pie object array for the viewe
    pies_obj_arr = [Pie() for i in range(pie_num)]
    
    for i,eql in enumerate(pie_array):
        
        pies_obj_arr[i].securities = eql
        sum_sec = 0
        num_sec = 0

        for sec in eql:            
            sum_sec = sum_sec + sec[1]
            num_sec = num_sec + 1            

        pies_obj_arr[i].number_of_securities[0] = num_sec
        pies_obj_arr[i].sum_of_security_weighing[0] = sum_sec

        total_ratios = total_ratios + sum_sec

    return pies_obj_arr, joint_list[len(joint_list)-failed_to_add:]

def ExternalMain(settings):

    etf_weights = []
    holdings_list = []
    holdings_list_final = []
    
    ## get number of different etfs
    number_of_etfs = len(settings.etf_locations)

    ## get number of custom securities
    if any(float(sec[1]) > 0 and sec[0] for sec in settings.user_securities):

        ## one more weight category
        number_of_etfs = number_of_etfs + 1

        ## add user defined securities to the additional weight
        holdings_list, holdings_list_final =  AddUserSecurities(settings, holdings_list, holdings_list_final, number_of_etfs-1)        

    print("Added user securities: ",len(holdings_list),"  ",len(holdings_list_final))     

    ## load securities from file
    holdings_list, etf_weights = LoadETFsSecurities(holdings_list, holdings_list_final, settings, number_of_etfs, etf_weights)


    print("Loaded securities: ",len(holdings_list))

    if holdings_list == False or etf_weights == False:
        return [], settings    

    ## filter out securities
    holdings_list, holdings_list_final = FilterT212Securities(holdings_list, holdings_list_final, settings)    

    print("After T212 filtering: ",len(holdings_list))

    ## calculate mean
    CalculateMeanInitials(holdings_list)

    ## sort
    holdings_list = SortMean(holdings_list)

    ## filter those taht didn't make the cut
    holdings_list =  FilterBelowThreshold(holdings_list, settings)    

    ## filter thsoe that exceed total allowed for all pies
    holdings_list = TrimExcessSecurities(settings, holdings_list, holdings_list_final)

    print("calc dist pre getting: ",len(holdings_list))

    ## full distribution
    holdings_list = CalculateDistribution(settings, holdings_list, holdings_list_final)

    print("calc dist post getting: ",len(holdings_list))

    ## make joint list
    joint_list = JoinLists(holdings_list, holdings_list_final)

    print("len(joint_list): ",len(joint_list))

    pies_display,failed_add = DivideAmongstPies(joint_list, settings)

    return pies_display, failed_add











