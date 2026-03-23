import { useState, useEffect, useRef, useCallback } from 'react';
import * as d3 from 'd3';
import * as topojson from 'topojson-client';
import './App.css';

interface Show {
  show_id: string;
  type: string;
  title: string;
  director: string;
  cast: string;
  country: string;
  date_added: string;
  release_year: number;
  rating: string;
  duration: string;
  listed_in: string;
  description: string;
}

const COLORS = {
  bg: '#19222d',
  bgCard: '#1e2a38',
  primary: '#00a8e1',
  primaryLight: '#b9ddf1',
  white: '#ffffff',
  textMuted: '#8899aa',
  border: '#2a3a4a',
};

/* ─── World Map (Choropleth) ─── */
function WorldMap({ data }: { data: Show[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [worldData, setWorldData] = useState<ReturnType<typeof topojson.feature> | null>(null);

  useEffect(() => {
    fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json')
      .then(res => res.json())
      .then(world => {
        const countries = topojson.feature(world, world.objects.countries);
        setWorldData(countries);
      });
  }, []);

  useEffect(() => {
    if (!svgRef.current || !worldData || !containerRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight - 40;

    svg.attr('width', width).attr('height', height);

    const countryCountMap = new Map<string, number>();
    data.forEach(d => {
      if (d.country) {
        d.country.split(',').forEach(c => {
          const name = c.trim();
          countryCountMap.set(name, (countryCountMap.get(name) || 0) + 1);
        });
      }
    });

    const maxCount = Math.max(...Array.from(countryCountMap.values()), 1);
    const colorScale = d3.scaleSequential(d3.interpolateBlues).domain([0, maxCount]);

    const projection = d3.geoNaturalEarth1()
      .fitSize([width, height], worldData as d3.GeoPermissibleObjects);
    const pathGen = d3.geoPath().projection(projection);

    const nameMap: Record<string, string> = {
      'United States': 'United States of America',
      'UK': 'United Kingdom',
      'South Korea': 'Korea, Republic of',
      'Russia': 'Russian Federation',
      'Czech Republic': 'Czechia',
    };

    const features = (worldData as GeoJSON.FeatureCollection).features;
    svg.append('g')
      .selectAll('path')
      .data(features)
      .join('path')
      .attr('d', d => pathGen(d) || '')
      .attr('fill', d => {
        const name = (d.properties as { name?: string })?.name || '';
        let count = countryCountMap.get(name) || 0;
        if (!count) {
          for (const [csvName, mapName] of Object.entries(nameMap)) {
            if (mapName === name) {
              count = countryCountMap.get(csvName) || 0;
              break;
            }
          }
        }
        return count > 0 ? colorScale(count) : '#0d1520';
      })
      .attr('stroke', '#1a2535')
      .attr('stroke-width', 0.5)
      .on('mouseover', function (event, d) {
        const name = (d.properties as { name?: string })?.name || '';
        let count = countryCountMap.get(name) || 0;
        if (!count) {
          for (const [csvName, mapName] of Object.entries(nameMap)) {
            if (mapName === name) {
              count = countryCountMap.get(csvName) || 0;
              break;
            }
          }
        }
        d3.select(this).attr('stroke', COLORS.primary).attr('stroke-width', 1.5);
        if (tooltipRef.current) {
          tooltipRef.current.style.display = 'block';
          tooltipRef.current.innerHTML = `<strong>${name}</strong><br/>${count} show${count !== 1 ? 's' : ''}`;
          tooltipRef.current.style.left = event.offsetX + 10 + 'px';
          tooltipRef.current.style.top = event.offsetY - 30 + 'px';
        }
      })
      .on('mouseout', function () {
        d3.select(this).attr('stroke', '#1a2535').attr('stroke-width', 0.5);
        if (tooltipRef.current) tooltipRef.current.style.display = 'none';
      });
  }, [worldData, data]);

  return (
    <div ref={containerRef} className="relative w-full h-full">
      <h3 className="text-sm font-bold px-3 pt-2" style={{ color: COLORS.white }}>Total Shows by Country</h3>
      <svg ref={svgRef} />
      <div ref={tooltipRef} className="absolute hidden pointer-events-none rounded px-2 py-1 text-xs z-50"
        style={{ background: COLORS.bgCard, color: COLORS.white, border: `1px solid ${COLORS.border}` }} />
    </div>
  );
}

/* ─── Donut Chart ─── */
function DonutChart({ data }: { data: Show[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight - 40;
    const radius = Math.min(width, height) / 2 - 20;

    svg.attr('width', width).attr('height', height);

    const types = d3.rollup(data, v => v.length, d => d.type);
    const total = d3.sum(Array.from(types.values()));
    const pieData = Array.from(types, ([key, value]) => ({ type: key, count: value }));

    const pie = d3.pie<{ type: string; count: number }>().value(d => d.count).sort(null);
    const arc = d3.arc<d3.PieArcDatum<{ type: string; count: number }>>()
      .innerRadius(radius * 0.55)
      .outerRadius(radius);

    const g = svg.append('g').attr('transform', `translate(${width / 2},${height / 2})`);

    const colorMap: Record<string, string> = { 'Movie': COLORS.primary, 'TV Show': COLORS.primaryLight };

    g.selectAll('path')
      .data(pie(pieData))
      .join('path')
      .attr('d', arc)
      .attr('fill', d => colorMap[d.data.type] || COLORS.primary)
      .attr('stroke', COLORS.bg)
      .attr('stroke-width', 2);

    g.selectAll('text.label')
      .data(pie(pieData))
      .join('text')
      .attr('class', 'label')
      .attr('transform', d => `translate(${arc.centroid(d)})`)
      .attr('text-anchor', 'middle')
      .attr('fill', COLORS.white)
      .attr('font-size', '11px')
      .attr('font-weight', 'bold')
      .text(d => `${d.data.type}`);

    g.selectAll('text.pct')
      .data(pie(pieData))
      .join('text')
      .attr('class', 'pct')
      .attr('transform', d => {
        const c = arc.centroid(d);
        return `translate(${c[0]},${c[1] + 14})`;
      })
      .attr('text-anchor', 'middle')
      .attr('fill', COLORS.white)
      .attr('font-size', '10px')
      .text(d => `${((d.data.count / total) * 100).toFixed(1)}%`);

    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-0.2em')
      .attr('fill', COLORS.white)
      .attr('font-size', '22px')
      .attr('font-weight', 'bold')
      .text(total.toLocaleString());

    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.2em')
      .attr('fill', COLORS.textMuted)
      .attr('font-size', '10px')
      .text('Total Shows');
  }, [data]);

  return (
    <div ref={containerRef} className="w-full h-full">
      <h3 className="text-sm font-bold px-3 pt-2" style={{ color: COLORS.white }}>Shows by Type</h3>
      <svg ref={svgRef} />
    </div>
  );
}

/* ─── Area Chart ─── */
function AreaChart({ data }: { data: Show[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight - 40;
    const margin = { top: 10, right: 20, bottom: 30, left: 40 };

    svg.attr('width', width).attr('height', height);

    const grouped = d3.rollup(data, v => v.length, d => d.release_year, d => d.type);
    const years = Array.from(new Set(data.map(d => d.release_year))).filter(y => y >= 1920).sort((a, b) => a - b);
    const types = ['Movie', 'TV Show'];

    const stackData = years.map(year => {
      const entry: Record<string, number> = { year };
      types.forEach(t => {
        entry[t] = grouped.get(year)?.get(t) || 0;
      });
      return entry;
    });

    const stack = d3.stack<Record<string, number>>().keys(types);
    const series = stack(stackData);

    const x = d3.scaleLinear()
      .domain([d3.min(years) || 1920, d3.max(years) || 2021])
      .range([margin.left, width - margin.right]);

    const y = d3.scaleLinear()
      .domain([0, d3.max(series, s => d3.max(s, d => d[1])) || 0])
      .nice()
      .range([height - margin.bottom, margin.top]);

    const area = d3.area<d3.SeriesPoint<Record<string, number>>>()
      .x(d => x(d.data.year))
      .y0(d => y(d[0]))
      .y1(d => y(d[1]))
      .curve(d3.curveMonotoneX);

    const colorMap: Record<string, string> = { 'Movie': COLORS.primary, 'TV Show': COLORS.primaryLight };

    svg.selectAll('path.area')
      .data(series)
      .join('path')
      .attr('class', 'area')
      .attr('d', area)
      .attr('fill', d => colorMap[d.key] || COLORS.primary)
      .attr('opacity', 0.85);

    svg.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(8).tickFormat(d3.format('d')))
      .call(g => g.select('.domain').attr('stroke', COLORS.border))
      .call(g => g.selectAll('.tick line').attr('stroke', COLORS.border))
      .call(g => g.selectAll('.tick text').attr('fill', COLORS.textMuted).attr('font-size', '9px'));

    svg.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(5))
      .call(g => g.select('.domain').attr('stroke', COLORS.border))
      .call(g => g.selectAll('.tick line').attr('stroke', COLORS.border))
      .call(g => g.selectAll('.tick text').attr('fill', COLORS.textMuted).attr('font-size', '9px'));

    const legend = svg.append('g').attr('transform', `translate(${width - 140}, ${margin.top + 5})`);
    types.forEach((t, i) => {
      legend.append('rect').attr('x', 0).attr('y', i * 18).attr('width', 12).attr('height', 12)
        .attr('fill', colorMap[t]).attr('rx', 2);
      legend.append('text').attr('x', 18).attr('y', i * 18 + 10)
        .attr('fill', COLORS.white).attr('font-size', '10px').text(t);
    });
  }, [data]);

  return (
    <div ref={containerRef} className="w-full h-full">
      <h3 className="text-sm font-bold px-3 pt-2" style={{ color: COLORS.white }}>Shows by Release Year and Type</h3>
      <svg ref={svgRef} />
    </div>
  );
}

/* ─── Horizontal Bar Chart (Top 10 Genres) ─── */
function TopGenresChart({ data }: { data: Show[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight - 40;
    const margin = { top: 5, right: 50, bottom: 20, left: 180 };

    svg.attr('width', width).attr('height', height);

    const genreCounts = d3.rollup(data, v => new Set(v.map(d => d.show_id)).size, d => d.listed_in);
    const sorted = Array.from(genreCounts, ([genre, count]) => ({ genre, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    const x = d3.scaleLinear()
      .domain([0, d3.max(sorted, d => d.count) || 0])
      .range([margin.left, width - margin.right]);

    const y = d3.scaleBand()
      .domain(sorted.map(d => d.genre))
      .range([margin.top, height - margin.bottom])
      .padding(0.3);

    svg.selectAll('rect')
      .data(sorted)
      .join('rect')
      .attr('x', margin.left)
      .attr('y', d => y(d.genre) || 0)
      .attr('width', d => x(d.count) - margin.left)
      .attr('height', y.bandwidth())
      .attr('fill', COLORS.primary)
      .attr('rx', 3);

    svg.selectAll('text.label')
      .data(sorted)
      .join('text')
      .attr('class', 'label')
      .attr('x', margin.left - 5)
      .attr('y', d => (y(d.genre) || 0) + y.bandwidth() / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('fill', COLORS.white)
      .attr('font-size', '9px')
      .text(d => d.genre.length > 28 ? d.genre.slice(0, 28) + '...' : d.genre);

    svg.selectAll('text.value')
      .data(sorted)
      .join('text')
      .attr('class', 'value')
      .attr('x', d => x(d.count) + 5)
      .attr('y', d => (y(d.genre) || 0) + y.bandwidth() / 2)
      .attr('dy', '0.35em')
      .attr('fill', COLORS.white)
      .attr('font-size', '9px')
      .text(d => d.count);
  }, [data]);

  return (
    <div ref={containerRef} className="w-full h-full">
      <h3 className="text-sm font-bold px-3 pt-2" style={{ color: COLORS.white }}>Top 10 Genres</h3>
      <svg ref={svgRef} />
    </div>
  );
}

/* ─── Radial Bar Chart (Top Ratings) ─── */
function RatingsChart({ data }: { data: Show[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight - 40;

    svg.attr('width', width).attr('height', height);

    const ratingCounts = d3.rollup(data, v => new Set(v.map(d => d.show_id)).size, d => d.rating);
    const sorted = Array.from(ratingCounts, ([rating, count]) => ({ rating, count }))
      .filter(d => d.rating && d.rating.trim() !== '')
      .sort((a, b) => b.count - a.count);

    const maxCount = d3.max(sorted, d => d.count) || 1;
    const innerRadius = 30;
    const outerRadius = Math.min(width, height) / 2 - 25;

    const xScale = d3.scaleBand()
      .domain(sorted.map(d => d.rating))
      .range([0, 2 * Math.PI])
      .padding(0.15);

    const yScale = d3.scaleRadial()
      .domain([0, maxCount])
      .range([innerRadius, outerRadius]);

    const g = svg.append('g').attr('transform', `translate(${width / 2},${height / 2})`);

    g.selectAll('path')
      .data(sorted)
      .join('path')
      .attr('d', d3.arc<{ rating: string; count: number }>()
        .innerRadius(innerRadius)
        .outerRadius(d => yScale(d.count))
        .startAngle(d => xScale(d.rating) || 0)
        .endAngle(d => (xScale(d.rating) || 0) + xScale.bandwidth())
        .padAngle(0.02)
        .padRadius(innerRadius)
      )
      .attr('fill', COLORS.primary)
      .attr('opacity', 0.85);

    g.selectAll('text')
      .data(sorted)
      .join('text')
      .attr('text-anchor', 'middle')
      .attr('transform', d => {
        const angle = ((xScale(d.rating) || 0) + xScale.bandwidth() / 2) * 180 / Math.PI - 90;
        const r = yScale(d.count) + 12;
        return `rotate(${angle}) translate(${r},0) rotate(${angle > 90 ? -angle - 90 : -angle + 90})`;
      })
      .attr('fill', COLORS.white)
      .attr('font-size', '8px')
      .text(d => d.rating);
  }, [data]);

  return (
    <div ref={containerRef} className="w-full h-full">
      <h3 className="text-sm font-bold px-3 pt-2" style={{ color: COLORS.white }}>Top Ratings</h3>
      <svg ref={svgRef} />
    </div>
  );
}

/* ─── Stat Card ─── */
function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-2 rounded-lg"
      style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}` }}>
      <span className="text-xs font-medium" style={{ color: COLORS.textMuted }}>{label}</span>
      <span className="text-lg font-bold" style={{ color: COLORS.primary }}>{value}</span>
    </div>
  );
}

/* ─── Main App ─── */
function App() {
  const [data, setData] = useState<Show[]>([]);
  const [selectedTitle, setSelectedTitle] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    d3.csv('/amazon_prime_titles.csv').then(raw => {
      const parsed: Show[] = raw.map(d => ({
        show_id: d.show_id || '',
        type: d.type || '',
        title: d.title || '',
        director: d.director || '',
        cast: d.cast || '',
        country: d.country || '',
        date_added: d.date_added || '',
        release_year: +(d.release_year || 0),
        rating: d.rating || '',
        duration: d.duration || '',
        listed_in: d.listed_in || '',
        description: d.description || '',
      }));
      setData(parsed);
      if (parsed.length > 0) setSelectedTitle(parsed[0].title);
      setLoading(false);
    });
  }, []);

  const selectedShow = data.find(d => d.title === selectedTitle);
  const totalShows = new Set(data.map(d => d.show_id)).size;
  const totalDirectors = new Set(data.filter(d => d.director).map(d => d.director)).size;
  const dateRange = data.length > 0
    ? `${d3.min(data, d => d.release_year)} - ${d3.max(data, d => d.release_year)}`
    : '';

  const handleTitleChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedTitle(e.target.value);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen w-screen" style={{ background: COLORS.bg }}>
        <div className="text-xl font-bold" style={{ color: COLORS.primary }}>Loading Amazon Prime Video Data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full" style={{ background: COLORS.bg, color: COLORS.white }}>
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3" style={{ borderBottom: `1px solid ${COLORS.border}` }}>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="6" fill={COLORS.primary} />
              <path d="M8 20 L16 12 L24 20" stroke="white" strokeWidth="2.5" fill="none" />
            </svg>
            <div>
              <h1 className="text-lg font-bold leading-tight" style={{ color: COLORS.white }}>Amazon Prime Video</h1>
              <p className="text-xs" style={{ color: COLORS.textMuted }}>Dashboard Analytics</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <StatCard label="Total Shows" value={totalShows.toLocaleString()} />
          <StatCard label="Directors" value={totalDirectors.toLocaleString()} />
          <StatCard label="Year Range" value={dateRange} />
        </div>
      </header>

      {/* Title selector + info bar */}
      <div className="flex items-center gap-4 px-6 py-3" style={{ borderBottom: `1px solid ${COLORS.border}` }}>
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium" style={{ color: COLORS.textMuted }}>Select Title</label>
          <select
            value={selectedTitle}
            onChange={handleTitleChange}
            className="rounded px-3 py-1.5 text-sm min-w-64"
            style={{ background: COLORS.bgCard, color: COLORS.white, border: `1px solid ${COLORS.border}` }}
          >
            {data.map(d => (
              <option key={d.show_id} value={d.title}>{d.title}</option>
            ))}
          </select>
        </div>
        {selectedShow && (
          <div className="flex items-center gap-6 ml-4 text-xs flex-1 overflow-hidden">
            <div><span style={{ color: COLORS.textMuted }}>Type: </span><span className="font-semibold">{selectedShow.type}</span></div>
            <div><span style={{ color: COLORS.textMuted }}>Rating: </span><span className="font-semibold">{selectedShow.rating || 'N/A'}</span></div>
            <div><span style={{ color: COLORS.textMuted }}>Duration: </span><span className="font-semibold">{selectedShow.duration || 'N/A'}</span></div>
            <div><span style={{ color: COLORS.textMuted }}>Released: </span><span className="font-semibold">{selectedShow.release_year}</span></div>
            <div><span style={{ color: COLORS.textMuted }}>Genre: </span><span className="font-semibold truncate">{selectedShow.listed_in}</span></div>
          </div>
        )}
      </div>

      {/* Main content grid */}
      <div className="grid gap-3 p-4" style={{ gridTemplateColumns: '1fr 1fr 1fr', gridTemplateRows: 'auto auto' }}>

        {/* Row 1: Map | Details + Logo | Ratings */}
        <div className="rounded-xl overflow-hidden" style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, height: '380px' }}>
          <WorldMap data={data} />
        </div>

        <div className="rounded-xl overflow-hidden flex flex-col" style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, height: '380px' }}>
          {selectedShow && (
            <div className="flex flex-col flex-1 p-4 overflow-y-auto">
              <h3 className="text-sm font-bold mb-2" style={{ color: COLORS.primary }}>{selectedShow.title}</h3>
              <div className="mb-3">
                <span className="text-xs font-medium" style={{ color: COLORS.textMuted }}>Cast</span>
                <p className="text-xs mt-1 leading-relaxed">{selectedShow.cast || 'N/A'}</p>
              </div>
              <div className="mb-3">
                <span className="text-xs font-medium" style={{ color: COLORS.textMuted }}>Description</span>
                <p className="text-xs mt-1 leading-relaxed" style={{ color: '#c0d0e0' }}>{selectedShow.description || 'N/A'}</p>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-auto">
                <div className="rounded-lg p-2 text-center" style={{ background: COLORS.bg }}>
                  <div className="text-xs" style={{ color: COLORS.textMuted }}>Director</div>
                  <div className="text-xs font-semibold mt-0.5">{selectedShow.director || 'N/A'}</div>
                </div>
                <div className="rounded-lg p-2 text-center" style={{ background: COLORS.bg }}>
                  <div className="text-xs" style={{ color: COLORS.textMuted }}>Country</div>
                  <div className="text-xs font-semibold mt-0.5">{selectedShow.country || 'N/A'}</div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="rounded-xl overflow-hidden" style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, height: '380px' }}>
          <RatingsChart data={data} />
        </div>

        {/* Row 2: Top 10 Genres | Donut Chart | Area Chart */}
        <div className="rounded-xl overflow-hidden" style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, height: '340px' }}>
          <TopGenresChart data={data} />
        </div>

        <div className="rounded-xl overflow-hidden" style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, height: '340px' }}>
          <DonutChart data={data} />
        </div>

        <div className="rounded-xl overflow-hidden" style={{ background: COLORS.bgCard, border: `1px solid ${COLORS.border}`, height: '340px' }}>
          <AreaChart data={data} />
        </div>
      </div>
    </div>
  );
}

export default App;
