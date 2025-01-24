import logging
import json
import pandas

NA_FLAG = "AUTOMATED RESPONSE UNAVAILABLE"
IN_YES  = "Y"
IN_NO   = "N"
OUT_YES = "YES"
OUT_NO  = "NO"
AWARD_BALANCE_THRESHOLD = 0.25

logger = logging.getLogger(__name__)

def process_query_result(df):
    
    """
    Input:  query results as a dataframe; dataframe is assumed to be a SINGLE ROW, column names refer
            to names of columns in the database that are used to answer questions on the ERM
        
    Output: JSON mapping the abbreviation for each question in the form to its answer
    """
    
    authorized_amount = df.iloc[0,"awrd.AuthorizedAmount"]
    billed_to_date_amt = df.iloc[0,"awrd.BilledToDateAmount"]
    
    ri1 = ri1()
    
    award_balance = ri2(authorized_amount, billed_to_date_amt)
    
    ri3 = ri3(authorized_amount, billed_to_date_amt)
    
    # TODO: check notes and validate w/ Ed – authorized amount or total award?
    ri4 = ri4(award_balance, authorized_amount)
    
    ri5 = ri5()
    
    ri6 = ri6()
    
    ri7 = ri7()
    
    is_human_subjects = df.iloc[0, "egc1.isHumanSubjects"]
    
    ri8 = ri8(is_human_subjects)
    
    is_animal_use = df.iloc[0, "egc1.isAnimalUse"]
    
    ri9 = ri9(is_animal_use)
    
    ri10 = ri10()
    
    num_prior_ext = df.iloc[0, "numberPriorExtensions"]
    
    ri11 = ri11(num_prior_ext)
    
    sponsor_has_timeframe = df.iloc[0, "mod.sponsorHasDeadline"]
    sponsor_deadline_date = df.iloc[0, "egc1.sponsorDeadlineDate"]
    award_schedule_end_date = df.iloc[0, "awrd.AwardScheduleEndDate"]
    
    ri12 = ri12(sponsor_has_timeframe, sponsor_deadline_date, award_schedule_end_date)
    
    sponsor_entity_type = df.iloc[0, "egc1.FECDMSponsorEntityType"]
    project_type = df.iloc[0, "egc1.projectType"]
    ri13 = ri13(sponsor_entity_type, project_type)
    
    ri14 = ri14()
    
    num_outstanding_payments = df.iloc[0, "numberOutstandingPayments"]
    ri15 = ri15(num_outstanding_payments)
    
    ri16 = ri16()
    
    ri17 = ri17()
    
    # fill in the output JSON
    
    num_items = 17
    out_dict = dict()
    
    for i in range(1, num_items + 1):
        key = f"ri{i}"
        value = locals()[key]
        
        out_dict[key] = value
    
    # return in JSON format
    return json.dumps(out_dict)        


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


# PLACEHOLDER: SFI current? – not possible from RAD only
def ri1():
    
    """
    Input:
    Output: String – "YES/NO" specifying if SFI is current
    """
    return NA_FLAG # not possible with just RAD data as of 1/23

# remaining balance $$?
def ri2(authorized_amount, billed_to_date_amt):
    
    """
    Input: floats representing the amounts ($) authorized and billed, respectively, for the award
    Output:  Formatted string – remaining award balance dollar amount
    """
    remaining = authorized_amount - billed_to_date_amt

    formatted_remaining = f"${remaining:.2f}"

    return formatted_remaining

# is the award in deficit?
def ri3(authorized_amount, billed_to_date_amt):
    
    """
    Input: floats representing the amounts ($) authorized and billed, respectively, for the award
    Output: "YES" if billed amt. exceeds authorized; "NO" otherwise
    """

    return tf_to_yn((billed_to_date_amt > authorized_amount))

# is the award balance greater than 25% of the total award?
def ri4(award_balance, total_award):
    
    ### TODO: actual logic is more nuanced; need to modify
    ### In most cases, the total award portion of this calculation
    ### can disregard the cost share; but if there is a new cost share
    ### associated with this request, the NEW cost share must be 
    ### included
    
    return tf_to_yn(
        (award_balance / total_award) >= AWARD_BALANCE_THRESHOLD
    )
    
# award lines listed or "extend all" indicated
def ri5():

    return NA_FLAG

# PLACEHOLDER for temporary request -- need to determine variable to use as input
def ri6():
    
    return NA_FLAG

# PLACEHOLDER for new cost share -- need to determine variable to use as input
def ri7():
    
    return NA_FLAG
    
# Human Subjects?
def ri8(is_human_subjects):
    
    """
    Input: varchar from database – "Y" / "N"
    Output: string "YES/NO"
    """

    return is_yes(is_human_subjects)

# Animal Use?
def ri9(is_animal_use):
    
    """
    Input: varchar from database – "Y" / "N"
    Output: string "YES/NO"
    """

    return is_yes(is_animal_use)

# PLACEHOLDER - prior approval required
# Not possible with only RAD data
def ri10():
    return NA_FLAG

# has the project been previously extended?
def ri11(number_of_prior_extensions):
    return tf_to_yn(
        number_of_prior_extensions > 1
    )

# request to extend is within sponsor's timeframe?
def ri12(sponsor_has_timeframe, sponsor_deadline_date, award_schedule_end_date):
    
    return NA_FLAG

# is this a federal contract?
def ri13(sponsor_entity_type, project_type):
    
    """
    Input: strings indicating sponsor type (federal gov't, industry, etc.) and project type (grant, project, etc.)
    Output: "YES" if federal contract, "NO" otherwise
    """
    return tf_to_yn(
        (sponsor_entity_type == "Federal Government") and (project_type == "Contract")
    )

# PLACEHOLDER
# E-verify question; not possible with RAD data alone
def ri14():
    return NA_FLAG

# PLACEHOLDER
def ri15(number_outstanding_payments):
    
    return tf_to_yn(
        number_outstanding_payments > 0
    )

# PLACEHOLDER
# All deliverables submitted?; not possible with RAD data alone
def ri16():
    
    return NA_FLAG

def ri17():
    
    return NA_FLAG