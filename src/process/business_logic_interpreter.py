import logging
import json
import pandas
import numpy as np
import datetime

NA_FLAG = "AUTOMATED RESPONSE UNAVAILABLE"
UNEXPECTED_INPUT = "UNEXPECTED OR MISSING INPUT"
IN_YES  = "Y"
IN_NO   = "N"
OUT_YES = "YES"
OUT_NO  = "NO"
OUT_YES_PI = "YES, according to PI – verify"
AWARD_BALANCE_THRESHOLD = 0.25


logger = logging.getLogger(__name__)

def process_query_result(df):
    
    """
    Input:  query results as a dataframe; dataframe is assumed to be a SINGLE ROW, column names refer
            to names of columns in the database that are used to answer questions on the ERM.
        
    Output: JSON mapping the abbreviation for each question in the form to its answer.
    """
    
    ri1_ = ri1()
    
    authorized_amount = df.loc[0, "AuthorizedAmount"]
    billed_to_date_amt = df.loc[0, "BilledToDateAmount"]
    
    ri2_ = ri2(authorized_amount, billed_to_date_amt)
    
    # needs to be converted back to numerical form to enable computations below 
    award_balance = float(ri2_.replace("$", "")) 
    
    ri3_ = ri3(authorized_amount, billed_to_date_amt)
    
    ri4_ = ri4(award_balance, authorized_amount)
    
    ri5_ = ri5()
    
    is_temporary_extension_request = df.loc[0, "isTemporaryExtensionRequest"]
    
    ri6_ = ri6(is_temporary_extension_request)
    
    is_new_cost_share = df.loc[0, "isNewCostShare"]
    ri7_ = ri7(is_new_cost_share)
    
    is_human_subjects = df.loc[0, "isHumanSubjects"]
    ri8_ = ri8(is_human_subjects)
    
    is_animal_use = df.loc[0, "isAnimalUse"]
    ri9_ = ri9(is_animal_use)
    
    ri10_ = ri10()
    
    num_prior_ext = df.loc[0, "numberPriorExtensions"] # this will be separate query
    
    is_nih_2plus_ext = df.loc[0, "isNIH2PlusExtension"]
    if is_nih_2plus_ext is not None:
        ri11_ = ri11(num_prior_ext, is_nih_2plus_ext)
    else:
        ri11_ = ri11(num_prior_ext)
    
    sponsor_has_timeframe = df.loc[0, "sponsorHasDeadline"]
    sponsor_deadline_date = df.loc[0, "sponsorDeadlineDate"]
    award_schedule_end_date = df.loc[0, "AwardScheduleEndDate"]
    
    ri12_ = ri12(sponsor_has_timeframe, sponsor_deadline_date, award_schedule_end_date)
    
    sponsor_entity_type = df.loc[0, "PrimeSponsorFECDMEntityType"]
    project_type = df.loc[0, "projectType"]
    ri13_ = ri13(sponsor_entity_type, project_type)
    
    ri14_ = ri14()
    
    
    award_type = df.loc[0, "AwardLineType"]
    ri15_ = ri15(award_type)
    
    num_outstanding_payments = df.loc[0, "numberOutStandingPayments"]  # this will be a separate query - from edw
    ri16_ = ri16(num_outstanding_payments)
    
    all_deliverables_submitted = df.loc[0, "allDeliverablesSubmitted"]
    ri17_ = ri17(all_deliverables_submitted)
    
    # Fill in the output JSON
    num_items = 17
    out_dict = dict()
    
    out_dict["pi_name"] = df.loc[0, "pi_name"]
    out_dict["mod_id"] = df.loc[0, "mod_id"]
    
    for i in range(1, num_items + 1):
        key = f"ri{i}"
        value = locals()[f"ri{i}_"]
        
        out_dict[key] = value
    
    # Return in JSON format
    return json.dumps(out_dict)       

# helper function – translates database encoding for YES/NO to preferred output formatting
def is_yes(db_yes_no, pi_form=False):
    
    """
    The database encodes "YES" and "Y" and "NO" as "N"; this helper function translates

    Input: "Y" or "N" from database
    Output: "YES" or "NO"
    """

    if isinstance(db_yes_no, str) and ((db_yes_no == IN_YES) | (db_yes_no == IN_NO)):

        if db_yes_no == IN_YES:
            # sometimes, the source of data is the PI form; this is less reliable than 
            # data taken directly from the database, so we want to qualify it
            if pi_form:
                return OUT_YES_PI
            else:
                return OUT_YES
        else:
            return OUT_NO
    else:
        logger.error("Unexpected input – expected 'Y' or 'N'")

# formatting helper – outputs "YES" if input is TRUE (bool), "NO" otherwise
def tf_to_yn(condition):
    
    if isinstance(condition, (bool, np.bool_)):
        if condition:
            return OUT_YES
        else:
            return OUT_NO
    else:
        raise Exception(f"Expected boolean input, got {type(condition)} instead")

# PLACEHOLDER: SFI current? – not possible from RAD only
def ri1():
    
    """
    Input:
    Output: String – "YES/NO" specifying if SFI is current
    """
    return NA_FLAG # not possible with just RAD data as of 1/23

# remaining balance $$? --- TO BE UPDATED WHEN WE GET MORE INFO IN RAD
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
# requires processing - PI form + RAD
def ri5():

    return NA_FLAG

# PLACEHOLDER for temporary request -- need to determine variable to use as input
def ri6(is_temporary_extension_request):
    
    # use first character of "Yes" or "No" to answer
    return is_yes(is_temporary_extension_request[0], pi_form=True)

# PLACEHOLDER for new cost share -- need to determine variable to use as input
def ri7(is_new_cost_share):
    
    return is_yes(is_new_cost_share[0])
    
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
def ri11(number_of_prior_extensions, nih_2plus_ext=""):
    
    if isinstance(nih_2plus_ext, str):
        return is_yes(
            nih_2plus_ext[0]
        )
    
    if isinstance(number_of_prior_extensions, (int, float)):
        return tf_to_yn(
            number_of_prior_extensions > 1
        )
        
    else:
        return UNEXPECTED_INPUT

# request to extend is within sponsor's timeframe?
# NEED TO REFINE BUSINESS LOGIC
def ri12(sponsor_has_timeframe, sponsor_deadline_date):
    
    if sponsor_has_timeframe:
        
        try:
            
            today = datetime.date.today()
        
            return today < sponsor_deadline_date
        
        except:
            return UNEXPECTED_INPUT
    
    else:
        return NA_FLAG
        

# is this a federal contract?
def ri13(sponsor_entity_type, project_type):
    
    """
    Input: strings indicating sponsor type (federal gov't, industry, etc.) and project type (grant, project, etc.)
    Output: "YES" if federal contract, "NO" otherwise
    """
    
    if (isinstance(sponsor_entity_type, str) and isinstance(project_type, str)):
        
        return tf_to_yn(
            (sponsor_entity_type == "Federal Government") and (project_type == "Contract")
        )
    
    else:
        return UNEXPECTED_INPUT

# PLACEHOLDER
# E-verify question; not possible with RAD data alone
def ri14():
    return NA_FLAG

# PLACEHOLDER - fixed price terms?
def ri15(award_type):
    
    if isinstance(award_type, str):
        return is_yes((
            award_type == "FIXED AMOUNT"
        ))
    
    else:
        return UNEXPECTED_INPUT

# PLACEHOLDER - paid in full?
def ri16(number_outstanding_payments):
    
    if isinstance(number_outstanding_payments, (float, int)):
        return tf_to_yn(
            number_outstanding_payments < 1
        )
    
    else:
        return UNEXPECTED_INPUT

# PLACEHOLDER
# All deliverables submitted?; not possible with RAD data alone
def ri17(all_deliverables_submitted):
    
    if isinstance(all_deliverables_submitted, str):
        return NA_FLAG
    
    else:
        return UNEXPECTED_INPUT