let chartInstance = null;

async function getChartData(payload = null) {
  const opts = payload
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }
    : {};
  const url = payload ? "/simulate" : "/api/risk-factors";
  const res = await fetch(url, opts);
  return res.json();
}


function createChart(arc, pie, color, pathGroup, labelGroup, data) {
  const arcs = pie(data);
  const path = pathGroup.selectAll("path").data(arcs, d => d.data.name);
  path.join(
    enter => enter.append("path")
      .attr("fill", d => color(d.data.name))
      .attr("d", arc)
      .each(function(d) { this._current = d; }),
    update => update.transition().duration(750).attrTween("d", function(a) {
      const i = d3.interpolate(this._current, a);
      this._current = i(0);
      return t => arc(i(t));
    }),
    exit => exit.transition().duration(500).remove()
  );
  // TITLES
  pathGroup.selectAll("path").append("title")
    .text(d => `${d.data.name}: ${d.data.value.toFixed(1)}%`);

  // LABELS
  const labels = labelGroup.selectAll("text").data(arcs, d => d.data.name);
  labels.join(
    enter => enter.append("text")
      .attr("transform", d => `translate(${arc.centroid(d)})`)
      .style("opacity", 0)
      .call(text => text.append("tspan")
        .attr("y", "-0.4em").attr("font-weight", "bold").text(d => d.data.name))
      .call(text => text.append("tspan")
        .attr("x", 0).attr("y", "0.7em").attr("fill-opacity", 0.7)
        .text(d => `${d.data.value.toFixed(1)}%`))
      .transition().duration(750).style("opacity", 1),
    update => update.transition().duration(750)
        .attr("transform", d => `translate(${arc.centroid(d)})`)
        .call(txt => txt.select("tspan:last-child")
          .text(d => `${d.data.value.toFixed(1)}%`)),
    exit => exit.transition().duration(500).style("opacity", 0).remove()
  );
}

async function drawRiskChart() {
  const data = await getChartData();

  const width = 400;
  const height = 400;
  const radius = Math.min(width, height) / 2;
  const arc = d3.arc().innerRadius(radius * 0.67).outerRadius(radius - 1);
  const pie = d3.pie().sort(null).value(d => d.value).padAngle(1 / radius);
  const color = d3.scaleOrdinal()
    .domain(data.map(d => d.name))
    .range(d3.quantize(t => d3.interpolateSpectral(t * 0.8 + 0.1), data.length).reverse());

  const svg = d3.select("#risk-chart").append("svg")
    .attr("width", width).attr("height", height)
    .attr("viewBox", [-width/2, -height/2, width, height])
    .style("max-width", "100%; height: auto;");

  const pathGroup = svg.append("g");
  const labelGroup = svg.append("g")
      .attr("font-family", "sans-serif")
      .attr("font-size", 12)
      .attr("text-anchor", "middle");

  createChart(arc, pie, color, pathGroup, labelGroup, data);

  chartInstance = { update: payload => getChartData(payload).then(newData =>
      createChart(arc, pie, color, pathGroup, labelGroup, newData)
  )};
}

document.addEventListener("DOMContentLoaded", () => {
  drawRiskChart();

  document.getElementById("simulate").addEventListener("click", () => {
    const payload = {
      demographics: {
        age: +document.getElementById("age").value,
        gender: document.getElementById("gender").value,
        height_m: +document.getElementById("height").value,
        weight_kg: +document.getElementById("weight").value
      },
      lifestyle: {
        veggie_freq: +document.getElementById("veggies").value,
        water_litres: +document.getElementById("water").value,
        transport: document.getElementById("transport").value,
        physical_activity: +document.getElementById("exercise").value,
        tech_use: +document.getElementById("screen").value,
        high_calorie_food: true,
        caloric_beverages: "frequently",
        between_meals: "frequently",
        meals_per_day: 2
      },
      family_history_overweight: true
    };
    chartInstance.update(payload);
  });
});
