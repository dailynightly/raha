import utilities
import re
import random
import key_knowledge_generator

class Tuple_choosing_block:
    def __init__(self):
        self.tuple_candidates = []
        self.chosen_tuple_index: int = -1
        self.chosen_tuple = {}
        self.llm_chose_tuple = False
        self.tuple_choosing_prompt = ""
        self.tuple_choosing_response = ""
        self.tuple_extraction_prompt = ""
        self.tuple_extraction_response = ""

class Tuple_chooser:

    def __init__(self, error_dataset: dict, tuple_choosing_prompts_path: str = "/home/danielle/raha/llm/tuple_choosing_prompts.json"):
        self.error_dataset = error_dataset
        self.tuple_choosing_prompts = utilities.load_prompts(tuple_choosing_prompts_path)
        self.tuple_choosing_block: Tuple_choosing_block = Tuple_choosing_block()

    def get_tuples(self, incorrect_key: str, amount_needed: int) -> list:
        tuples_collected = []
        all_entries_with_same_error_key: list = self.error_dataset[incorrect_key]
        
        for i in range(amount_needed):
            while len(tuples_collected) <= i:
                random_entry_index = random.randint(0, len(all_entries_with_same_error_key)-1)
                random_entry = all_entries_with_same_error_key[random_entry_index]

                if random_entry in tuples_collected:
                    continue

                tuples_collected.append(random_entry)

        self.tuple_choosing_block.tuple_candidates = self.tuple_choosing_block.tuple_candidates + tuples_collected

        return tuples_collected


    def add_tuples_to_prompt(self, prompt_draft: str, entries: list, incorrect_key: str) -> str:
        prompt_entry_splits = prompt_draft.split("[Entry]")
        prompt = ""
        for i in range(len(entries)):
            prompt += prompt_entry_splits[i] + utilities.dict_to_string(entries[i])
        prompt += prompt_entry_splits[-1]

        incorrect_key_split = prompt.split("[Keyname]")
        final_prompt = incorrect_key_split[0]
        final_prompt += incorrect_key
        final_prompt += incorrect_key_split[1]

        return final_prompt

    def create_tuple_choosing_prompt(self, key_knowledge_block: key_knowledge_generator.Key_knowledge_block):

        tuple_chooser_prompt_draft = self.tuple_choosing_prompts["tuple_prompt"]
        tuples_needed = self.get_tuples(key_knowledge_block.get_incorrect_key(), self.tuple_choosing_prompts["tuples_needed"])
        tuple_chooser_prompt = self.add_tuples_to_prompt(tuple_chooser_prompt_draft, tuples_needed, key_knowledge_block.get_incorrect_key())
        tuple_chooser_prompt_final = "<s>[INST] " + key_knowledge_block.get_prompt() + "[INST] " + key_knowledge_block.get_key_knowledge() + "</s>"
        tuple_chooser_prompt_final  += "[INST]" + tuple_chooser_prompt + "[INST]"

        return tuple_chooser_prompt_final, tuples_needed

    def create_extraction_prompt(self, tuple_candidates: list, incorrect_key: str, llm_answer: str):
        tuple_chooser_prompt_draft = self.tuple_choosing_prompts["tuple_prompt"]
        tuples_needed = tuple_candidates
        tuple_chooser_prompt = self.add_tuples_to_prompt(tuple_chooser_prompt_draft, tuples_needed, incorrect_key)
        extraction_prompt_draft = self.tuple_choosing_prompts["tuples_extraction_prompt"]
        extraction_prompt_final = "<s>[INST] " + tuple_chooser_prompt + "[INST] " + llm_answer + "</s>"
        extraction_prompt_final  += "[INST]" + extraction_prompt_draft + "[INST]"

        return extraction_prompt_final
        

    def send_tuple_choosing_prompt_raw(self, prompt: str, model: str, url: str="http://localhost:11434/api/generate") -> str:
        print("----------------Tuple choosing prompt-----------------")
        print(prompt)
        template = r"{{ .System }} {{ .Prompt }}"
        llm_response = utilities.send_request(prompt, model, url, template)
        return llm_response

    def send_tuple_extraction_prompt(self, prompt: str, model: str, url: str="http://localhost:11434/api/generate") -> int:
        print("------Tuple extraction prompt--------")
        print(prompt)
        template = r"{{ .System }} {{ .Prompt }}"
        llm_response = utilities.send_request(prompt, model, url, template)

        self.tuple_choosing_block.tuple_extraction_response = llm_response
        # Regular expression pattern to match "I chose number x"
        pattern = r"I chose tuple number (\d+)"

        # Search for the pattern in the sentence
        match = re.search(pattern, llm_response)

        # If a match is found, extract and return the number
        if match:
            self.tuple_choosing_block.chosen_tuple_index = int(match.group(1)) - 1
            self.tuple_choosing_block.llm_chose_tuple = True
            return int(match.group(1)) - 1
        else:
            return None
        
    def get_tuple_choosing_block(self, key_knowledge_block: key_knowledge_generator.Key_knowledge_block, model:str):
        prompt, tuple_candidates = self.create_tuple_choosing_prompt(key_knowledge_block)
        llm_tuple_choose_response = self.send_tuple_choosing_prompt_raw(prompt, model)
        extraction_prompt = self.create_extraction_prompt(tuple_candidates, key_knowledge_block.get_incorrect_key(), llm_tuple_choose_response)
        tuple_index = self.send_tuple_extraction_prompt(extraction_prompt, model)

        if tuple_index:
            self.tuple_choosing_block.chosen_tuple = tuple_candidates[tuple_index]

        self.tuple_choosing_block.tuple_choosing_prompt = prompt
        self.tuple_choosing_block.tuple_choosing_response = llm_tuple_choose_response
        self.tuple_choosing_block.tuple_extraction_prompt = extraction_prompt

        return self.tuple_choosing_block

        


if __name__ == "__main__":
    clean_filepath_csv="/home/danielle/raha/datasets/beers/clean.csv"
    dirty_filepath_csv="/home/danielle/raha/datasets/beers/dirty.csv"
    clean_database: dict = utilities.read_csv_to_dict(clean_filepath_csv)
    dirty_database: dict = utilities.read_csv_to_dict(dirty_filepath_csv)
    error_database: dict = utilities.compare_datasets(clean_database, dirty_database)
    model = "mistral"
    
    key_knowledge_prompt = """Look at the following semantically and syntactically correct entries: { "index" : "2255" ,  "id" : "1723" ,  "beer-name" : "Hop Nosh IPA" ,  "style" : "American IPA" ,  "ounces" : "12" ,  "abv" : "0.073" ,  "ibu" : "83" ,  "brewery_id" : "159" ,  "brewery-name" : "Uinta Brewing Company" ,  "city" : "Salt Lake City" ,  "state" : "UT" }, { "index" : "151" ,  "id" : "2503" ,  "beer-name" : "Hop A-Peel" ,  "style" : "American Double / Imperial IPA" ,  "ounces" : "16" ,  "abv" : "0.075" ,  "ibu" : "115" ,  "brewery_id" : "72" ,  "brewery-name" : "Atwater Brewery" ,  "city" : "Detroit" ,  "state" : "MI" }, { "index" : "1" ,  "id" : "1436" ,  "beer-name" : "Pub Beer" ,  "style" : "American Pale Lager" ,  "ounces" : "12" ,  "abv" : "0.05" ,  "ibu" : "" ,  "brewery_id" : "408" ,  "brewery-name" : "10 Barrel Brewing Company" ,  "city" : "Bend" ,  "state" : "OR" }, { "index" : "213" ,  "id" : "1806" ,  "beer-name" : "Hoptopus Double IPA" ,  "style" : "American Double / Imperial IPA" ,  "ounces" : "16" ,  "abv" : "0.088" ,  "ibu" : "108" ,  "brewery_id" : "306" ,  "brewery-name" : "Beach Brewing Company" ,  "city" : "Virginia Beach" ,  "state" : "VA" }, { "index" : "22" ,  "id" : "1036" ,  "beer-name" : "Lower De Boom" ,  "style" : "American Barleywine" ,  "ounces" : "8.4" ,  "abv" : "0.099" ,  "ibu" : "92" ,  "brewery_id" : "368" ,  "brewery-name" : "21st Amendment Brewery" ,  "city" : "San Francisco" ,  "state" : "CA" }, { "index" : "63" ,  "id" : "1165" ,  "beer-name" : "Colorado Native" ,  "style" : "American Amber / Red Lager" ,  "ounces" : "12" ,  "abv" : "0.055" ,  "ibu" : "26" ,  "brewery_id" : "462" ,  "brewery-name" : "AC Golden Brewing Company" ,  "city" : "Golden" ,  "state" : "CO" }, { "index" : "241" ,  "id" : "1762" ,  "beer-name" : "Hemlock Double IPA" ,  "style" : "American Double / Imperial IPA" ,  "ounces" : "12" ,  "abv" : "0.095" ,  "ibu" : "104" ,  "brewery_id" : "220" ,  "brewery-name" : "Big Choice Brewing" ,  "city" : "Broomfield" ,  "state" : "CO" }, { "index" : "141" ,  "id" : "428" ,  "beer-name" : "Shiva IPA" ,  "style" : "American IPA" ,  "ounces" : "12" ,  "abv" : "0.06" ,  "ibu" : "69" ,  "brewery_id" : "528" ,  "brewery-name" : "Asheville Brewing Company" ,  "city" : "Asheville" ,  "state" : "NC" }, { "index" : "526" ,  "id" : "2067" ,  "beer-name" : "Dead-Eye DIPA" ,  "style" : "American Double / Imperial IPA" ,  "ounces" : "16" ,  "abv" : "0.09" ,  "ibu" : "130" ,  "brewery_id" : "230" ,  "brewery-name" : "Cape Ann Brewing Company" ,  "city" : "Gloucester" ,  "state" : "MA" }, { "index" : "288" ,  "id" : "2634" ,  "beer-name" : "Nordskye" ,  "style" : "American IPA" ,  "ounces" : "12" ,  "abv" : "0.048" ,  "ibu" : "47" ,  "brewery_id" : "12" ,  "brewery-name" : "Blackrocks Brewery" ,  "city" : "Marquette" ,  "state" : "MI" }. Now look at the values of the key ibu. How are the values formatted and what kind of semantic and syntactic form do they take?"""
    key_knowledge_generated = """ The key "ibu" stands for International Bitterness Units, which is a standard measure of bitterness in beer. The values associated with this key are integers representing the number of IBUs for each beer entry. The values are syntactically formatted as simple integers, without any additional characters or formatting. Semantically, they represent the level of bitterness for a specific beer style."""
    error_key = "ibu"

    key_knowledge_block = key_knowledge_generator.Key_knowledge_block(key_knowledge_prompt, key_knowledge_generated, error_key)

    tuple_chooser = Tuple_chooser(error_database)
    tuple_choosing_block = tuple_chooser.get_tuple_choosing_block(key_knowledge_block, model)
    print(tuple_choosing_block.chosen_tuple)
    print(tuple_choosing_block.chosen_tuple_index)
    print(tuple_choosing_block.llm_chose_tuple)
    print(tuple_choosing_block.tuple_candidates)