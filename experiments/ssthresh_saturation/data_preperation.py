
def get_sshthresh_from_file(file_name: str):
    first_loss = (0, None)
    second_loss = (0, None)

    with open(file_name, 'r+') as f:
        for line in f:
            bits = line.split(" ")

            time = bits[0]
            ssthresh = bits[12]

            if ssthresh.split(":")[0] == "ssthresh":
                if first_loss[1] is None:
                    first_loss = (ssthresh.split(":")[1], time)
                elif ssthresh != first_loss[0]:
                    second_loss = (ssthresh.split(":")[1], time)
                    break

    return first_loss, second_loss

