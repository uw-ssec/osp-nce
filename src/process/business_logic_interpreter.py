import logging

NA_FLAG = "N/A"
IN_YES = "Y"
IN_NO = "N"
OUT_YES = "YES"
OUT_NO = "NO"

logger = logging.getLogger(__name__)

# helper function – translates database encoding for YES/NO to preferred output formatting
def is_yes(db_yes_no):
    """
    The database encodes "YES" and "Y" and "NO" as "N"; this helper function translates
    
    Input: "Y" or "N" from database
    Output: "YES" or "NO"
    """
    
    if isinstance(db_yes_no, str) and (db_yes_no == IN_YES | db_yes_no == IN_NO):
        
        if db_yes_no == IN_YES:
            return OUT_YES
        else:
            return OUT_NO
    else:
        logger.error("Unexpected input – expected 'Y' or 'N'")

# foramtting helper – outputs "YES" if input is TRUE (bool), "NO" otherwise 
def tf_to_yn(condition):
    if isinstance(condition, bool):
        if condition:
            return OUT_YES
        else:
            return OUT_NO

# SFI current?
def ri1(sfi_data):
    """
    Input: 
    Output: String – "YES/NO" specifying if SFI is current
    """
    return NA_FLAG # need to better understand logic

# is the award in deficit?
def ri3(authorized_amount, billed_to_date_amt):
    
    """
    Input: floats representing the amounts ($) authorized and billed, respectively, for the award
    Output: "YES" if billed amt. exceeds authorized; "NO" otherwise
    """
    
    return tf_to_yn(
        (billed_to_date_amt > authorized_amount)
    )
    

def ri8(is_human_subjects):
    
    """
    Input: varchar from database – "Y" / "N"
    Output: string "YES/NO"
    """
    
    return is_yes(is_human_subjects)       

def ri9(is_animal_use):
    
    """
    Input: varchar from database – "Y" / "N"
    Output: string "YES/NO"
    """
    
    return is_yes(is_animal_use)