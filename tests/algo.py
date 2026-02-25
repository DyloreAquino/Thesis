def make_horizontal_queues(number_of_queues : int,
                           line_size : int,
                           length: int,
                           start_pos_x : int,
                           start_pos_y : int) -> list[list[tuple[int, int]]]:
    waiting_queues = []
    increments = length / (number_of_queues / 2)
    middle = int(number_of_queues / 2)
    start_y_dec = start_pos_y
    for _ in range(middle):
        waiting_list = []
        for j in range(line_size):
            waiting_list.append((start_pos_x + j, start_y_dec))

        start_y_dec -= increments
        waiting_queues.append(waiting_list)
    start_y_dec = start_pos_y
    for _ in range(middle):
        waiting_list = []
        for j in range(line_size):
            waiting_list.append((start_pos_x - j + 36, start_y_dec))  

        start_y_dec -= increments
        waiting_queues.append(waiting_list)
    return waiting_queues
                
queues = make_horizontal_queues(4, 6, 20, -8, 30)

print(queues)
      