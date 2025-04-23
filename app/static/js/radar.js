async function fetchData() {
  const [data, axis, userData] = await Promise.all([
    fetch("/api/radar").then(res => res.json()),
    fetch("/api/radar_axis").then(res => res.json()),
    fetch("/api/user_radar").then(res => res.json())  // user's own data
  ]);

  console.log("DATA:", data);
  console.log("AXIS META:", axis);
  console.log("USER:", userData);

  drawRadarChart(data, axis, userData);
}

function drawRadarChart(data, axisMeta, userData = null) {
  d3.select("#radar").selectAll("*").remove();
  const features = Object.keys(data[0]).filter(k => k !== "_id" && k !== "obesity_class");
  const width = 600, height = 600;
  const margin = 60;
  const full = width + margin * 2;

  const svg = d3.select("#radar").append("svg")
    .attr("viewBox", `0 0 ${full} ${full}`)
    .style("width", "100%")
    .append("g")
    .attr("transform", `translate(${full / 2},${full / 2})`);

  const radialScale = d3.scaleLinear().domain([0, 1]).range([0, 250]);

  const ticks = [0.2, 0.4, 0.6, 0.8, 1.0];
  svg.selectAll("circle")
    .data(ticks)
    .join("circle")
    .attr("fill", "none")
    .attr("stroke", "lightgray")
    .attr("r", d => radialScale(d));

  svg.selectAll(".ticklabel")
    .data(ticks)
    .join("text")
    .attr("class", "ticklabel")
    .attr("x", 5)
    .attr("y", d => -radialScale(d))
    .text(d => d);

  function angleToCoordinate(angle, value) {
    return {
      x: Math.cos(angle) * radialScale(value),
      y: Math.sin(angle) * radialScale(value)
    };
  }

  const featureData = features.map((f, i) => {
    const angle = (Math.PI / 2) + (2 * Math.PI * i / features.length);
    return {
      name: f,
      angle: angle,
      line_coord: angleToCoordinate(angle, 1),
      label_coord: angleToCoordinate(angle, 1.2)
    };
  });

  svg.selectAll("line")
    .data(featureData)
    .join("line")
    .attr("x1", 0)
    .attr("y1", 0)
    .attr("x2", d => d.line_coord.x)
    .attr("y2", d => d.line_coord.y)
    .attr("stroke", "black");

  svg.selectAll(".axislabel")
    .data(featureData)
    .join("text")
    .attr("x", d => d.label_coord.x)
    .attr("y", d => d.label_coord.y)
    .text(d => d.name.replace(/_/g, " "))
    .attr("font-size", "13px")
    .attr("font-weight", "bold")
    .attr("text-anchor", "middle");

  const line = d3.line()
    .x(d => d.x)
    .y(d => d.y)
    .curve(d3.curveLinearClosed);

  const colors = d3.schemeCategory10;

  function normalize(val, min, max) {
    return (max - min === 0) ? 0.5 : (val - min) / (max - min);
  }

  function getPathCoordinates(data_point) {
    const coords = features.map((f, i) => {
      const angle = (Math.PI / 2) + (2 * Math.PI * i / features.length);
      const val = normalize(+data_point[f], +axisMeta[f].min, +axisMeta[f].max);
      return angleToCoordinate(angle, val);
    });
    coords.push(coords[0]);
    return coords;
  }

  const paths = data.map(d => getPathCoordinates(d));
  svg.selectAll(".data-path")
    .data(paths)
    .join("path")
    .attr("class", (d, i) => `data-path polygon-${i}`)
    .attr("d", line)
    .attr("stroke-width", 3)
    .attr("stroke", (_, i) => colors[i % colors.length])
    .attr("fill", (_, i) => colors[i % colors.length])
    .attr("fill-opacity", 0.3)
    .attr("stroke-opacity", 1);

  const legend = d3.select("#radar").append("div")
    .attr("class", "legend")
    .style("margin-top", "20px");

  data.forEach((d, i) => {
    const id = `poly-toggle-${i}`;
    const entry = legend.append("div").style("margin-bottom", "6px");

    entry.append("input")
      .attr("type", "checkbox")
      .attr("id", id)
      .attr("checked", true)
      .on("change", function () {
        const visible = this.checked;
        d3.select(`.polygon-${i}`)
          .style("display", visible ? "block" : "none");
      });

    entry.append("label")
      .attr("for", id)
      .style("margin-left", "6px")
      .html(`<span style="display:inline-block; width:15px; height:15px; background:${colors[i % colors.length]}; margin-right:6px;"></span>${d._id || d.obesity_class}`);
  });

  if (userData) {
    // Ensure userData is aligned with feature order
    const coords = features.map((f, i) => {
      const angle = (Math.PI / 2) + (2 * Math.PI * i / features.length);
      let val = userData[f];

      // If it's already normalized in backend:
      val = +val;

      return angleToCoordinate(angle, val);
    });
    coords.push(coords[0]);

    
    svg.append("path")
      .datum(coords)
      .attr("class", "user-data-path")
      .attr("d", line)
      .attr("stroke", "black")
      .attr("fill", "black")
      .attr("fill-opacity", 0.2)
      .attr("stroke-width", 2);
  }

  if (userData) {
    const userToggle = legend.append("div").style("margin-bottom", "6px");
  
    userToggle.append("input")
      .attr("type", "checkbox")
      .attr("id", "toggle-user")
      .attr("checked", true)
      .on("change", function () {
        const visible = this.checked;
        d3.select(".user-data-path")
          .style("display", visible ? "block" : "none");
      });
  
    userToggle.append("label")
      .attr("for", "toggle-user")
      .style("margin-left", "6px")
      .html(`<span style="display:inline-block; width:15px; height:15px; background:black; margin-right:6px;"></span><strong>YOU</strong>`);
  }
}

fetchData();
