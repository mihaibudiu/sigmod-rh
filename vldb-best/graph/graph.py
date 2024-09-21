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
 .encode(x=alt.X("system:N", title="System").title(None),
         y=alt.Y("memory", title=""),
         color=alt.Color("system:N", title="").scale(scheme="category10"),
         column=alt.Column("query:N", title="Peak Memory Usage by Query, in GiB"))
 .configure_axis(labelFontSize=20, titleFontSize=20)
 .configure_axisX(labels=False, ticks=False)
 .configure_legend(labelFontSize=20, labelLimit=200, titleFontSize=10, orient="bottom")
 .configure_title(fontSize=20)
 .configure_header(labelFontSize=20, titleFontSize=20)
 .save('memory.pdf'))

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="").title(None),
         y=alt.Y("normal_memory", title=""),
         color=alt.Color("system:N", title="").scale(scheme="category10"),
         column=alt.Column("query:N", title="Normalized Peak Memory Usage by Query"))
 .configure_axis(labelFontSize=20, titleFontSize=20)
 .configure_axisX(labels=False, ticks=False)
 .configure_legend(labelFontSize=20, labelLimit=200, titleFontSize=10, orient="bottom")
 .configure_title(fontSize=20)
 .configure_header(labelFontSize=20, titleFontSize=20)
 .save('memory_normal.pdf'))

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="").title(None),
         y=alt.Y("cpu", title=""),
         color=alt.Color("system:N", title="").scale(scheme="category10"),
         column=alt.Column("query:N", title="Total CPU Usage by Query, in CPU-Seconds"))
 .configure_axis(labelFontSize=20, titleFontSize=20)
 .configure_axisX(labels=False, ticks=False)
 .configure_legend(labelFontSize=20, labelLimit=200, titleFontSize=10, orient="bottom")
 .configure_title(fontSize=20)
 .configure_header(labelFontSize=20, titleFontSize=20)
 .save('cpu.pdf'))

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="").title(None),
         y=alt.Y("normal_cpu", title=""),
         color=alt.Color("system:N", title="").scale(scheme="category10"),
         column=alt.Column("query:N", title="Normalized Total CPU Usage by Query"))
 .configure_axis(labelFontSize=20, titleFontSize=20)
 .configure_axisX(labels=False, ticks=False)
 .configure_legend(labelFontSize=20, labelLimit=200, titleFontSize=10, orient="bottom")
 .configure_title(fontSize=20)
 .configure_header(labelFontSize=20, titleFontSize=20)
 .save('cpu_normal.pdf'))

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="").title(None),
         y=alt.Y("elapsed", title=""),
         color=alt.Color("system:N", title="").scale(scheme="category10"),
         column=alt.Column("query:N", title="Elapsed Time by Query, in Seconds"))
 .configure_axis(labelFontSize=20, titleFontSize=20)
 .configure_axisX(labels=False, ticks=False)
 .configure_legend(labelFontSize=20, labelLimit=200, titleFontSize=10, orient="bottom")
 .configure_title(fontSize=20)
 .configure_header(labelFontSize=20, titleFontSize=20)
 .save('elapsed.pdf'))

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="").title(None),
         y=alt.Y("throughput", title=""),
         color=alt.Color("system:N", title="").scale(scheme="category10"),
         column=alt.Column("query:N", title="Throughput by Query, in Events/Second"))
 .configure_axis(labelFontSize=20, titleFontSize=20)
 .configure_axisX(labels=False, ticks=False)
 .configure_legend(labelFontSize=20, labelLimit=200, titleFontSize=10, orient="bottom")
 .configure_title(fontSize=20)
 .configure_header(labelFontSize=20, titleFontSize=20)
 .save('throughput.pdf'))

(alt
 .Chart(data)
 .mark_bar()
 .encode(x=alt.X("system:N", title="").title(None),
         y=alt.Y("normal_throughput", title=""),
         color=alt.Color("system:N", title="").scale(scheme="category10"),
         column=alt.Column("query:N", title="Normalized Throughput by Query"))
 .configure_axis(labelFontSize=20, titleFontSize=20)
 .configure_axisX(labels=False, ticks=False)
 .configure_legend(labelFontSize=20, labelLimit=200, titleFontSize=10, orient="bottom")
 .configure_title(fontSize=20)
 .configure_header(labelFontSize=20, titleFontSize=20)
 .save('throughput_normal.pdf'))
