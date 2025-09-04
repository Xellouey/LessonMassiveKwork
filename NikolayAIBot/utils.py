import json


def get_steps(filename="json/steps.json"):
    try:
        with open(filename, 'r') as f:
            steps = json.load(f)
        return steps
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось декодировать JSON из файла {filename}.  Возвращается пустой словарь.")
        return {}


def update_steps(new_steps, filename="json/steps.json"):
    with open(filename, 'w') as f:
        json.dump(new_steps, f, indent=4, ensure_ascii=False)
        
        
def get_admins(filename="json/admins.json"):
    try:
        with open(filename, 'r') as f:
            admins = json.load(f)
        return admins
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось декодировать JSON из файла {filename}.  Возвращается пустой словарь.")
        return {}


def update_admins(new_admins, filename="json/admins.json"):
    with open(filename, 'w') as f:
        json.dump(new_admins, f, indent=4, ensure_ascii=False)
        
        
def move_dict_item(dictionary, key, new_position):
    if key not in dictionary:
        raise KeyError(f"Key '{key}' not found in dictionary")
    
    if new_position < 0 or new_position >= len(dictionary):
        raise IndexError("New position is out of bounds")
    
    items = list(dictionary.items())
    
    current_position = next(i for i, (k, _) in enumerate(items) if k == key)
    
    if current_position == new_position:
        return dictionary
    
    item = items.pop(current_position)
    items.insert(new_position, item)
    
    return dict(items)


def remove_dict_item(dictionary, key):
    if key not in dictionary:
        raise KeyError(f"Key '{key}' not found in dictionary")
    
    new_dict = dictionary.copy()
    del new_dict[key]
    return new_dict


def get_new_key():
    steps = get_steps()
    
    keys = list(steps.keys())
    last_key = keys[-1]

    if 'step' not in last_key:
        key = f'step1'
    else:
        new_index = int(last_key.split('step')[1]) + 1
        key = f'step{new_index}'
                
    return key
    