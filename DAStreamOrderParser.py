def main():
    txtFileInput = open("C:\Users\A02150284\Documents\GIS Data\Asotin\TributaryImpactPoints\DAStreamOrderComparison(DataInput).txt", 'r')
    lines = txtFileInput.readlines()

    drainageAreas = []
    streamOrders = []

    i = 0
    for line in lines:
        line = line.rstrip()
        if i % 4 == 0 or 1:
            drainageAreas.append(float(line))
        else:
            streamOrders.append(int(line))

    for i in range(len(streamOrders)):
        if streamOrders[i] == 1:



main()