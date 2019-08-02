def find_pair_adding_to_target(values, target):
    values = list(sorted(values))
    low_index = 0
    high_index = len(values) - 1

    while low_index < high_index:
        pair_sum = values[low_index] + values[high_index]
        if pair_sum < target:
            low_index += 1
        elif pair_sum > target:
            high_index -= 1
        else:
            return [values[low_index], values[high_index]]

    return None


def is_subset_sum(values, target):
    n = len(values)
    subset = [[False for _ in range(target+1)] for _ in range(n+1)]

    for i in range(n+1):
        subset[i][0] = True

        for i in range(1, target+1):
            subset[0][i] = False

        for i in range(1, n+1):
            for j in range(1, target+1):
                if j < values[i-1]:
                    subset[i][j] = subset[i-1][j]
                if j >= values[i-1]:
                    subset[i][j] = subset[i-1][j] or subset[i-1][j-values[i-1]]

    return subset[n][target]


if __name__ == '__main__':
    values = [2, 8, 20, 4]
    target = 10

    print(find_pair_adding_to_target(values, target))
    print(is_subset_sum(values, target))
