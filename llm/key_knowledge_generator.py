from typing import Tuple
import utilities

def get_clean_entries(clean_entries: list, amount: int) -> list:
    return clean_entries[0:amount]

def add_entries_and_incorrect_key_to_prompt(prompt_draft: str, entries: list, incorrect_key: str) -> str:
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
    
def create_knowledge_generation_prompt(clean_csv_path: str, incorrect_key:str, key_knowledge_prompt_path: str) -> str:
    all_clean_entries = utilities.csv_to_dict_list(clean_csv_path)
    knowledge_prompt_info = utilities.load_prompts(key_knowledge_prompt_path)
    knowledge_prompt_draft = knowledge_prompt_info["knowledge_prompt"]
    clean_entries = get_clean_entries(all_clean_entries, knowledge_prompt_info["entry_examples_needed"])
    final_prompt = add_entries_and_incorrect_key_to_prompt(knowledge_prompt_draft, clean_entries, incorrect_key)
    return final_prompt

def ask_llm_for_knowledge(prompt: str, model: str, url: str = "http://localhost:11434/api/generate") -> str:
    llm_response = utilities.send_request(prompt, model, url)
    return llm_response