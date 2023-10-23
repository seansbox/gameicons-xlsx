import csv
import os


class CSVKeyValueStore:
    def __init__(self, csv_filename):
        self.csv_filename = csv_filename
        self.data = self.load_data()

    def load_data(self):
        if not os.path.exists(self.csv_filename):
            return {}

        data = {}
        with open(self.csv_filename, "r", newline="") as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                key = row[0]
                value = row[1:]
                data[key] = value
        return data

    def save_data(self):
        with open(self.csv_filename, "w", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            for key, value in self.data.items():
                csvwriter.writerow([key] + value)

    def get(self, key):
        return self.data.get(key)

    def set(self, key, *values):
        self.data[key] = list(values)
        self.save_data()

    def delete(self, key):
        if key in self.data:
            del self.data[key]
            self.save_data()


if __name__ == "__main__":
    # Example usage:
    store = CSVKeyValueStore("data.csv")

    # Setting values
    store.set("key1", "value1", "value2", "value3")
    store.set("key2", "value4", "value5")

    # Retrieving values
    print(store.get("key1"))  # Output: ['value1', 'value2', 'value3']
    print(store.get("key2"))  # Output: ['value4', 'value5']

    # Deleting a key
    store.delete("key1")
    print(store.get("key1"))  # Output: None

    # Adding a new key
    store.set("key3", "value6")
    print(store.get("key3"))  # Output: ['value6']
