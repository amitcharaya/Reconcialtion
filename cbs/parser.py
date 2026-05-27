"""
Parser utilities for the cbs application. These functions convert bank/switch/NDPG source files into clean Python dictionaries or model-ready values.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from reconciliation.utils import normalize_date
def parse_cbs_record(line):

    file_type = line[112:113]

    common_data = {
        "stan_no": line[0:6].strip(),
        "card_no": line[6:22].strip(),
        "branch_id": line[83:87].strip(),
        "branch_name": line[87:112].strip(),
        "file_type": file_type,
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
            "acquirer_gl": line[43:57].strip(),
            "acquirer_gl_name": line[57:83].strip(),
        })

    elif file_type == "I":
        common_data.update({
            "customer_account_no": line[42:57].strip(),
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



