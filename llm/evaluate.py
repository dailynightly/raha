import key_knowledge_generator
import correction_engine
import tuple_chooser
import utilities
import pandas as pd
from datetime import datetime

def eval_correction(model: str, clean_filepath_csv: str, dirty_filepath_csv: str, knowledge_prompt_filepath: str, correction_prompt_filepath: str, test_amount: int):
    #load databases
    clean_database: dict = utilities.read_csv_to_dict(clean_filepath_csv)
    dirty_database: dict = utilities.read_csv_to_dict(dirty_filepath_csv)
    error_database: dict = utilities.compare_datasets(clean_database, dirty_database)

    error_keynames = list(error_database.keys())
    index = list(list(clean_database.values())[0].keys())[0] #remove index column and save the name for the index
    tests_run: int = 0
    score: int = 0

    while tests_run < test_amount:
        error_key: str = error_keynames[tests_run % len(error_keynames)]
        knowledge_prompt: str = key_knowledge_generator.create_knowledge_generation_prompt(clean_filepath_csv, error_key, knowledge_prompt_filepath)
        llm_knowledge_response: str = key_knowledge_generator.ask_llm_for_knowledge(knowledge_prompt, model)
        
        wrong_data_entry: dict = error_database[error_key][-1 - tests_run]
        correct_data_entry: dict = clean_database[wrong_data_entry[index]]
        correction_prompt: str = correction_engine.create_corrector_prompt(utilities.dict_to_string(wrong_data_entry), knowledge_prompt, llm_knowledge_response)
        llm_correction: str = correction_engine.send_correction_prompt_raw(correction_prompt, model, error_key)
        extraction_prompt: str = correction_engine.create_extraction_prompt(utilities.dict_to_string(wrong_data_entry), llm_correction)
        extracted_correction: str = correction_engine.send_extraction_prompt(extraction_prompt, model, error_key)
        if extracted_correction == str(correct_data_entry[error_key]):
            score += 1
        
        print(f"LLM: {extracted_correction} | Correct: {correct_data_entry[error_key]}")
        
        tests_run += 1
    
    return score

def eval_correction_choosing(model: str, clean_filepath_csv: str, dirty_filepath_csv: str, knowledge_prompt_filepath: str, correction_prompt_filepath: str, test_amount: int, database_name):
    #load databases
    clean_database, key = utilities.read_csv_to_dict(clean_filepath_csv)
    dirty_database, key = utilities.read_csv_to_dict(dirty_filepath_csv)
    error_database: dict = utilities.compare_datasets(clean_database, dirty_database)

    clean_database_list = utilities.csv_to_dict_list(clean_filepath_csv)

    error_keynames = list(error_database.keys())
    index = list(list(clean_database.values())[0].keys())[0] #remove index column and save the name for the index
    tests_run: int = 0
    score: int = 0

    data_structure = {"Successful correction": [], "Successful tuple_extraction": [], "Key_knowledge": [], "Correction_extracted": [],
                       "Tuples prompt": [], "Extraction_response": [], "Correction_response": [], "Correction_Extr_response": []}


    key_knowledge_gen = key_knowledge_generator.Key_knowledge_generator(clean_database_list, knowledge_prompt_filepath, model)
    tuple_choose = tuple_chooser.Tuple_chooser(error_database)
    correction = correction_engine.Corrector(model)

    while tests_run < test_amount:
        error_key: str = error_keynames[tests_run % len(error_keynames)]

        key_knowledge_block = key_knowledge_gen.get_key_knowledge_block(error_key, 1)
        chosen_tuple = None
        tuple_choose_block = tuple_choose.get_tuple_choosing_block(key_knowledge_block, model)


        if not tuple_choose_block.chosen_tuple_index:
            chosen_tuple = tuple_choose_block.tuple_candidates[0]
        else:
            chosen_tuple = tuple_choose_block.chosen_tuple
        
        wrong_data_entry: dict = chosen_tuple
        correct_data_entry: dict = clean_database[wrong_data_entry[index]]
        correction_llm = correction.get_correction(wrong_data_entry, error_key, key_knowledge_block.get_prompt(), key_knowledge_block.get_key_knowledge())
        correction_log = correction.get_correction_log()

        if correction_llm == str(correct_data_entry[error_key]):
            score += 1
            data_structure["Successful correction"].append(1)
        else:
            data_structure["Successful correction"].append(0)
        
        print(f"LLM: {correction_llm} | Correct: {correct_data_entry[error_key]}")

        if tuple_choose_block.llm_chose_tuple:
            data_structure["Successful tuple_extraction"].append(1)
        else:
            data_structure["Successful tuple_extraction"].append(0)

        if correction_log.extraction_successful:
            data_structure["Correction_extracted"].append(1)
        else:
            data_structure["Correction_extracted"].append(0)


        data_structure["Key_knowledge"].append(key_knowledge_block.get_key_knowledge())
        data_structure["Tuples prompt"].append(tuple_choose_block.tuple_choosing_prompt)
        data_structure["Extraction_response"].append(tuple_choose_block.tuple_extraction_response)
        data_structure["Correction_response"].append(correction_log.correction_response)
        data_structure["Correction_Extr_response"].append(correction_log.extraction_response)
        
        tests_run += 1

    # Get the current date and time
    current_datetime = datetime.now()

    # Format the date and time as a string
    datetime_string = current_datetime.strftime("%Y-%m-%d %H-%M-%S")

    data: pd.DataFrame = pd.DataFrame(data_structure)
    filename = database_name + datetime_string + ".json"
    data.to_json(filename)
    
    return score

def evaluate_chain_of_thought(model: str, clean_filepath_csv: str, dirty_filepath_csv: str, knowledge_prompt_filepath: str, correction_prompt_filepath: str, test_amount: int):
    
    #databases = ["beers", "hospital", "flights", "movies_1"]
    databases = ["beers"]

    for database in databases:
        clean_filepath_csv_with_name = clean_filepath_csv.replace("[database_name]", database)
        dirty_filepath_csv_with_name = dirty_filepath_csv.replace("[database_name]", database)
        eval_correction_choosing(model, clean_filepath_csv_with_name, dirty_filepath_csv_with_name, knowledge_prompt_filepath, correction_prompt_filepath, test_amount, database)

if __name__ == "__main__":
    test_amount = 1
    score = evaluate_chain_of_thought(model="mistral",
                    clean_filepath_csv="/home/danielle/raha/datasets/[database_name]/clean.csv", 
                    dirty_filepath_csv="/home/danielle/raha/datasets/[database_name]/dirty.csv", 
                    knowledge_prompt_filepath="/home/danielle/raha/llm/key_knowledge_prompts.json", 
                    correction_prompt_filepath="/home/danielle/raha/llm/correction_prompts.json", 
                    test_amount=test_amount)
    print(f"Score is {score} out of {test_amount}.")