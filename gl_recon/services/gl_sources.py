# These will call your existing modules

def get_cbs_acquirer_withdrawal(date):
    # reuse your CBS parsing logic
    return Decimal("0.00")

def get_cbs_issuer_withdrawal(date):
    return Decimal("0.00")

def get_ntsl_settlement_total(date):
    # sum of ATMSettlementCycle.final_settlement_amount
    return Decimal("0.00")

