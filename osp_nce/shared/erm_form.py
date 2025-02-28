import json


class Form:

    def __init__(self, input_data = None):
        if input_data:
            self.from_dict(input_data)
            return
        
        self.fields = {
            "SFI Current?": "No - Send email to research@uw.edu for review.",
            "Remaining Balance $$": "Check Award Portal for award balance.",
            "Is the award in deficit?": "Yes - PI must explain deficit & transfer costs to appropriate non-federal, non-sponsored departmental worktag or provide Sponsor assurance that further funding is forthcoming.",
            "Is the balance greater than 25% of the total award?": "Yes - PI must provide a programmatic explanation for a large balance.",
            "Award lines listed or 'extend all' indicated?": "Note in MOD Comments which award lines are to be extended if campus so indicates.",
            "Temporary Request?": "Include non-sponsored departmental worktag in MOD Comments & History.",
            "New Cost Share?": "Yes - Attach revised CS Addendum to MOD.",
            "Human Subjects?": "Yes - Verify and document IRB approval(s). Refer to Human Subjects Review Guidance.",
            "Animal Use?": "Yes - Verify and document IACUC approval(s). Refer to Animal Use Compliance Verification guidance.",
            "Prior Approval required?": "Federal award - Review Federal-Wide Research Terms & Conditions (RTCs) Prior Approval Matrix, Appendix A to confirm whether the award requires prior approval.",
            "Has the project previously been extended? Is this an NIH 2nd+ extension?": "Yes - Ensure that the Budget, Progress Report, and Programmatic Justification are included as 3 separate PDFs.",
            "Is the request to extend within Sponsor’s required timeframe?": "No - Extension requires Sponsor approval.",
            "Is this a federal contract?": "Yes - Extension requires Sponsor approval.",
            "Fixed Price terms?": "No - Extension requires Sponsor approval. Review fixed price terms.",
            "Paid in full?": "No - Check Award Portal. If outstanding payments exist, deny extension until PI/campus resolve with Sponsor.",
            "All deliverables submitted?": "No - Extension requires Sponsor approval. Review fixed price terms.",
            "FAR clause 52.222-54 (e-verify)?": "Yes - Forward E-verify process to your campus contact & state in MOD comments that e-verify is required.",
            "Review Notes": "Enter any additional notes here.",
        }
        self.fields_map = {
            "ri1": "SFI Current?",
            "ri2": "Remaining Balance $$",
            "ri3": "Is the award in deficit?",
            "ri4": "Is the balance greater than 25% of the total award?",
            "ri5": "Award lines listed or 'extend all' indicated?",
            "ri6": "Temporary Request?",
            "ri7": "New Cost Share?",
            "ri8": "Human Subjects?",
            "ri9": "Animal Use?",
            "ri10": "Prior Approval required?",
            "ri11": "Has the project previously been extended? Is this an NIH 2nd+ extension?",
            "ri12": "Is the request to extend within Sponsor’s required timeframe?",
            "ri13": "Is this a federal contract?",
            "ri14": "FAR clause 52.222-54 (e-verify)?",
            "ri15": "Fixed Price terms?",
            "ri16": "Paid in full?",
            "ri17": "All deliverables submitted?",
            "review_notes": "Review Notes",
        }
        self.fields_map_pdf = {
            "pi_name": "PI Name",
            "mod_id": "MOD/Worktag ID",
            "ri1": "SFI",
            "ri2": "RemBal",
            "ri3": "Deficit?",
            "ri4": "Greater than 25%?",
            "ri5": "Award lines",
            "ri6": "TempReq",
            "ri7": "CostShare",
            "ri8": "HumSub",
            "ri9": "AnimalUse",
            "ri10": "PriorApp",
            "ri11": "PrevExt?",
            "ri12": "ExtendInTime?",
            "ri13": "FedContract?",
            "ri14": "FAR clause 5222254",
            "ri15": "Fixed Price terms",
            "ri16": "Paid in full",
            "ri17": "All deliverables  submitted",
            "review_notes": "Review Notes",
        }

        # Check if Fields Map keys are a subset of Fields Map PDF keys
        if not self.fields_map.keys() <= self.fields_map_pdf.keys():
            raise ValueError(
                "There was an error initializing the ERM form. \n"
                "Fields Map keys are not a subset of Fields Map PDF keys.\n"
                "To troubleshoot this, check the fields_map.json and fields_map_pdf.json files in the src/shared/form directory."
            )
        
        self.answers = {}

    def get_fields(self):
        return self.fields

    def get_fields_map(self):
        return self.fields_map

    def get_fields_map_pdf(self):
        return self.fields_map_pdf

    def fill_item(self, item_id, answer):
        self.answers[item_id] = answer

    def to_dict(self):
        return {
            "fields": dict(self.fields),
            "fields_map": dict(self.fields_map),
            "fields_map_pdf": dict(self.fields_map_pdf),
            "answers": dict(self.answers),
        }

    def from_dict(self, data):
        self.fields = data["fields"]
        self.fields_map = data["fields_map"]
        self.fields_map_pdf = data["fields_map_pdf"]
        self.answers = data["answers"]
