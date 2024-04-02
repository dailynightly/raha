import key_knowledge_generator
import correction_engine
import utilities
import os

def generate_knowledge_test_basic():
    model: str = "mistral"
    key_knowledge_prompts_path = "/home/danielle/raha/llm/key_knowledge_prompts.json"
    clean_csv_filepath: str = "/home/danielle/raha/datasets/beers/clean.csv"
    dirty_csv_filepath: str = "/home/danielle/raha/datasets/beers/dirty.csv"
    clean_entries = utilities.read_csv_to_dict(clean_csv_filepath)
    dirty_entries = utilities.read_csv_to_dict(dirty_csv_filepath)
    differences, key = utilities.compare_datasets(clean_dataset=clean_entries, dirty_dataset=dirty_entries)
    incorrect_key = list(differences.keys())[0]


    key_knowledge: str = key_knowledge_generator.create_knowledge_generation_prompt(clean_csv_filepath, incorrect_key, key_knowledge_prompts_path)
    print(key_knowledge)
    llm_response = key_knowledge_generator.ask_llm_for_knowledge(prompt=key_knowledge, model=model)
    return llm_response

def generate_correction_basic():
    model: str = "mistral"
    key_knowledge_prompt = """Look at the following data entries: Correct entry: src: aa, flight: AA-1733-ORD-PHX, sched_dep_time: 7:45 p.m., act_dep_time: 7:58 p.m., sched_arr_time: 10:30 p.m., act_arr_time: 10:30 p.m. Correct entry: src: aa, flight: AA-1640-MIA-MCO, sched_dep_time: 6:30 p.m., act_dep_time: 6:30 p.m., sched_arr_time: 7:25 p.m., act_arr_time: 7:25 p.m. Correct entry: src: aa, flight: AA-204-LAX-MCO, sched_dep_time: 11:25 p.m., act_dep_time: 11:25 p.m., sched_arr_time: 6:55 a.m., act_arr_time: 6:55 a.m. Now look at the key sched_arr_time. How are the values formatted and what kind of semantic and syntactic form do they take?"""
    key_knowledge = """The values of the key "sched_arr_time" in the provided data entries are formatted in a specific way. They are in a time format using the 12-hour clock system, with hours and minutes, followed by either "a.m." or "p.m." to indicate whether it's morning or afternoon/evening.

Here's how the values are formatted:

- 10:30 p.m.
- 7:25 p.m.
- 6:55 a.m.

In terms of semantic and syntactic forms, these values are structured as follows:

- Semantic Form: The semantic form of these values represents a specific time of the day, indicating when the scheduled arrival time of a flight is. It provides information about the hour and minute at which the flight is expected to arrive.
- Syntactic Form: The syntactic form follows a consistent pattern of "hh:mm a.m." or "hh:mm p.m." where "hh" represents the hour (with leading zero if it's a single digit), "mm" represents the minutes, and "a.m." or "p.m." indicates whether it's morning or evening.

These forms are commonly used to represent time in schedules and are easily understandable to people reading the data."""
    clean_csv_filepath: str = "/home/danielle/raha/datasets/flights/clean.csv"
    dirty_csv_filepath: str = "/home/danielle/raha/datasets/flights/dirty.csv"
    clean_entries = utilities.read_csv_to_dict(clean_csv_filepath)
    dirty_entries = utilities.read_csv_to_dict(dirty_csv_filepath)
    differences, key = utilities.compare_datasets(clean_dataset=clean_entries, dirty_dataset=dirty_entries)
    incorrect_entry = differences["sched_arr_time"][-1]
    incorrect_entry = utilities.dict_to_string(incorrect_entry)

    corrector_prompt = correction_engine.create_corrector_prompt(incorrect_entry,key_knowledge_prompt, key_knowledge)
    llm_response = correction_engine.send_correction_prompt(corrector_prompt, model, "sched_arr_time")

    return llm_response

if __name__ == "__main__":
    #print(generate_knowledge_test_basic())
    print(generate_correction_basic())