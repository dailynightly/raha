from typing import Tuple
import utilities
import random
import Levenshtein as lev

class Key_knowledge_block:
    def __init__(self, prompt:str, key_knowledge:str, incorrect_entry:str):
        self.prompt = prompt
        self.key_knowledge = key_knowledge
        self.incorrect_key = incorrect_entry

    def get_prompt(self):
        return self.prompt
    
    def get_key_knowledge(self):
        return self.key_knowledge
    
    def get_incorrect_key(self):
        return self.incorrect_key


class Key_knowledge_generator:
    def __init__(self, clean_entries: list, knowledge_prompt_filepath: str, model:str):
        self.clean_entries = clean_entries
        self.key_knowledge_store: dict = { } #stores key_knowledge for every key, that has been generated already
        self.knowledge_prompts = utilities.load_prompts(knowledge_prompt_filepath)
        self.model = model
        self.knowledge_prompt_created = None
        self.incorrect_key = None
        self.llm_knowledge_response = None

    def get_chosen_entries(self, amount: int, incorrect_key) -> list:
        #add first entry
        tuples_collected = []
        all_entries_with_same_error_key = self.clean_entries[:] #shallow copy all entries
        random_entry_index = random.randint(0, len(all_entries_with_same_error_key)-1)
        random_entry = all_entries_with_same_error_key[random_entry_index]
        all_entries_with_same_error_key.remove(random_entry)
        tuples_collected.append(random_entry)

        while len(tuples_collected) < amount:
            most_different_entry = self.get_most_different_entry(all_entries_with_same_error_key, tuples_collected, incorrect_key)
            tuples_collected.append(most_different_entry)
            all_entries_with_same_error_key.remove(most_different_entry)
                
        return tuples_collected

    def get_most_different_entry(self, entries: list, tuples_already_chosen: list, incorrect_key):
        most_different_entry = entries[0]
        most_different_entry_distance = self.get_levenshtein_distance_for_entry(tuples_already_chosen, most_different_entry, incorrect_key)
        for entry in entries:
            different_entry_candidate_score = self.get_levenshtein_distance_for_entry(tuples_already_chosen, entry, incorrect_key)
            if different_entry_candidate_score > most_different_entry_distance:
                most_different_entry = entry
                most_different_entry_distance = different_entry_candidate_score
        
        return most_different_entry
                
    def get_levenshtein_distance_for_entry(self, already_selected_entries: list, entry2: dict, incorrect_key):
        levenshtein_distance = 0
        for entry in already_selected_entries:
            levenshtein_distance += lev.distance(entry[incorrect_key], entry2[incorrect_key])
        return levenshtein_distance

    def add_entries_and_incorrect_key_to_prompt(self, prompt_draft: str, entries: list, incorrect_key: str) -> str:

        all_entries = ""
        for i in range(len(entries) - 1):
            all_entries += utilities.dict_to_string(entries[i]) + ", "
        all_entries += utilities.dict_to_string(entries[-1])

        prompt_entry_splits = prompt_draft.split("[Entries]")
        prompt = prompt_entry_splits[0] + all_entries + prompt_entry_splits[1]

        incorrect_key_split = prompt.split("[Keyname]")
        final_prompt = incorrect_key_split[0]
        final_prompt += incorrect_key
        final_prompt += incorrect_key_split[1]

        return final_prompt
        
    def create_knowledge_generation_prompt(self, incorrect_key:str, amount_entries_wanted: int) -> str:
        self.incorrect_key = incorrect_key
        knowledge_prompt_draft = self.knowledge_prompts["knowledge_prompt"]
        chosen_entries = self.get_chosen_entries(amount_entries_wanted, incorrect_key)
        self.knowledge_prompt_created = self.add_entries_and_incorrect_key_to_prompt(knowledge_prompt_draft, chosen_entries, incorrect_key)
        return self.knowledge_prompt_created

    def ask_llm_for_knowledge(self, prompt: str, model: str, url: str = "http://localhost:11434/api/generate") -> str:
        self.llm_knowledge_response = utilities.send_request(prompt, model, url)
        return self.llm_knowledge_response

    def get_key_knowledge_block(self, incorrect_key: str, amount_entries_wanted: int) -> Key_knowledge_block:
        self.create_knowledge_generation_prompt(incorrect_key, amount_entries_wanted)
        self.ask_llm_for_knowledge(self.knowledge_prompt_created, self.model)
        key_knowledge_block = Key_knowledge_block(self.knowledge_prompt_created, self.llm_knowledge_response, self.incorrect_key)
        return key_knowledge_block


if __name__ == "__main__":
    clean_filepath_csv= "/home/danielle/raha/datasets/beers/clean.csv"
    knowledge_prompt_filepath="/home/danielle/raha/llm/key_knowledge_prompts.json"
    model = "mistral"
    clean_entries = utilities.csv_to_dict_list(clean_filepath_csv)
    knowledge_generator = Key_knowledge_generator(clean_entries, knowledge_prompt_filepath, model)
    key_knowledge_block = knowledge_generator.get_key_knowledge_block("ibu", 10)

    print(key_knowledge_block.get_prompt())
    print(key_knowledge_block.get_incorrect_key())
    print(key_knowledge_block.get_key_knowledge())