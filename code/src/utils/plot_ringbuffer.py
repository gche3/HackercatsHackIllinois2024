import numpy as np

class ArrayRingBuffer:
    def __init__(self, window_size, vector_length):
        self.length = 0
        self.start = 0
        self.window_size = window_size
        self.buffer = np.empty((window_size*2, vector_length), dtype=np.float64)

    def get_data(self):
        return self.buffer[self.start:self.start+self.length, :]

    def add_data(self, vec):
        start = self.start + self.length

        self.buffer[start, :] = vec

        if self.length < self.window_size:
            self.buffer[start + self.window_size, :] = vec
            self.length += 1
        else:
            self.buffer[start - self.window_size, :] = vec
            self.start += 1
            if self.start >= self.window_size:
                self.start = 0


if __name__ == "__main__":
    from plot_wrapper import InteractiveMatplotlibWrapper
    plt = InteractiveMatplotlibWrapper()
    plt.start()

    plt.figure(0)

    import time
    buf = ArrayRingBuffer(10, 3)
    for x in range(100):
        y = np.sin(x/10)
        y2 = np.cos(x/10)
        buf.add_data([x, y, y2])

        dat = buf.get_data()
        plt.clf()
        plt.plot(dat[:, 0], dat[:, 1])
        plt.plot(dat[:, 0], dat[:, 2])
        time.sleep(0.05)

    plt.stop()
