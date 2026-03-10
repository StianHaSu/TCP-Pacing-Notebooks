import datetime

def get_sshthresh_from_file(file_name: str):
    first_loss = (None, None, None)
    second_loss = (None, None, None)
    max_cwnd = -1

    with open(file_name, 'r+') as f:

        for line in f:
            bits = line.split(" ")

            # TODO: Use pandas?
            time = bits[0]
            ssthresh = bits[12]
            rtt = bits[4].split(":")[1].split("/")[0]

            if ssthresh.split(":")[0] == "ssthresh":
                if first_loss[1] is None:
                    first_loss = (ssthresh.split(":")[1], rtt, time)
                    max_cwnd = int(bits[11].split(":")[1])
                elif second_loss[1] is None and ssthresh.split(":")[1] != first_loss[0]:
                    second_loss = (ssthresh.split(":")[1], rtt, time)
                    break

    if first_loss[0] is None:
        print(file_name)

    return first_loss, second_loss, max_cwnd


def get_last_sshthresh_from_file(file_name: str):
    loss = (0, None, None)
    loss2 = (0, None, None)
    with open(file_name, 'r+') as f:

        for line in f:
            bits = line.split(" ")

            # TODO: Use pandas?
            time = bits[0]
            ssthresh = bits[12]
            rtt = bits[4].split(":")[1].split("/")[0]

            if ssthresh.split(":")[0] == "ssthresh" and (ssthresh.split(":")[1] != loss[0] or loss[1] is None):
                loss2 = loss
                loss = (ssthresh.split(":")[1], rtt, time)

    return loss2 if loss2[1] is not None else loss


def get_last_queue_ssthresh_rtt(experiment_time: str):
    queues = [x for x in range(5, 255, 5)]
    ssthresh = []
    rtts = []

    for queue in queues:
        losses = get_last_sshthresh_from_file(f"{experiment_time}/ssthresh/ssthresh-queue-{queue}.txt")
        ssthresh.append(int(losses[0]))
        rtts.append(int(losses[1]))

    return queues, ssthresh, rtts

def get_queue_ssthresh_rtt(experiment_time: str):
    queues = [x for x in range(5, 255, 5)]
    ssthresh = []
    second_ssthresh = []
    cwnds = []
    rtts = []

    for queue in queues:
        first_loss, second_loss, max_cwnd = get_sshthresh_from_file(f"{experiment_time}/ssthresh/ssthresh-queue-{queue}.txt")
        if first_loss[0] is not None:
            ssthresh.append(int(first_loss[0]))
            rtts.append(int(first_loss[1]))
            cwnds.append(max_cwnd)

        else:
            ssthresh.append(-1)
            rtts.append(-1)
            cwnds.append(-1)

        if second_loss[0] is not None:
            second_ssthresh.append(int(second_loss[0]))
        else:
            second_ssthresh.append(-1)

    return queues, ssthresh, rtts, cwnds, second_ssthresh
