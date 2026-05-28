"""
Parser utilities for the cbs application. These functions convert bank/switch/NDPG source files into clean Python dictionaries or model-ready values.


"""

from reconciliation.utils import normalize_date



def parse_cbs_record(line):
    """parse CBS record for ATM transaction converts line into python dictionary
    Arguments:
          line {string} -- line to parse
    Returns:
          common_data {dictionary} -- Transaction fields as follows:.

          stan_no: {string} -- STAN number
          card_no: {string} -- Card number
          rrn_no: {string} -- RRN number
          account_type: {string} -- Account type
          branch_id: {string} -- Branch ID
          branch_name: {string} -- Branch name
          file_type: {string} -- File type
          dr_cr_flag: {string} -- DR flag
          txn_date: {string} -- Transaction date
          txn_time: {string} -- Transaction time
          settlement_date: {string} -- Settlement date
          settlement_time: {string} -- Settlement time
          atm_id: {string} -- ATM ID
          atm_location: {string} -- ATM location
          status: {string} -- Status of transaction
          raw_record: {string} -- Raw record
          acquirer_gl: {string} -- Acquirer GL number
          acquirer_gl_name: {string} -- Acquirer GL name
          customer_account_no: {string} -- Customer account number
          customer_name: {string} -- Customer name
          unknown_data: {string} -- Unknown data

    """

    file_type = line[112:113]

    common_data = {
        "stan_no": line[0:6].strip(),
        "card_no": line[6:25].strip(),
        "rrn_no": line[25:37].strip(),
        "account_type": line[37:39].strip(),

        "branch_id": line[83:87].strip(),
        "branch_name": line[87:112].strip(),
        "file_type": line[112:113].strip(),
        "dr_cr_flag": line[113:114].strip(),
        "txn_amount": int(line[114:129].strip()) / 100,
        "txn_date": normalize_date(line[129:135].strip()),
        "txn_time": line[135:141].strip(),
        "settlement_date":  normalize_date(line[141:147].strip()),
        "settlement_time": line[147:153].strip(),
        "atm_id": line[153:161].strip(),
        "atm_location": line[173:201].strip(),
        "status": line[201:203].strip(),
        "raw_record": line
    }

    if file_type == "A":
        common_data.update({
            "acquirer_gl": line[39:57].strip(),
            "acquirer_gl_name": line[57:83].strip(),
        })

    elif file_type == "I":
        common_data.update({
            "customer_account_no": line[39:57].strip(),
            "customer_name": line[57:83].strip(),
            "acquirer_bank": line[161:167].strip(),
        })

    elif file_type == "O":
        common_data.update({
            "customer_account_no": line[42:57].strip(),
            "customer_name": line[57:83].strip(),
            "unknown_data": line[161:173].strip(),
        })

    return common_data



