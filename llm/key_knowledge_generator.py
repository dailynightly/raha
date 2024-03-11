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

if __name__ == "__main__":
    prompt = """Look at the following data entries:
Correct entry: Name: Psycho, Year: 1960, Release Date: 8 September 1960 (USA), Director: Alfred Hitchcock, Creator: Joseph Stefano,Robert Bloch, Actors: Anthony Perkins,Janet Leigh,Vera Miles, Language: English, Country: USA, Duration: 109 min, RatingValue: 8.6, RatingCount: 379998.0, ReviewCount: 976 user,290 critic, Genre: Horror,Mystery,Thriller, Filming Locations: Title and Trust Building, 114 West Adams Street, downtown Phoenix, Arizona, USA, Description: A Phoenix secretary steals $40,000 from her employer's client, goes on the run and checks into a remote motel run by a young man under the domination of his mother. 
Correct entry: Name: Day of the Dead, Year: 1985, Release Date: 19 July 1985 (USA), Director: George A. Romero, Creator: George A. Romero, Actors: Lori Cardille,Terry Alexander,Joseph Pilato, Language: English, Country: USA, Duration: 96 min, RatingValue: 7.2, RatingCount: 46421.0, ReviewCount: 414 user,177 critic, Genre: Action,Drama,Horror, Filming Locations: Sanibel Island, Florida, USA, Description: A small group of military officers and scientists dwell in an underground bunker as the world above is overrun by zombies. 
Correct entry: Name: Foreign Correspondent, Year: 1940, Release Date: 16 August 1940 (USA), Director: Alfred Hitchcock, Creator: Charles Bennett,Joan Harrison, Actors: Joel McCrea,Laraine Day,Herbert Marshall, Language: English,Dutch,Latvian, Country: USA, Duration: 120 min, RatingValue: 7.6, RatingCount: 12684.0, ReviewCount: 124 user,73 critic, Genre: Romance,Thriller,War, Filming Locations: Hotel de l'Europe, Nieuwe Doelenstraat 2-14, Amsterdam, Netherlands, Description: On the eve of WWII, a young American reporter tries to expose enemy agents in London. Now look at the key RatingCount. How are the values formatted and what kind of semantic and syntactic form do they take?
"""
    llm_response = ask_llm_for_knowledge(prompt, "mistral")
    print(llm_response)