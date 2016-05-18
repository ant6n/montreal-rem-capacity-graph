import re, scipy.stats
import schedules
import matplotlib.pyplot as plot
import matplotlib.ticker as ticker
import matplotlib
import math

remColor = '#500000'
lines = [
    {'line': 'dm','schedule': schedules.dm, 'color': '#00aab5', 'capacity': 2000, 'stacked': True},
    {'line': 'ma','schedule': schedules.ma, 'color': '#ef2c8d', 'capacity': 2000, 'stacked': True},
    {'line': 'sj','schedule': schedules.sj, 'color': '#74ba20', 'capacity': 2000, 'stacked': True,
     'offset': 7}, # schedule is relative to Parc, make it relative to downtown
    {'line': 'vh','schedule': schedules.vh, 'color': '#c32e3c', 'capacity': 2000, 'stacked': True},    
    {
        'line': 'orange',
        'schedule': schedules.orange, 'color': '#ef7f00', 'capacity': int(round(1440*1.08)),
        'linewidth': 2.0*2,
        'alpha': 0.4,
    },
    {
        'line': 'REM-planned capacity','schedule': schedules.rem, 'color': remColor, # '#a7db38',
        'capacity': int(round(600)),
        'linewidth': 3.5*2,
    },
    {
        'line': 'REM-max capacity','schedule': schedules.rem, 'color': remColor, #a7db38',
        'capacity': int(round(600*1.35)),
        'linestyle': '--',
        'linewidth': 3.5*2,
    },
    {
        'line': 'REM-planned capacity','schedule': schedules.rem, 'color': '#a7db38',
        'capacity': int(round(600)),
        'linewidth': 1.8*2,
    },
    {
        'line': 'REM-max capacity','schedule': schedules.rem, 'color': '#a7db38',
        'capacity': int(round(600*1.35)),
        'linestyle': '--',
        'linewidth': 1.8*2,
    },
]

def getTimesInMinutes(schedule):
    result = []
    for s in schedule:
        h, m, s = re.match('\s?(\d+):(\d+):(\d+)', s).groups()
        result.append(int(h)*60 + int(m))
    return result

def getNormalDistribution(schedule, capacityPerTrain):
    times = getTimesInMinutes(schedule)
    scale = scipy.stats.norm(scale=1).pdf(0)
    h = 60
    result = [0 for _ in range(24*h)]
    for t0 in times:
        normal = scipy.stats.norm(loc=t0, scale=scale*h)
        for t in range(t - 3*h, t + 3*h + 1):
            result[t % (24*h)] += (normal.cdf(t+.5) - normal.cdf(t-.5))  * h * capacityPerTrain
    return [int(round(f)) for f in result]

def cosDistribution(x, center, width):
    if abs(x - center) >= width:
        return 0.0
    xp = (x - center) * math.pi / width
    return 0.5*(math.cos(xp) + 1) / width
    

def getCosDistribution(schedule, capacityPerTrain):
    times = getTimesInMinutes(schedule)
    scale = scipy.stats.norm(scale=1).pdf(0)
    h = 60
    result = [0 for _ in range(24*h)]
    for t0 in times:
        add = [0 for _ in range(24*h)]
        for t in range(t0 - 3*h, t0 + 3*h + 1):        
            add[t % (24*h)] += cosDistribution(t, t0, h) * h * capacityPerTrain
        for i in range(len(result)):
            result[i] += add[i]
    result = [int(round(f)) for f in result]
    return result

def getBarDistribution(schedule, capacityPerTrain):
    h = 60
    times = getTimesInMinutes(schedule)
    times = [t + 24*h if t < 3*h else t for t in times]
    result = [0 for _ in range(24*h)]
    for i in range(len(times)-1):
        t1 = times[i]
        t2 = times[i+1]
        add = [0 for _ in range(24*h)]
        for t in range(t1,t2):
            result[t % (24*h)] += capacityPerTrain * 60.0 / (t2-t1)
    return [int(round(f)) for f in result]

def rotate(l,n):
    return l[n:] + l[:n]

def makePlot(fn=getCosDistribution):
    # collect data
    h = 60
    linePlots = []
    stackedPlots = {
        'labels': [],
        'data': [],
        'colors': [],
    }
    for line in lines:
        distribution = fn(line['schedule'], line['capacity'])
        distribution = rotate(distribution, -line.get('offset', 0))
        distribution = distribution[3*h:] + distribution[:3*h]
        distribution = distribution[1*h:23*h]
        if line.get('stacked'):
            stackedPlots['data'  ].append(distribution)
            stackedPlots['colors'].append(line['color'])
            stackedPlots['labels'].append(line['line'])            
            
        else:
            linePlots.append({
                'y': distribution,
                'color': line['color'],
                'linestyle': line.get('linestyle', '-'),
                'linewidth': line.get('linewidth', 2),
                'alpha': line.get('alpha', 1),
            })
    X = [t/60.0 for t in  range(4*h, 26*h)]

    # make plot
    matplotlib.rcParams.update({'font.size': 16})
    fig, ax = plot.subplots(facecolor="white", figsize=(13,7), dpi=100)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda d, _: str(d%24)+"h"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda d, _: "{:,}".format(int(d))))
    plot.xlim(4, 26)
    plot.ylim(0, 35000)
    plot.xticks(range(4,27, 2))
    plot.ticklabel_format(axis='x',)
    plot.minorticks_on()
    plot.grid(color='#000000', alpha=0.2, linestyle='-', linewidth=0.8, which='both')
    ax.yaxis.grid(color='#000000', alpha=0.1, linestyle='-', linewidth=0.4, which='minor')
#    plot.grid(color='#000000', b=True, which='minor', axis='x', alpha=0.15, linestyle='-', linewidth=0.5, xdata=range(5,27, 2))
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))

    if len(stackedPlots['data']) > 0:
        plot.stackplot(X,
                       *(stackedPlots['data']),
                       colors=stackedPlots['colors'],
                       alpha = 0.5,
                       linewidth = 0)
    for p in linePlots:
        plot.plot(X,
                  p['y'],
                  alpha=p['alpha'],
                  color=p['color'], linewidth=p['linewidth'], linestyle=p['linestyle'],)
#    plot.axes(axisbg='w')

    plot.show()

    

if __name__ == "__main__":
    makePlot()
