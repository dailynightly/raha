import requests
import json
import csv

def csv_to_dict_list(csv_file_path):
    # Initialize an empty list to store the dictionaries
    dict_list = []

    # Open the CSV file
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        # Create a CSV reader
        csv_reader = csv.DictReader(file)

        # Iterate over each row in the CSV file
        for row in csv_reader:
            # Each row is already a dictionary; append it to the list
            dict_list.append(row)

    return dict_list

def send_request(prompt: str, model: str, url:str) -> str:

    # JSON object you want to send
    data = {
        "stream": False
    }
    data["model"] = model
    data["prompt"] = prompt
    # Convert your data to JSON
    json_data = json.dumps(data)

    # Send a POST request
    response = requests.post(url, data=json_data, headers={'Content-Type': 'application/json'})

    # Check if the request was successful
    if response.status_code == 200:
        try:
            response_data = response.json()

            # Access a specific entry in the JSON data
            specific_entry = response_data['response']
            print(specific_entry)
            return specific_entry

        except json.JSONDecodeError:
            print("Response is not in JSON format.")
            print(response.text)
    else:
        print(f"Failed to send request. Status code: {response.status_code}")
    

def dict_to_string(input_dict: dict) -> str:
    # Use a list comprehension to format each key-value pair as 'key : value'
    pairs = [f"{key} : {value}" for key, value in input_dict.items()]

    # Join all pairs with a comma and a space
    result = ', '.join(pairs)

    return result

def load_prompts(file_name: str) -> dict:
    # Path to the JSON file
    json_file_path = file_name

    # Reading the JSON data from the file
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Now you can use the 'data' dictionary as needed
    return data

def read_csv_to_dict(file_path):
    data = {}
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = row.pop(reader.fieldnames[0])  # Assumes first column is the unique identifier
            data[key] = row
    return data

def compare_datasets(clean_dataset, dirty_dataset):
    differences = {}
    for key, dirty_entry in dirty_dataset.items():
        clean_entry = clean_dataset.get(key)
        if clean_entry and dirty_entry != clean_entry:
            diff_keys = [k for k in dirty_entry if dirty_entry[k] != clean_entry.get(k, None)]
            if diff_keys:
                for diff_key in diff_keys:
                    if diff_key not in differences:
                        differences[diff_key] = list()
                    differences[diff_key].append(dirty_entry)

    return differences