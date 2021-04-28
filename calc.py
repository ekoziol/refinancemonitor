import numpy as np
import pandas as pd

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

