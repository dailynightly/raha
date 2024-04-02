import key_knowledge_generator
import tuple_chooser
import correction_engine

def chain_of_thought_pipeline(dirty_entry: str, incorrect_key: str, clean_csv_filepath: str, knowledge_prompt_filepath: str, model: str):
    error_key: str = incorrect_key
    knowledge_prompt: str = key_knowledge_generator.create_knowledge_generation_prompt(clean_csv_filepath, error_key, knowledge_prompt_filepath)
    llm_knowledge_response: str = key_knowledge_generator.ask_llm_for_knowledge(knowledge_prompt, model)

    chosen_tuple = None
    tuple_choose_prompt, tuple_candidates = tuple_chooser.create_tuple_choosing_prompt(error_database, knowledge_prompt, llm_knowledge_response, error_key)
    tuple_choose_response = tuple_chooser.send_tuple_choosing_prompt_raw(tuple_choose_prompt, model, error_key)
    tuple_extraction_prompt = tuple_chooser.create_extraction_prompt(tuple_candidates, error_key, tuple_choose_response)
    tuple_index = tuple_chooser.send_tuple_extraction_prompt(tuple_extraction_prompt, model)

    if not tuple_index:
        chosen_tuple = tuple_candidates[0]
    else:
        chosen_tuple = tuple_candidates[tuple_index-1]
    
    wrong_data_entry: dict = chosen_tuple
    correct_data_entry: dict = clean_database[wrong_data_entry[index]]
    correction_prompt: str = correction_engine.create_corrector_prompt(utilities.dict_to_string(wrong_data_entry), knowledge_prompt, llm_knowledge_response)
    llm_correction: str = correction_engine.send_correction_prompt_raw(correction_prompt, model, error_key)
    extraction_prompt: str = correction_engine.create_extraction_prompt(utilities.dict_to_string(wrong_data_entry), llm_correction)
    extracted_correction: str = correction_engine.send_extraction_prompt(extraction_prompt, model, error_key)