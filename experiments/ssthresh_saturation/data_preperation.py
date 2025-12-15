
def get_sshthresh_from_file(file_name: str):
    first_loss = (0, None)
    second_loss = (0, None)
    third_loss = (0, None)

    with open(file_name, 'r+') as f:

        for line in f:
            bits = line.split(" ")

            # TODO: Use pandas
            time = bits[0]
            ssthresh = bits[12]

            if ssthresh.split(":")[0] == "ssthresh":
                if first_loss[1] is None:
                    first_loss = (ssthresh.split(":")[1], time)
                elif second_loss[1] is None and ssthresh.split(":")[1] != first_loss[0]:
                    second_loss = (ssthresh.split(":")[1], time)
                    break
                elif second_loss[1] is not None and ssthresh.split(":")[1] != second_loss[0]:
                    third_loss = (ssthresh.split(":")[1], time)
                    break

    return first_loss, second_loss, third_loss

def get_queue_and_ssthresh(experiment_time: str):
    queues = [x for x in range(5, 255, 5)]
    ssthresh = []

    for queue in queues:
        ssthresh.append(
            int(get_sshthresh_from_file(f"{experiment_time}/ssthresh/ssthresh-queue-{queue}.txt")[0][0])
        )

    return queues, ssthresh
