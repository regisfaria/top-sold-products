from pathlib import Path
import csv
# Here i'll be writting some utilitys that will help on the main codes

def get_project_root() -> Path:
    return Path(__file__).parent.parent

def remove_duplicates(l):
    duplicate_elements = []
    for i in range(0, len(l)):
        if i == len(l)-1:
            break
        if l[i] == l[i+1]:
            duplicate_elements.append(l[i])
    for i in range(0, len(duplicate_elements)):
        l.remove(duplicate_elements[i])