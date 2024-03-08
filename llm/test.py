import key_knowledge_generator
import utilities
import os

def generate_knowledge_test_basic():
    model: str = "mistral"
    key_knowledge_prompts_path = os.getcwd() + "key_knowledge_prompts.json"
    os.chdir("..")
    clean_csv_filepath: str = os.getcwd() + "/datasets/beers/clean.csv"
    dirty_csv_filepath: str = os.getcwd() + "/datasets/beers/dirty.csv"
    clean_entries = utilities.read_csv_to_dict(clean_csv_filepath)
    dirty_entries = utilities.read_csv_to_dict(dirty_csv_filepath)
    differences = utilities.compare_datasets(clean_dataset=clean_entries, dirty_dataset=dirty_entries)
    incorrect_key = differences.keys()[0]


    key_knowledge: str = key_knowledge_generator.create_knowledge_generation_prompt(clean_csv_filepath, incorrect_key, key_knowledge_prompts_path)
    print(key_knowledge)