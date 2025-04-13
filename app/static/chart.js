const hahaBtn = document.getElementById("hahahahaha-button");
const wrapper = document.getElementById("chart-wrapper");

let chartVisible = false;

hahaBtn.addEventListener("click", () => {
  chartVisible = !chartVisible;
  wrapper.style.display = chartVisible ? "block" : "none";

  // Optionally clear the chart if hiding
  if (!chartVisible) {
    document.getElementById("chart-container").innerHTML = "";
    document.getElementById("animation-controls").style.display = "none";
  }
});

document.getElementById("show-chart").addEventListener("click", () => {
  document.getElementById("chart-container").style.display = "block";
  document.getElementById("animation-controls").style.display = "block";
  initObesityChart();
});
  
document.getElementById("hide-chart").addEventListener("click", () => {
  document.getElementById("chart-container").style.display = "none";
  document.getElementById("animation-controls").style.display = "none";
  document.getElementById("chart-container").innerHTML = ""; // Clear SVG
});

document.getElementById("reset-chart").addEventListener("click", () => {
  document.getElementById("chart-container").innerHTML = "";
  document.getElementById("chart-container").style.display = "block";
  document.getElementById("animation-controls").style.display = "block";
  initObesityChart();
});
  
  function initObesityChart() {
    // Chart settings
    const width = 960, barSize = 48, duration = 250, k = 10;
    let n = parseInt(document.getElementById("country-count").value);
    const margin = { top: 16, right: 6, bottom: 6, left: 0 };
    const formatNumber = d3.format(",d");
    const formatDate = d3.utcFormat("%Y");
  
    let names, datevalues, keyframes, nameframes, prev, next;
    let x, y, svg, currentFrame = 0, running = false;
    let updateBars, updateAxis, updateLabels, updateTicker;
  
    const chartContainer = d3.select("#chart-container");
  
    fetch("/data")
      .then(res => res.json())
      .then(data => {
        data.forEach(d => {
          d.date = +d.date;
          d.value = +d.value;
        });
  
        names = new Set(data.map(d => d.name));
  
        datevalues = Array.from(
          d3.rollup(data, v => d3.sum(v, d => d.value), d => d.date, d => d.name)
        )
          .map(([date, map]) => [new Date(date, 0, 1), map])
          .sort(([a], [b]) => d3.ascending(a, b));
  
        x = d3.scaleLinear().range([margin.left, width - margin.right]);
        y = d3.scaleBand()
          .domain(d3.range(n + 1))
          .rangeRound([margin.top, margin.top + barSize * (n + 1 + 0.1)])
          .padding(0.1);
  
        svg = chartContainer.append("svg")
          .attr("viewBox", [0, 0, width, margin.top + barSize * n + margin.bottom])
          .attr("width", width)
          .attr("height", margin.top + barSize * n + margin.bottom);
  
        generateKeyframes();
        setupChart();
      });
  
    function rank(value) {
      const data = Array.from(names, name => ({ name, value: value(name) }));
      data.sort((a, b) => d3.descending(a.value, b.value));
      for (let i = 0; i < data.length; ++i) data[i].rank = Math.min(n, i);
      return data;
    }
  
    function generateKeyframes() {
      keyframes = [];
      let ka, a, kb, b;
  
      for ([[ka, a], [kb, b]] of d3.pairs(datevalues)) {
        for (let i = 0; i < k; ++i) {
          const t = i / k;
          keyframes.push([
            new Date(ka.getTime() * (1 - t) + kb.getTime() * t),
            rank(name => (a.get(name) || 0) * (1 - t) + (b.get(name) || 0) * t)
          ]);
        }
      }
      keyframes.push([new Date(kb), rank(name => b.get(name) || 0)]);
  
      nameframes = d3.groups(keyframes.flatMap(([, data]) => data), d => d.name);
      prev = new Map(nameframes.flatMap(([, data]) => d3.pairs(data, (a, b) => [b, a])));
      next = new Map(nameframes.flatMap(([, data]) => d3.pairs(data)));
    }
  
    function setupChart() {
      updateBars = bars(svg);
      updateAxis = axis(svg);
      updateLabels = labels(svg);
      updateTicker = ticker(svg);
  
      // Button event handlers
      d3.select("#play").on("click", () => {
        if (!running) animateFrom(currentFrame);
      });
  
      d3.select("#pause").on("click", () => {
        running = false;
      });
  
      d3.select("#restart").on("click", () => {
        running = false;
        currentFrame = 0;
        svg.selectAll("*").remove();
        generateKeyframes();
        updateBars = bars(svg);
        updateAxis = axis(svg);
        updateLabels = labels(svg);
        updateTicker = ticker(svg);
        animateFrom(0);
      });
    }
  
    async function animateFrom(index = 0) {
      currentFrame = index;
      running = true;
  
      for (; currentFrame < keyframes.length && running; currentFrame++) {
        const keyframe = keyframes[currentFrame];
        const transition = svg.transition().duration(duration).ease(d3.easeLinear);
  
        x.domain([0, keyframe[1][0].value]);
        updateAxis(keyframe, transition);
        updateBars(keyframe, transition);
        updateLabels(keyframe, transition);
        updateTicker(keyframe, transition);
  
        await transition.end();
      }
    }
  
    // --- Modular Chart Elements ---
  
    function bars(svg) {
      let bar = svg.append("g").attr("fill-opacity", 0.6).selectAll("rect");
  
      return ([, data], transition) => bar = bar
        .data(data.slice(0, n), d => d.name)
        .join(
          enter => enter.append("rect")
            .attr("fill", color)
            .attr("height", y.bandwidth())
            .attr("x", x(0))
            .attr("y", d => y((prev.get(d) || d).rank))
            .attr("width", d => x((prev.get(d) || d).value) - x(0)),
          update => update,
          exit => exit.transition(transition).remove()
            .attr("y", d => y((next.get(d) || d).rank))
            .attr("width", d => x((next.get(d) || d).value) - x(0))
        )
        .call(bar => bar.transition(transition)
          .attr("y", d => y(d.rank))
          .attr("width", d => x(d.value) - x(0)));
    }
  
    function labels(svg) {
      let label = svg.append("g")
        .style("font", "bold 12px sans-serif")
        .attr("text-anchor", "end")
        .selectAll("text");
  
      return ([, data], transition) => label = label
        .data(data.slice(0, n), d => d.name)
        .join(
          enter => enter.append("text")
            .attr("transform", d => `translate(${x((prev.get(d) || d).value)},${y((prev.get(d) || d).rank)})`)
            .attr("y", y.bandwidth() / 2)
            .attr("x", -6)
            .attr("dy", "-0.25em")
            .text(d => d.name)
            .call(text => text.append("tspan")
              .attr("fill-opacity", 0.7)
              .attr("font-weight", "normal")
              .attr("x", -6)
              .attr("dy", "1.15em")),
          update => update,
          exit => exit.transition(transition).remove()
            .attr("transform", d => `translate(${x((next.get(d) || d).value)},${y((next.get(d) || d).rank)})`)
            .call(g => g.select("tspan").tween("text", d => textTween(d.value, (next.get(d) || d).value)))
        )
        .call(label => label.transition(transition)
          .attr("transform", d => `translate(${x(d.value)},${y(d.rank)})`)
          .call(g => g.select("tspan").tween("text", d => textTween((prev.get(d) || d).value, d.value))));
    }
  
    function axis(svg) {
      const g = svg.append("g").attr("transform", `translate(0,${margin.top})`);
      const axis = d3.axisTop(x).ticks(width / 160).tickSizeOuter(0).tickSizeInner(-barSize * (n + y.padding()));
  
      return (_, transition) => {
        g.transition(transition).call(axis);
        g.select(".tick:first-of-type text").remove();
        g.selectAll(".tick:not(:first-of-type) line").attr("stroke", "white");
        g.select(".domain").remove();
      };
    }
  
    function ticker(svg) {
      const now = svg.append("text")
        .style("font", `bold ${barSize}px sans-serif`)
        .attr("text-anchor", "end")
        .attr("x", width - 6)
        .attr("y", margin.top + barSize * (n - 0.45))
        .attr("dy", "0.32em")
        .text(formatDate(keyframes[0][0]));
  
      return ([date], transition) => {
        transition.end().then(() => now.text(formatDate(date)));
      };
    }
  
    function textTween(a, b) {
      const i = d3.interpolateNumber(a, b);
      return function (t) {
        this.textContent = formatNumber(i(t));
      };
    }
  
    function color(d) {
      const scale = d3.scaleOrdinal(d3.schemeTableau10);
      return scale(d.name);
    }
  }
  

// USA

let mapVisible = false;
let mapDrawn = false;

document.getElementById("hehehe-button").addEventListener("click", async () => {
  const mapContainer = document.getElementById("map-container");

  if (mapVisible) {
    mapContainer.style.display = "none";
    mapVisible = false;
  } else {
    mapContainer.style.display = "block";
    mapVisible = true;

    if (!mapDrawn) {
      await drawMap();  // Only draw once
      mapDrawn = true;
    }
  }
});

async function drawMap() {
  const width = 975;
  const height = 610;

  const us = await fetch("../static/us.json").then(res => res.json());
  const stateValues = await fetch("/api/state-values").then(res => res.json());

  const valueMap = new Map(
    stateValues.map(d => [d.state.toLowerCase().trim(), d.obesity])
  );

  const zoom = d3.zoom()
    .scaleExtent([1, 8])
    .on("zoom", zoomed);

  const svg = d3.create("svg")
    .attr("viewBox", [0, 0, width, height])
    .attr("width", width)
    .attr("height", height)
    .attr("style", "max-width: 100%; height: auto;")
    .on("click", reset);

  const path = d3.geoPath();
  const g = svg.append("g");

  const states = g.append("g")
    .attr("fill", "#444")
    .attr("cursor", "pointer")
    .selectAll("path")
    .data(topojson.feature(us, us.objects.states).features)
    .join("path")
    .on("click", clicked)
    .attr("d", path);

  states.append("title")
    .text(d => d.properties.name);

  g.append("path")
    .attr("fill", "none")
    .attr("stroke", "white")
    .attr("stroke-linejoin", "round")
    .attr("d", path(topojson.mesh(us, us.objects.states, (a, b) => a !== b)));

  svg.call(zoom);

  function reset() {
    states.transition().style("fill", null);
    g.selectAll("text.state-label").remove();
    svg.transition().duration(750).call(
      zoom.transform,
      d3.zoomIdentity,
      d3.zoomTransform(svg.node()).invert([width / 2, height / 2])
    );
  }

  function clicked(event, d) {
    const [[x0, y0], [x1, y1]] = path.bounds(d);
    event.stopPropagation();
    states.transition().style("fill", null);
    d3.select(this).transition().style("fill", "red");

    g.selectAll("text.state-label").remove();

    const [x, y] = path.centroid(d);
    const stateName = d.properties.name.toLowerCase().trim();
    const obesity = valueMap.get(stateName);
    const label = obesity != null ? `${stateName}: ${obesity}%` : `${stateName}: N/A`;

    g.append("text")
      .attr("class", "state-label")
      .attr("x", x)
      .attr("y", y)
      .attr("text-anchor", "middle")
      .attr("dy", ".35em")
      .attr("font-size", 20)
      .attr("fill", "black")
      .text(label);

    svg.transition().duration(750).call(
      zoom.transform,
      d3.zoomIdentity
        .translate(width / 2, height / 2)
        .scale(Math.min(8, 0.9 / Math.max((x1 - x0) / width, (y1 - y0) / height)))
        .translate(-(x0 + x1) / 2, -(y0 + y1) / 2),
      d3.pointer(event, svg.node())
    );
  }

  function zoomed(event) {
    const { transform } = event;
    g.attr("transform", transform);
    g.attr("stroke-width", 1 / transform.k);
  }

  document.getElementById("map").appendChild(svg.node());
}
