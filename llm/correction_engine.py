import utilities
import re

def extract_value_from_prompt(llm_response: str, key: str) -> str:
    # Define the regex pattern
    pattern = rf"\b{key}\b\s*:\s*([^,]*)"
 
    # Search for the pattern in the text
    match = re.search(pattern, llm_response)
    
    # If a match is found, return the value
    if match:
        return match.group(1)
    else:
        return "Key not found."

def add_incorrect_entry_to_prompt(correction_prompt: str, incorrect_entry: str) -> str:
    correction_prompt_parts = correction_prompt.split("[Incorrect entry]")
    correction_prompt_draft = correction_prompt_parts[0]
    correction_prompt_draft += incorrect_entry
    correction_prompt_draft += correction_prompt_parts[1]
    return correction_prompt_draft


def create_corrector_prompt(incorrect_entry: str, key_knowledge: str):
    correction_info = utilities.load_prompts("/home/danielle/raha/llm/correction_prompts.json")
    correction_prompt_draft = correction_info["correction_prompt"]
    correction_prompt_final = key_knowledge
    correction_prompt_final += add_incorrect_entry_to_prompt(correction_prompt_draft, incorrect_entry)

    return correction_prompt_final

def send_correction_prompt(prompt: str, model: str, incorrect_key: str, url: str = "http://localhost:11434/api/generate") -> str:
    llm_response = utilities.send_request(prompt, model, url)
    correction = extract_value_from_prompt(llm_response, incorrect_key)
    return correction

