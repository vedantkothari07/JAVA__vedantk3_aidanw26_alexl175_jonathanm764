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
  
  function initObesityChart() {
    // Chart settings
    const width = 960, barSize = 48, n = 25, duration = 250, k = 10;
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
  