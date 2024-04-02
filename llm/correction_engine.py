import utilities
import re
import json

class Correction_log:
    def __init__(self):
        self.incorrect_entry = { }
        self.correction_prompt = ""
        self.correction_response = ""
        self.extraction_prompt = ""
        self.extraction_response = ""
        self.extracted_correction = ""
        self.extraction_successful = False


class Corrector:

    def __init__(self, model, url = "http://localhost:11434/api/generate", json_correction_prompt_filepath = "/home/danielle/raha/llm/correction_prompts.json") -> None:
        self.correction_prompt_filepath = json_correction_prompt_filepath
        self.url = url
        self.model = model
        self.correction_log: Correction_log = Correction_log()

    def get_correction(self, incorrect_entry, incorrect_key, key_knowledge_prompt, key_knowledge):
        incorrect_entry_as_string = utilities.dict_to_string(incorrect_entry)
        corrector_prompt = self.create_corrector_prompt(incorrect_entry_as_string, key_knowledge_prompt, key_knowledge)
        llm_response_correction = self.send_correction_prompt_raw(corrector_prompt, incorrect_key)
        extraction_prompt = self.create_extraction_prompt(incorrect_entry_as_string, llm_response_correction)
        correction = self.send_extraction_prompt(extraction_prompt, incorrect_key)

        self.correction_log.incorrect_entry = incorrect_entry
        self.correction_log.correction_prompt = corrector_prompt
        self.correction_log.correction_response = llm_response_correction
        self.correction_log.extraction_prompt = extraction_prompt
        self.correction_log.extracted_correction = correction
        return correction

    def get_correction_log(self):
        return self.correction_log

    def extract_value_from_prompt(self, llm_response: str, incorrect_key: str) -> str:
        # Define the regex pattern
        pattern = rf"\b{incorrect_key}\b\s*:\s*([^,]*)"
    
        # Search for the pattern in the text
        match = re.search(pattern, llm_response)
        
        # If a match is found, return the value
        if match:
            return match.group(1)
        else:
            return "Key not found."

    def add_incorrect_entry_to_prompt(self, correction_prompt: str, incorrect_entry: str) -> str:
        correction_prompt_parts = correction_prompt.split("[Incorrect entry]")
        correction_prompt_draft = correction_prompt_parts[0]
        correction_prompt_draft += incorrect_entry
        correction_prompt_draft += correction_prompt_parts[1]
        return correction_prompt_draft


    def create_corrector_prompt(self, incorrect_entry: str, key_knowledge_prompt: str, key_knowledge):
        correction_info = utilities.load_prompts(self.correction_prompt_filepath)
        correction_prompt_draft = correction_info["correction_prompt_2"]
        correction_prompt_final = "<s>[INST] " + key_knowledge_prompt + "[INST] " + key_knowledge + "</s>"
        correction_prompt_final += "[INST]" + self.add_incorrect_entry_to_prompt(correction_prompt_draft, incorrect_entry) + "[INST]"

        return correction_prompt_final

    def create_extraction_prompt(self, incorrect_entry: str, llm_correction: str) -> str:
        correction_info = utilities.load_prompts(self.correction_prompt_filepath)

        corrector_prompt_draft = correction_info["correction_prompt_2"]
        corrector_prompt = self.add_incorrect_entry_to_prompt(corrector_prompt_draft, incorrect_entry)

        extraction_prompt_draft = correction_info["extraction_prompt"]
        extraction_prompt_final = "<s>[INST] " + corrector_prompt + "[INST] " + llm_correction + "</s>"
        extraction_prompt_final  += "[INST]" + extraction_prompt_draft + "[INST]"

        return extraction_prompt_final


    def send_correction_prompt_raw(self, prompt: str, incorrect_key: str, ) -> str:
        print("----------------Correction prompt-----------------")
        print(prompt)
        template = r"{{ .System }} {{ .Prompt }}"
        llm_response = utilities.send_request(prompt, self.model, self.url, template)
        return llm_response

    def send_correction_prompt(self, prompt: str, incorrect_key: str) -> str:
        template = r"{{ .System }} {{ .Prompt }}"
        llm_response = utilities.send_request(prompt, self.model, self.url, template)
        correction = self.extract_value_from_prompt(llm_response, incorrect_key)
        return correction

    def send_correction_prompt_dict(self, prompt: str, incorrect_key: str) -> dict:
        template = r"{{ .System }} {{ .Prompt }}"
        llm_response = utilities.send_request(prompt, self.model, self.url, template)
        llm_response_list = re.split(r"[{}]", llm_response)
        llm_json = r"{" + llm_response_list[1] + r"}"
        correction_dict = json.loads(llm_json)
        return correction_dict

    def send_extraction_prompt(self, prompt: str, incorrect_key: str) -> str:
        template = r"{{ .System }} {{ .Prompt }}"
        print("----------------Extraction prompt-----------------")
        print(prompt)
        llm_response = utilities.send_request(prompt, self.model, self.url, template)
        self.correction_log.extraction_response = llm_response
        llm_response_list = re.split(r"[{}]", llm_response)
        llm_json = r"{" + llm_response_list[1] + r"}"
        try:
            correction_dict = json.loads(llm_json)
        except:
            return "Key not found"
        if incorrect_key not in correction_dict:
            return "Key not found"
        correction = correction_dict[incorrect_key]
        self.correction_log.extraction_successful = True
        return correction
    
    def add_entries_and_key_to_prompt(self, few_shot_prompt:str, incorrect_entry, incorrect_and_correct_entries, incorrect_key):
        prompt = few_shot_prompt
        for entry in incorrect_and_correct_entries:
            prompt = prompt.replace("[Incorrect entry]", utilities.dict_to_string(entry[0]), 1)
        for entry in incorrect_and_correct_entries:
            prompt = prompt.replace("[Correct entry]", utilities.dict_to_string(entry[1]), 1)

        prompt = prompt.replace("[Chosen Incorrect entry]", utilities.dict_to_string(incorrect_entry), 1)
        prompt = prompt.replace("[Keyname]", incorrect_key, 1)
        return prompt


    def create_few_shot_correction_prompt(self, incorrect_entry: str, incorrect_and_correct_entries: list, incorrect_key:str):
        prompts = utilities.load_prompts(self.correction_prompt_filepath)
        few_shot_prompt_draft = prompts["correction_prompt_few_shot"]
        few_shot_prompt_with_incorrect_entries = self.add_entries_and_key_to_prompt(few_shot_prompt_draft, incorrect_entry, incorrect_and_correct_entries, incorrect_key)
        return few_shot_prompt_with_incorrect_entries


if __name__ == "__main__":
    clean_filepath_csv = "/home/danielle/raha/datasets/beers/clean.csv"
    dirty_filepath_csv="/home/danielle/raha/datasets/beers/dirty.csv" 
    clean_entries, key = utilities.read_csv_to_dict(clean_filepath_csv)
    dirty_entries, key = utilities.read_csv_to_dict(dirty_filepath_csv)
    clean_entries_list= utilities.csv_to_dict_list(clean_filepath_csv)
    dirty_entries_list= utilities.csv_to_dict_list(dirty_filepath_csv)
    error_database = utilities.compare_datasets(clean_entries, dirty_entries)
    corrector = Corrector("mistral")

    key_knowledge_prompt = """Look at the following semantically and syntactically correct entries: { "index" : "2255" ,  "id" : "1723" ,  "beer-name" : "Hop Nosh IPA" ,  "style" : "American IPA" ,  "ounces" : "12" ,  "abv" : "0.073" ,  "ibu" : "83" ,  "brewery_id" : "159" ,  "brewery-name" : "Uinta Brewing Company" ,  "city" : "Salt Lake City" ,  "state" : "UT" }, { "index" : "151" ,  "id" : "2503" ,  "beer-name" : "Hop A-Peel" ,  "style" : "American Double / Imperial IPA" ,  "ounces" : "16" ,  "abv" : "0.075" ,  "ibu" : "115" ,  "brewery_id" : "72" ,  "brewery-name" : "Atwater Brewery" ,  "city" : "Detroit" ,  "state" : "MI" }, { "index" : "1" ,  "id" : "1436" ,  "beer-name" : "Pub Beer" ,  "style" : "American Pale Lager" ,  "ounces" : "12" ,  "abv" : "0.05" ,  "ibu" : "" ,  "brewery_id" : "408" ,  "brewery-name" : "10 Barrel Brewing Company" ,  "city" : "Bend" ,  "state" : "OR" }, { "index" : "213" ,  "id" : "1806" ,  "beer-name" : "Hoptopus Double IPA" ,  "style" : "American Double / Imperial IPA" ,  "ounces" : "16" ,  "abv" : "0.088" ,  "ibu" : "108" ,  "brewery_id" : "306" ,  "brewery-name" : "Beach Brewing Company" ,  "city" : "Virginia Beach" ,  "state" : "VA" }, { "index" : "22" ,  "id" : "1036" ,  "beer-name" : "Lower De Boom" ,  "style" : "American Barleywine" ,  "ounces" : "8.4" ,  "abv" : "0.099" ,  "ibu" : "92" ,  "brewery_id" : "368" ,  "brewery-name" : "21st Amendment Brewery" ,  "city" : "San Francisco" ,  "state" : "CA" }, { "index" : "63" ,  "id" : "1165" ,  "beer-name" : "Colorado Native" ,  "style" : "American Amber / Red Lager" ,  "ounces" : "12" ,  "abv" : "0.055" ,  "ibu" : "26" ,  "brewery_id" : "462" ,  "brewery-name" : "AC Golden Brewing Company" ,  "city" : "Golden" ,  "state" : "CO" }, { "index" : "241" ,  "id" : "1762" ,  "beer-name" : "Hemlock Double IPA" ,  "style" : "American Double / Imperial IPA" ,  "ounces" : "12" ,  "abv" : "0.095" ,  "ibu" : "104" ,  "brewery_id" : "220" ,  "brewery-name" : "Big Choice Brewing" ,  "city" : "Broomfield" ,  "state" : "CO" }, { "index" : "141" ,  "id" : "428" ,  "beer-name" : "Shiva IPA" ,  "style" : "American IPA" ,  "ounces" : "12" ,  "abv" : "0.06" ,  "ibu" : "69" ,  "brewery_id" : "528" ,  "brewery-name" : "Asheville Brewing Company" ,  "city" : "Asheville" ,  "state" : "NC" }, { "index" : "526" ,  "id" : "2067" ,  "beer-name" : "Dead-Eye DIPA" ,  "style" : "American Double / Imperial IPA" ,  "ounces" : "16" ,  "abv" : "0.09" ,  "ibu" : "130" ,  "brewery_id" : "230" ,  "brewery-name" : "Cape Ann Brewing Company" ,  "city" : "Gloucester" ,  "state" : "MA" }, { "index" : "288" ,  "id" : "2634" ,  "beer-name" : "Nordskye" ,  "style" : "American IPA" ,  "ounces" : "12" ,  "abv" : "0.048" ,  "ibu" : "47" ,  "brewery_id" : "12" ,  "brewery-name" : "Blackrocks Brewery" ,  "city" : "Marquette" ,  "state" : "MI" }. Now look at the values of the key ibu. How are the values formatted and what kind of semantic and syntactic form do they take?"""
    key_knowledge_generated = """ The key "ibu" stands for International Bitterness Units, which is a standard measure of bitterness in beer. The values associated with this key are integers representing the number of IBUs for each beer entry. The values are syntactically formatted as simple integers, without any additional characters or formatting. Semantically, they represent the level of bitterness for a specific beer style."""
#    correction = corrector.get_correction(dirty_entry, "ibu", key_knowledge_prompt, key_knowledge_generated)
#    print(f"The correction by the LLM is {correction}")
    incorrect_and_correct_entries = []
    
    for entry in error_database["ibu"][0:3]:
        for clean_entry in clean_entries_list:
            if entry[key] != clean_entry[key]:
                continue
            else:
                incorrect_and_correct_entries.append([entry, clean_entry])

    all_chosen_dirty_entries = []
    for entry in incorrect_and_correct_entries:
        all_chosen_dirty_entries.append(entry[0])

    dirty_entry_to_correct = {}

    for dirty_entry in error_database["ibu"]:
        if dirty_entry not in all_chosen_dirty_entries:
            dirty_entry_to_correct = dirty_entry
            break
    
    few_shot_prompt = corrector.create_few_shot_correction_prompt(dirty_entry_to_correct, incorrect_and_correct_entries, "ibu")
    print(few_shot_prompt)