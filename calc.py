import numpy as np
import pandas as pd
import numpy_financial as npf

def calc_loan_monthly_payment(principal, rate, term):
    # a = principal/((1+rate/12)**term-1)/(rate/12*(1+rate/12)**term)
    r = rate/12
    n = term
    if r <= 0:
        a = principal/term
    else:
        a = principal*(r*(1+r)**n)/((1+r)**n-1)
    return a

def total_payment(monthly_payment, term):
    return monthly_payment * term


def create_mortage_range(principal, term, rmax=0.1, rstep=0.00125):
    df = pd.DataFrame(data={'rate':np.arange(0,rmax+rstep,rstep)})
    df['monthly_payment'] = df.apply(lambda x: calc_loan_monthly_payment(principal, x['rate'], term), axis=1)
    df['total_payment'] = df.apply(lambda x: total_payment(x['monthly_payment'], term), axis=1)
    return df

def find_target_interest_rate(principal, term, target_payment):
    df = create_mortage_range(principal, term, rmax=0.185, rstep=0.00125)
    idx = df.loc[df['monthly_payment'] < target_payment, 'monthly_payment'].idxmax()
    return df.iloc[idx,:]['rate']

def amount_remaining(principal, monthly_payment, rate, months_remaining):
    '''
    B = (PMT/R) x (1 - (1/(1+R)^N) In the formula, "B" is the principal balance, 
    "PMT" is the monthly payment for principal and interest and "N" is the number of months remaining.
    "R" is your interest rate, but it's expressed as a monthly rate rather than an annual one. 
    To get the monthly rate, simply take your annual rate, expressed as a decimal, and divide it by 12. 
    If your annual rate is 6 percent, for example: R = 0.06/12 = 0.005.
    '''
    return (monthly_payment/(rate/12)) * (1 - (1/(1+(rate/12))**months_remaining))

def create_mortgage_table(principal, rate, term):
    df = pd.DataFrame(data={'month':np.arange(0,term+1,1)})
    monthly_payment = calc_loan_monthly_payment(principal, rate, term)
    
    df['months_remaining'] = term - df['month']                                     
    df['amount_remaining'] = df['months_remaining'].map(lambda x: amount_remaining(principal, monthly_payment, rate, x))
    return df

def find_break_even_interest(principal, new_term, target, current_rate, increment=0.00125):
    event_rate = current_rate
    while True:
        temp_total_payment = total_payment(calc_loan_monthly_payment(principal, event_rate, new_term),new_term)
        if temp_total_payment < target:
            break
        event_rate = event_rate - increment
        if event_rate < 0:
            break
    return event_rate