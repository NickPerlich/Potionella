# this file will contain functions used for optimizing different processes
from typing import List

# this function is an implementation of the solution to the 01-knapsack problem
def knapSack(capacity: int, num_items: int, items: List[tuple[int, int]]):
    table = [[0] * (capacity+1) for _ in range(num_items+1)]
    # fill in the table using dynamic programming
    for n in range(1, num_items+1):
        for cap in range(1, capacity+1):
            item = items[n-1]
            item_weight = item[0]
            item_value = item[1]
            if item_weight > cap:
                table[n][cap] = table[n-1][cap]
            else:
                table[n][cap] = max(table[n-1][cap-item_weight]+item_value, table[n-1][cap]) 

    #trace back through the table
    items_taken = []
    i = num_items
    j = capacity

    while i > 0 and j > 0:
        item = items[i-1]
        weight = item[0]
        value = item[1]

        if weight > j or table[i][j] != table[i-1][j-weight]+value:
            i -= 1
        else:
            items_taken.append(i)
            i -= 1
            j -= weight

    return table, items_taken
