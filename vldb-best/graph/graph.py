#! /usr/bin/python3
import altair as alt
import csv
import pandas

expected_num_events = 100_000_000
expected_num_cores = 16
n_side_inputs = 100
def read_csv(name, system):
    data = {}
    with open(name) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['when'].startswith('#'):
                continue
            assert int(row['num_cores']) == expected_num_cores
            num_events = int(row['num_events'])
            assert (num_events == expected_num_events
                    or num_events == expected_num_events + n_side_inputs)
            query = int(row["name"][1:])
            data[query] = {
                'query': query,
                'system': system,
                'elapsed': float(row['elapsed']),
                'throughput': expected_num_events / float(row['elapsed']),
                'memory': float(row['peak_memory_bytes']) / (1024 * 1024 * 1024),
                'cpu': float(row.get('cpu_msecs', row.get('cpu_seconds'))) / 1000
            }
    return data

def trim(dst, keys):
    for key in list(dst.keys()):
        if key not in keys:
            del dst[key]

def normalize(dst, baseline):
    for key in dst.keys():
        for column in ('elapsed', 'throughput', 'memory', 'cpu'):
            dst[key]['normal_' + column] = dst[key][column] / baseline[key][column]

# Read all the results.
files = [#('feldera-stream-sql-100M.csv', 'Feldera in-memory'),
         #('feldera-stream-sql-100M-revised.csv', 'Feldera in-memory'),
         #('feldera-stream-sql-100M-storage.csv', 'Feldera with storage'),
         #('feldera-stream-sql-100M-storage-revised.csv', 'Feldera with storage'),
         ('feldera-stream-sql-100M-stepsize.csv', 'DBSP in-memory'),
         ('feldera-stream-sql-100M-stepsize-storage.csv', 'DBSP with storage'),
         ('flink-stream-default-100M.csv', 'Flink')]

data = []
for file, system in files:
    data.append(read_csv(file, system))

# Delete queries that aren't implemented in all the systems.
common = set(data[0].keys())
for d in data[1:]:
    common &= set(d.keys())
for d in data:
    trim(d, common)

# Normalize everything against the last system.
for d in data:
    normalize(d, data[-1])

for file, system in files[:-1]:
    for stat in ('throughput', 'memory', 'cpu'):
        product = 1.0
        extrema = None
        n = 0
        for d in data:
            for attrs in d.values():
                if attrs['system'] == system:
                    f = attrs[f'normal_{stat}']
                    product *= f
                    if extrema is None:
                        extrema = (f, f)
                    else:
                        extrema = (min(f, extrema[0]), max(f, extrema[1]))
                    n += 1
        speedup = product ** (1.0 / n)
        print(f"relative {stat} for {system} = {speedup}, range = {extrema}")

def transpose(data):
    # Transpose our rows into columns because that's what Pandas wants.
    columns = {}
    for src in data:
        for query, stats in src.items():
            for k, v in stats.items():
                columns.setdefault(k, []).append(v)
    for column in columns.keys():
        assert len(columns[column]) == len(columns['query'])
    return columns

data_without_basis = pandas.DataFrame(data=transpose(data[:-1]))
data = pandas.DataFrame(data=transpose(data))
#print(data)

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="System"),
         y=alt.Y("memory", title="GiB"),
         color=alt.Color("system:N", title="System"),
         column=alt.Column("query:N", title="Query"))
 .properties(title="Peak Memory Usage")
 .save('memory.pdf'))

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="System"),
         y=alt.Y("normal_memory", title="Normalized Memory"),
         color=alt.Color("system:N", title="System"),
         column=alt.Column("query:N", title="Query"))
 .properties(title="Normalized Peak Memory Usage")
 .save('memory_normal.pdf'))

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="System"),
         y=alt.Y("cpu", title="CPU-Seconds"),
         color=alt.Color("system:N", title="System"),
         column=alt.Column("query:N", title="Query"))
 .properties(title='Total CPU Usage')
 .save('cpu.pdf'))

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="System"),
         y=alt.Y("normal_cpu", title="Normalized CPU-Seconds"),
         color=alt.Color("system:N", title="System"),
         column=alt.Column("query:N", title="Query"))
 .properties(title='Normalized Total CPU Usage')
 .save('cpu_normal.pdf'))

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="System"),
         y=alt.Y("elapsed", title="Seconds"),
         color=alt.Color("system:N", title="System"),
         column=alt.Column("query:N", title="Query"))
 .properties(title='Elapsed Time')
 .save('elapsed.pdf'))

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="System"),
         y=alt.Y("throughput", title="Events/Second"),
         color=alt.Color("system:N", title="System"),
         column=alt.Column("query:N", title="Query"))
 .properties(title='Throughput')
 .save('throughput.pdf'))

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="System"),
         y=alt.Y("normal_throughput", title="Normalized Throughput"),
         color=alt.Color("system:N", title="System"),
         column=alt.Column("query:N", title="Query"))
 .properties(title='Normalized Throughput')
 .save('throughput_normal.pdf'))
