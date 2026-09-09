import helper

x = helper.get_table_data()

print(sum(int(d["num_rows"]) for d in x))